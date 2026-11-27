#!/bin/bash
# 双击后输入项目名；也可运行：./新建项目.command "项目名称"
set -eu
TASK_PROJECT_BASE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TASK_INTERACTIVE=0
if [ "$#" -eq 0 ]; then
  TASK_INTERACTIVE=1
  printf '项目名称（将在 %s 下创建）：' "$TASK_PROJECT_BASE"
  IFS= read -r TASK_PROJECT_NAME || exit 0
elif [ "$#" -eq 1 ]; then
  TASK_PROJECT_NAME=$1
else
  printf '用法：%s [项目名称]\n' "$0" >&2
  exit 2
fi
TASK_RESULT=0
python3 - "$TASK_PROJECT_BASE" "$TASK_PROJECT_NAME" <<'PY' || TASK_RESULT=$?
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

base = Path(sys.argv[1]).resolve()
name = sys.argv[2].strip()
if not name:
    print('未输入项目名称，已取消。')
    sys.exit(0)
if name in {'.', '..'} or name.startswith('.') or any(c in name for c in '/\\:') or any(ord(c) < 32 for c in name):
    print('项目名称不能以点开头，也不能包含路径分隔符、冒号或控制字符。')
    sys.exit(2)
hub = base / 'tools'
try:
    for relative in ('all/README.md', 'all/RULES.md', 'all/setup.py', 'all/hub.json', 'scripts/sync_tools.py', 'scripts/check_links.py', 'projects.json'):
        if not (hub / relative).is_file():
            raise ValueError(f'缺少中央文件：{hub / relative}')
    index = json.loads((hub / 'projects.json').read_text(encoding='utf-8'))
    if any(p['name'] == name for p in index['projects']):
        raise ValueError(f'项目名称已登记：{name}，请使用其他名称。')
    project = base / name
    if project.exists() or project.is_symlink():
        raise ValueError(f'文件夹或文件已存在：{project}，请使用其他名称。')
    project.mkdir()
    # 只复制公共接入文件，不复制缓存或旧安装标记。
    (project / 'all').mkdir(exist_ok=True)
    for filename in ('README.md', 'RULES.md', 'setup.py', 'hub.json'):
        shutil.copy2(hub / 'all' / filename, project / 'all' / filename)
    env = dict(os.environ, TOOLS_HOME=str(hub))
    subprocess.run([sys.executable, str(project / 'all/setup.py')], env=env, check=True)
    for script, args in (('sync_tools.py', ['update']), ('sync_tools.py', ['check']), ('check_links.py', [])):
        result = subprocess.run([sys.executable, str(hub / 'scripts' / script), '--root', str(hub), *args], env=env)
        if result.returncode:
            print(f'项目已创建并登记：{project}；全局检查存在待办，请查看上方输出。')
            sys.exit(result.returncode)
    print(f'\n项目已创建：{project}\n已配置 all/、AGENTS.md 和 tool-dependencies.json；后续会纳入全局更新。')
except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
    print(f'创建未完成：{exc}', file=sys.stderr)
    print('若目录已生成，将保留文件供检查，不会覆盖或删除已有项目。', file=sys.stderr)
    sys.exit(2)
PY
if [ "$TASK_INTERACTIVE" -eq 1 ]; then
  printf '\n按回车关闭窗口…'
  IFS= read -r TASK_UNUSED || true
fi
exit "$TASK_RESULT"
