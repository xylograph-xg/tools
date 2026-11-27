#!/usr/bin/env python3
"""Install all/, check every registered project, and synchronize derived metadata."""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_links

BEGIN = '<!-- tools-all:begin -->'
END = '<!-- tools-all:end -->'
PACK = ('README.md', 'RULES.md', 'setup.py', 'hub.json')
SUFFIXES = {'.py', '.js', '.ts', '.json', '.md', '.toml'}
EXCLUDED = {'__pycache__', 'node_modules', 'venv', 'dist', 'build'}



def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.tools-sync-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


class Plan:
    """Stage metadata, compare before writing, back up old bytes, rollback errors."""
    def __init__(self):
        self.items = {}

    def put(self, path, data):
        path = Path(path)
        if isinstance(data, str):
            data = data.encode()
        old = self.items[path][0] if path in self.items else (path.read_bytes() if path.exists() else None)
        if old == data:
            self.items.pop(path, None)
        else:
            self.items[path] = (old, data)

    def commit(self, root):
        if not self.items:
            return 0
        for path, (old, _) in self.items.items():
            if (path.read_bytes() if path.exists() else None) != old:
                raise ValueError(f'文件在规划后被其他任务修改，未覆盖：{path}')
        backup = root / '.sync-backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
        saved = []
        for i, (path, (old, _)) in enumerate(self.items.items()):
            name = f'{i}.bak' if old is not None else None
            if old is not None:
                atomic(backup / name, old)
            saved.append({'path': str(path), 'backup': name})
        atomic(backup / 'manifest.json', encoded(saved))
        done = []
        try:
            for path, (old, data) in self.items.items():
                if (path.read_bytes() if path.exists() else None) != old:
                    raise ValueError(f'检测到并发修改：{path}')
                atomic(path, data)
                done.append(path)
        except BaseException:
            for path in reversed(done):
                old, written = self.items[path]
                if path.read_bytes() == written:
                    if old is None:
                        path.unlink()
                    else:
                        atomic(path, old)
            raise
        return len(done)


@contextmanager
def locked(root):
    path = root / '.tools-sync.lock'
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError(f'已有更新任务或遗留锁：{path}；确认原任务结束后再处理锁文件') from None
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(str(os.getpid()))
        yield
    finally:
        path.unlink(missing_ok=True)


