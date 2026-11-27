#!/usr/bin/env python3
"""Read-only checks for tool baselines and reciprocal project registrations."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def check(root: Path) -> tuple[list[str], list[str], dict]:
    errors, notes = [], []

    def expect(condition, message):
        if not condition:
            errors.append(message)

    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))

    def unique(rows, key, label):
        result = {}
        for row in rows:
            expect(row[key] not in result, f'{label} 重复：{row[key]}')
            result[row[key]] = row
        return result

    registry = read(root / 'registry.json')
    index = read(root / 'projects.json')
    tools = unique(registry['tools'], 'id', '工具 ID')
    projects = unique(index['projects'], 'name', '项目')
    manifests = {}
    registered_root = (root / 'registry.json').resolve()
    source_count = module_count = 0
    for name, project in projects.items():
        folder = Path(project['root'])
        rules = folder / project['rules_file']
        manifest_path = folder / project['manifest_file']
        expect(rules.is_file(), f'{name} 缺少规则文件：{rules}')
        if rules.is_file():
            text = rules.read_text(encoding='utf-8')
            linked_paths = re.findall(r'/[^\s()<>`]+registry\.json', text)
            expect(any(Path(path).resolve() == registered_root for path in linked_paths) and 'check_links.py' in text,
                   f'{name} 规则缺少 tools 清单链接或联动检查命令')
        if not manifest_path.is_file():
            errors.append(f'{name} 缺少关系表：{manifest_path}')
            continue
        manifest = read(manifest_path)
        manifests[name] = manifest
        expect(manifest['project_name'] == name, f'{name} 项目名称不一致')
        expect(Path(manifest['project_root']).resolve() == folder.resolve(), f'{name} 项目根路径不一致')
        expect(Path(manifest['registry_path']).resolve() == registered_root, f'{name} 未反向指向当前 registry.json')
        expect(Path(manifest['projects_index_path']).resolve() == (root / 'projects.json').resolve(), f'{name} 项目索引路径不一致')
        expect(Path(manifest['rules_path']).is_file(), f'{name} 中央联动规范路径失效')

    for tool_id, tool in tools.items():
        source = Path(tool['source_dir'])
        guide = root / tool['guide']
        expect(guide.is_file(), f'{tool_id} 调用说明失效：{guide}')
        for doc in tool['source_docs']:
            expect(Path(doc).is_file(), f'{tool_id} 原说明路径失效：{doc}')
        hashes = tool['source_files_sha256']
        expect(bool(hashes), f'{tool_id} 没有源码基线')
        for relative, expected in hashes.items():
            path = source / relative
            expect(path.resolve().is_relative_to(source.resolve()), f'{tool_id} 基线路径越界：{relative}')
            if not path.is_file():
                errors.append(f'{tool_id} 已登记文件缺失：{path}')
                continue
            source_count += 1
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            expect(actual == expected, f'{tool_id} 源码基线过期：{relative}；先核对接口/工具卡/使用方，再更新摘要')
        # New public implementation/docs must not silently escape the baseline.
        for path in source.rglob('*') if source.is_dir() else []:
            relative = path.relative_to(source)
            if any(part.startswith('.') or part in {'__pycache__', 'node_modules', 'venv', 'dist', 'build'} for part in relative.parts):
                continue
            if path.is_file() and path.suffix in {'.py', '.js', '.ts', '.json', '.md', '.toml'}:
                expect(relative.as_posix() in hashes, f'{tool_id} 新文件尚未登记基线：{relative}')
        owner = tool.get('owner_project', {})
        owner_name = owner.get('name')
        expect(owner_name in projects, f'{tool_id} 缺少有效维护方项目')
        if owner_name in projects:
            project = projects[owner_name]
            expect(owner.get('root') == project['root'], f'{tool_id} 维护方根路径不一致')
            expect(owner.get('manifest_file') == project['manifest_file'], f'{tool_id} 维护方关系表路径不一致')
            expect(owner.get('rules_file') == project['rules_file'], f'{tool_id} 维护方规则路径不一致')
            exports = [x for x in manifests.get(owner_name, {}).get('exports', []) if x['id'] == tool_id]
            expect(len(exports) == 1, f'{tool_id} 维护方缺少唯一 exports 反向登记')
        consumer_names = set()
        for consumer in tool['consumers']:
            name = consumer['project_name']
            expect(name not in consumer_names, f'{tool_id} 使用方重复：{name}')
            consumer_names.add(name)
            expect(name in projects, f'{tool_id} 使用方未加入项目索引：{name}')
            if name not in projects:
                continue
            expect(consumer['project_root'] == projects[name]['root'], f'{tool_id}/{name} 使用方路径不一致')
            expect(consumer['dependency_file'] == projects[name]['manifest_file'], f'{tool_id}/{name} 使用方关系表路径不一致')
            dependencies = [x for x in manifests.get(name, {}).get('tools', []) if x['id'] == tool_id]
            expect(len(dependencies) == 1, f'{tool_id}/{name} 缺少唯一 tools 反向登记')
            if len(dependencies) == 1:
                dependency = dependencies[0]
                for field in ['integration', 'status', 'verified_at']:
                    expect(consumer.get(field) == dependency.get(field), f'{tool_id}/{name} 双向 {field} 不一致')

    for name, manifest in manifests.items():
        folder = Path(projects[name]['root'])
        exports = unique(manifest['exports'], 'id', f'{name} 导出')
        for tool_id, entry in exports.items():
            expect(tool_id in tools, f'{name} 导出尚未登记：{tool_id}')
            if tool_id in tools:
                tool = tools[tool_id]
                expect(tool.get('owner_project', {}).get('name') == name, f'{name}/{tool_id} 维护方反向关系不一致')
                expect(entry['source_dir'] == tool['source_dir'], f'{name}/{tool_id} 导出源码路径不一致')
                expect(Path(entry['guide_path']).resolve() == (root / tool['guide']).resolve(), f'{name}/{tool_id} 工具卡路径不一致')
        dependencies = unique(manifest['tools'], 'id', f'{name} 依赖')
        for tool_id, entry in dependencies.items():
            expect(tool_id in tools, f'{name} 依赖未知工具：{tool_id}')
            if tool_id not in tools:
                continue
            tool = tools[tool_id]
            expect(entry['source_dir'] == tool['source_dir'], f'{name}/{tool_id} 依赖源码路径不一致')
            expect(any(c['project_name'] == name for c in tool['consumers']), f'{name}/{tool_id} 缺少 consumers 反向登记')
            status = entry.get('status')
            expect(status in {'source_inspected', 'verified'}, f'{name}/{tool_id} 核对状态无效')
            if status == 'source_inspected':
                expect(bool(entry.get('inspected_at')), f'{name}/{tool_id} 缺少静态核对日期')
                baseline = entry.get('observed_source_files_sha256')
                notes.append(f'{name} → {tool_id}：已核对源码，尚未完成真实接入验收')
            else:
                expect(bool(entry.get('verified_at')), f'{name}/{tool_id} 缺少验收日期')
                baseline = entry.get('verified_source_files_sha256')
            expect(baseline == tool['source_files_sha256'], f'{name}/{tool_id} 使用方记录落后于工具基线；需审查影响并记录验证范围')
            for path in entry.get('used_by', []):
                expect((folder / path).is_file(), f'{name}/{tool_id} 调用入口失效：{path}')
        for dependency in manifest.get('module_dependencies', []):
            module_count += 1
            provider = dependency['project_name']
            expect(provider in projects, f'{name} 模块提供方未知：{provider}')
            if provider in projects:
                for relative in dependency['source_files']:
                    expect((Path(projects[provider]['root']) / relative).is_file(), f'{name} → {provider} 模块路径失效：{relative}')
            for relative in dependency['used_by']:
                expect((folder / relative).is_file(), f'{name} 模块调用入口失效：{relative}')
    return errors, notes, {'projects': len(projects), 'tools': len(tools), 'source_files': source_count, 'module_links': module_count}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1], help='tools 目录；默认由脚本位置定位')
    args = parser.parse_args()
    try:
        errors, notes, counts = check(args.root.resolve())
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f'检查配置失败：{error}')
        return 2
    for error in errors:
        print('失败：' + error)
    for note in notes:
        print('说明：' + note)
    print(('检查未通过' if errors else '联动检查通过') + '：' + '，'.join(f'{k}={v}' for k, v in counts.items()))
    print('此检查不执行业务接口、不判断文档语义正确性、不刷新摘要，也不监听文件变化。')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