def snapshot(tool, root=None):
    folder = ((root or Path(__file__).resolve().parents[1]) / tool['source_dir']).resolve()
    if not folder.is_dir():
        raise ValueError(f'源码目录不存在：{folder}')
    hashes, declarations = {}, []
    for path in sorted(folder.rglob('*')):
        relative = path.relative_to(folder)
        if any(p.startswith('.') or p in EXCLUDED for p in relative.parts):
            continue
        if not path.is_file() or (path.suffix not in SUFFIXES and relative.as_posix() not in tool['source_files_sha256']):
            continue
        if not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError(f'源码文件链接越出目录：{path}')
        data = path.read_bytes()
        hashes[relative.as_posix()] = digest(data)
        if path.suffix == '.json':
            json.loads(data)
        if path.suffix != '.py':
            continue
        tree = ast.parse(data, filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith('_'):
                declarations.append(describe(relative, node, node.name))
            elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and (not method.name.startswith('_') or method.name == '__init__'):
                        declarations.append(describe(relative, method, node.name + '.' + method.name))
    # Explicit baseline entries also detect removal or unsupported file types.
    for relative in tool['source_files_sha256']:
        path = folder / relative
        if not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError(f'非法基线路径：{relative}')
        if path.is_file() and relative not in hashes:
            hashes[relative] = digest(path.read_bytes())
    old = tool['source_files_sha256']
    changed = [{'path': p, 'kind': 'added' if p not in old else 'removed' if p not in hashes else 'modified'}
               for p in sorted(set(old) | set(hashes)) if old.get(p) != hashes.get(p)]
    return {'files_sha256': hashes, 'changes': changed, 'declarations': declarations}


def describe(path, node, name):
    args = node.args
    positional = args.posonlyargs + args.args
    required = len(positional) - len(args.defaults)
    parameters = [p.arg + ('=…' if i >= required else '') for i, p in enumerate(positional)]
    if args.posonlyargs:
        parameters.insert(len(args.posonlyargs), '/')
    if args.vararg:
        parameters.append('*' + args.vararg.arg)
    elif args.kwonlyargs:
        parameters.append('*')
    parameters += [p.arg + ('=…' if d is not None else '') for p, d in zip(args.kwonlyargs, args.kw_defaults)]
    if args.kwarg:
        parameters.append('**' + args.kwarg.arg)
    return {'file': str(path), 'line': node.lineno, 'signature': name + '(' + ', '.join(parameters) + ')'}


def generated(tool, current, root):
    source = os.path.relpath(root / tool['source_dir'], (root / tool['guide']).parent)
    lines = [f"# {tool['id']}：自动接口快照", '',
             '由全局更新生成；仅记录当前源码结构，不承诺业务语义或运行验收。默认参数值以源码/人工工具卡为准。列出的文件级函数也可能是内部实现，不自动成为公共 API。', '',
             f"权威目录：`{tool['source_dir']}`", '', '## 相对已审查基线的变化', '']
    lines += [f"- {x['kind']}: `{x['path']}`" for x in current['changes']] or ['无源码变化。']
    lines += ['', '## Python 声明', '']
    lines += [f"- `{d['signature']}` — [{d['file']}:{d['line']}]({quote((Path(source) / d['file']).as_posix())}#L{d['line']})" for d in current['declarations']]
    lines += ['', '## 文件 SHA-256', '', '```json', json.dumps(current['files_sha256'], ensure_ascii=False, indent=2), '```', '']
    return '\n'.join(lines)


def block(root):
    return f'''{BEGIN}
## all 公共接口规则（自动维护）

开始接口任务先读 [all/RULES.md](all/RULES.md)、[工具清单]({root}/registry.json) 和对应工具卡。
修改接口后必须运行 `python3 "{root}/scripts/sync_tools.py" update`；同一任务完成说明、适配及待审查记录，结束前运行 `python3 "{root}/scripts/check_links.py"`。
新项目只需复制 all/ 并运行一次 `python3 all/setup.py`。本块与 all/ 公共文件由全局命令管理，项目定制放在本块之外。
{END}'''


def package(plan, root, folder, rules_file):
    destination = folder / 'all'
    if destination.is_symlink() or destination.resolve() == (root / 'all').resolve():
        raise ValueError(f'项目 all 必须是独立副本，不能覆盖中央目录/符号链接：{destination}')
    stamp = destination / '.managed.json'
    previous = read_json(stamp) if stamp.exists() else {}
    hashes = {}
    for name in PACK:
        original = (root / 'all' / name).read_bytes()
        data = encoded({'tools_root': os.path.relpath(root, destination)}) if name == 'hub.json' else original
        if name in {'README.md', 'RULES.md'}:
            data = original.decode().replace('../scripts/', os.path.relpath(root / 'scripts', destination) + '/').encode()
        path = destination / name
        if path.is_symlink():
            raise ValueError(f'all 受管理文件不能是符号链接：{path}')
        initial_copy = not previous and path.exists() and path.read_bytes() == original
        if path.exists() and path.read_bytes() != data and digest(path.read_bytes()) != previous.get(name) and not initial_copy and name != 'hub.json':
            raise ValueError(f'all 公共文件存在本地修改，未覆盖：{path}')
        hashes[name] = digest(data)
        plan.put(path, data)
    plan.put(stamp, encoded(hashes))
    path = folder / rules_file
    text = path.read_text() if path.exists() else '# 项目开发规则\n'
    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(END) < text.index(BEGIN):
            raise ValueError(f'AGENTS 受管理标记损坏：{path}')
        text = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), lambda _: block(os.path.relpath(root, folder)), text, flags=re.S)
    else:
        text = text.rstrip() + '\n\n' + block(os.path.relpath(root, folder)) + '\n'
    plan.put(path, text)


def load(root):
    registry, index = read_json(root / 'registry.json'), read_json(root / 'projects.json')
    names = [p['name'] for p in index['projects']]
    if len(names) != len(set(names)):
        raise ValueError('projects.json 存在重名项目')
    manifests = {p['name']: read_json((root / p['root']) / p['manifest_file']) for p in index['projects']}
    return registry, index, manifests


def install(root, folder):
    folder = folder.resolve()
    if folder == root or not folder.is_dir():
        raise ValueError('请选择存在的业务项目目录，不能是 tools 自身')
    registry, index, manifests = load(root)
    found = next((p for p in index['projects'] if (root / p['root']).resolve() == folder), None)
    name = found['name'] if found else folder.name
    if not found and any(p['name'] == name for p in index['projects']):
        raise ValueError(f'已有同名项目 {name}，请先为新目录使用唯一名称')
    plan = Plan()
    if not found:
        found = {'name': name, 'root': os.path.relpath(folder, root), 'rules_file': 'AGENTS.md', 'manifest_file': 'tool-dependencies.json'}
        index['projects'].append(found)
        path = folder / found['manifest_file']
        manifest = read_json(path) if path.exists() else {
            'schema_version': 1, 'project_name': name, 'project_root': '.',
            'registry_path': os.path.relpath(root / 'registry.json', folder), 'projects_index_path': os.path.relpath(root / 'projects.json', folder),
            'rules_path': os.path.relpath(root / 'docs/跨项目接入与联动.md', folder), 'exports': [], 'tools': [], 'module_dependencies': []}
        if manifest['project_name'] != name or (folder / manifest['project_root']).resolve() != folder:
            raise ValueError('现有依赖记录属于其他项目，请先合并')
        plan.put(path, encoded(manifest))
        plan.put(root / 'projects.json', encoded(index))
    package(plan, root, folder, found['rules_file'])
    count = plan.commit(root)
    print(f'已接入 {name}；更新 {count} 个文件，原项目自定义规则保留。')
    return 0


def reconcile(root, registry, index, manifests):
    """Dependency declarations are authoritative; derived backlinks are rebuilt."""
    projects = {p['name']: p for p in index['projects']}
    tools = {t['id']: t for t in registry['tools']}
    exports = {}
    for name, manifest in manifests.items():
        folder = root / projects[name]['root']
        if manifest['project_name'] != name or (folder / manifest['project_root']).resolve() != (root / projects[name]['root']).resolve():
            raise ValueError(f'{name} 关系表身份不一致')
        for entry in manifest['exports']:
            if entry['id'] not in tools or entry['id'] in exports:
                raise ValueError(f'导出工具未知或维护方冲突：{entry["id"]}')
            if (folder / entry['source_dir']).resolve() != (root / tools[entry['id']]['source_dir']).resolve():
                raise ValueError('源码路径迁移需先同时修改清单和项目记录')
            exports[entry['id']] = name
        ids = [e['id'] for e in manifest['tools']]
        if len(ids) != len(set(ids)) or any(i not in tools for i in ids):
            raise ValueError(f'{name} 工具依赖重复或尚未登记')
    for tool in tools.values():
        owner = exports.get(tool['id'])
        if owner is None:
            raise ValueError(f'{tool["id"]} 缺少维护方导出记录')
        p = projects[owner]
        tool['owner_project'] = {'name': owner, 'root': p['root'], 'manifest_file': p['manifest_file'], 'rules_file': p['rules_file']}
        consumers = []
        for name, manifest in manifests.items():
            for entry in manifest['tools']:
                if entry['id'] == tool['id']:
                    old = next((c for c in tool['consumers'] if c['project_name'] == name), {})
                    consumers.append({**old, 'project_name': name, 'project_root': projects[name]['root'],
                                      'dependency_file': projects[name]['manifest_file'],
                                      **{key: entry.get(key) for key in ['integration', 'status', 'inspected_at', 'verified_at', 'verification']}})
        tool['consumers'] = consumers


def update_plan(root, accept_tool=None, acknowledge=None, note=None):
    registry, index, manifests = load(root)
    plan, states, pending = Plan(), {}, []
    tools = {t['id']: t for t in registry['tools']}
    if accept_tool and accept_tool not in tools:
        raise ValueError('未知工具 ID')
    if acknowledge and (acknowledge[0] not in manifests or acknowledge[1] not in tools):
        raise ValueError('未知项目或工具')
    if (accept_tool or acknowledge) and (not note or not note.strip()):
        raise ValueError('审查登记必须填写具体 --note')
    for tool in registry['tools']:
        current = snapshot(tool, root)
        if accept_tool == tool['id']:
            previous_report = root / 'updates/latest.json'
            report = read_json(previous_report) if previous_report.exists() else {}
            previous = report.get('tools', {}).get(tool['id'], {})
            if previous.get('files_sha256') != current['files_sha256']:
                raise ValueError('先运行 update 并审查当前快照；源码已变化或没有最新快照')
            tool['source_files_sha256'] = current['files_sha256']
            tool['source_review'] = {'at': datetime.now(timezone.utc).isoformat(), 'note': note.strip(), 'kind': 'source_review_only'}
            tool['verification_history'] = tool.get('verification_history', []) + [{'verified_at': tool.get('verified_at'), 'verification': tool.get('verification')}]
            tool['verified_at'] = None
            tool['verification'] = {'kind': 'source_review_only', 'scope': note.strip(), 'live_generation_tested': False}
            current['changes'] = []
        state = 'needs_review' if current['changes'] else 'current'
        tool['sync_state'] = state
        tool['current_source_files_sha256'] = current['files_sha256']
        if state == 'needs_review':
            pending.append(f'{tool["id"]}：源码变化，核对原说明/工具卡/使用方后执行 accept')
        states[tool['id']] = current
        plan.put(root / Path(tool['guide']).parent / 'INTERFACE.generated.md', generated(tool, current, root))
    for name, manifest in manifests.items():
        for entry in manifest['tools']:
            tool = tools[entry['id']]
            current = states[tool['id']]['files_sha256']
            baseline = entry.get('verified_source_files_sha256') if entry.get('status') == 'verified' else entry.get('observed_source_files_sha256')
            if acknowledge == (name, tool['id']):
                if tool['sync_state'] != 'current':
                    raise ValueError('工具仍待源码审查，先完成 accept')
                entry.setdefault('verification_history', []).append({'status': entry.get('status'), 'verified_at': entry.get('verified_at'), 'verification': entry.get('verification')})
                entry.update(status='source_inspected', inspected_at=datetime.now().date().isoformat(), verified_at=None,
                             observed_source_files_sha256=current, verified_source_files_sha256={}, verification=note.strip())
                baseline = current
            entry['current_source_files_sha256'] = current
            entry['sync_state'] = 'current' if baseline == current and tool['sync_state'] == 'current' else 'needs_review'
            if entry['sync_state'] != 'current':
                pending.append(f'{name} → {tool["id"]}：检查适配后执行 acknowledge')
    if acknowledge and not any(e['id'] == acknowledge[1] for e in manifests[acknowledge[0]]['tools']):
        raise ValueError('该项目没有声明此工具依赖')
    reconcile(root, registry, index, manifests)
    # Module-level references are observed, not promoted to registered tools.
    module_states = []
    for p in index['projects']:
        manifest = manifests[p['name']]
        for dependency in manifest.get('module_dependencies', []):
            provider = next(x for x in index['projects'] if x['name'] == dependency['project_name'])
            hashes = {}
            for name in dependency['source_files']:
                path = (root / provider['root']) / name
                hashes[name] = digest(path.read_bytes())
            module_states.append({'consumer': p['name'], 'provider': provider['name'], 'files_sha256': hashes})
        package(plan, root, (root / p['root']), p['rules_file'])
        plan.put((root / p['root']) / p['manifest_file'], encoded(manifest))
    report = {'tools': states, 'module_observations': module_states, 'pending': pending,
              'scope': '已登记项目/工具及声明的模块路径；不扫描任意未登记项目，不执行业务接口。'}
    old_path = root / 'updates/latest.json'
    old = read_json(old_path) if old_path.exists() else {}
    module_changes = [x for x in module_states if x not in old.get('module_observations', [])]
    # Module diffs are a separate observation log; they do not erase manual review records.
    if module_changes:
        plan.put(root / 'updates/module-changes.json', encoded({'changes': module_changes, 'note': '仅源码指纹观察，需开发者核对模块依赖影响；不是接口验收。'}))
    plan.put(root / 'registry.json', encoded(registry))
    plan.put(root / 'updates/latest.json', encoded(report))
    summary = ['# 全局接口更新结果', '', report['scope'], '', '## 待处理', '']
    summary += [f'- {item}' for item in pending] or ['无已登记工具/使用方源码审查待办。']
    summary += ['', '## 工具快照', '']
    summary += [f'- [{t["id"]}](../{Path(t["guide"]).parent}/INTERFACE.generated.md)：{t["sync_state"]}' for t in registry['tools']]
    summary += ['', '模块指纹变化另见 module-changes.json（最近一次变化记录，需结合当前源码核对）。', '', '公共规则与反向关系由命令同步；业务契约说明和适配代码由开发者维护。', '']
    plan.put(root / 'updates/latest.md', '\n'.join(summary))
    if accept_tool or acknowledge:
        changelog = root / 'CHANGELOG.md'
        existing = changelog.read_text() if changelog.exists() else '# 变更记录\n'
        label = f'源码审查 {accept_tool}' if accept_tool else f'使用方核对 {acknowledge[0]} → {acknowledge[1]}'
        plan.put(changelog, existing.rstrip() + f'\n\n- {datetime.now().date()}：{label}。{note.strip()}（命令未执行业务验收。）\n')
    return plan, pending


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check')
    sub.add_parser('update')
    p = sub.add_parser('install'); p.add_argument('--project', type=Path, required=True)
    p = sub.add_parser('accept'); p.add_argument('--tool', required=True); p.add_argument('--note', required=True)
    p = sub.add_parser('acknowledge'); p.add_argument('--project', required=True); p.add_argument('--tool', required=True); p.add_argument('--note', required=True)
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    try:
        if args.command == 'check':
            plan, pending = update_plan(root)
            errors, notes, counts = check_links.check(root)
            for line in pending + errors:
                print('待处理：' + line)
            print(f'检查：{counts}；待同步文件 {len(plan.items)}，未写入文件。')
            for path in plan.items:
                print('待同步：' + str(path))
            return int(bool(plan.items or pending or errors))
        with locked(root):
            if args.command == 'install':
                return install(root, args.project)
            plan, pending = update_plan(root, accept_tool=args.tool if args.command == 'accept' else None,
                                        acknowledge=(args.project, args.tool) if args.command == 'acknowledge' else None,
                                        note=getattr(args, 'note', None))
            count = plan.commit(root)
            errors, notes, counts = check_links.check(root)
            for line in pending + errors:
                print('待处理：' + line)
            print(f'全局更新完成：{count} 个文件，{counts}。报告：{root / "updates/latest.md"}')
            return int(bool(pending or errors))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, StopIteration, SyntaxError) as error:
        print(f'未完成：{error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
