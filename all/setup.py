#!/usr/bin/env python3
"""Copy all/ to a project, then run this once. Only the central updater is used."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    folder = Path(__file__).resolve().parent
    hub = Path(os.environ.get('TOOLS_HOME') or json.loads((folder / 'hub.json').read_text())['tools_root']).expanduser().resolve()
    project = folder.parent
    if project == hub:
        print('请先把 all 文件夹复制到新项目根目录，再运行该项目中的 all/setup.py。')
        return 2
    script = hub / 'scripts/sync_tools.py'
    if not script.is_file():
        print('找不到 tools 中央脚本；请设置 TOOLS_HOME 或修改 all/hub.json。')
        return 2
    return subprocess.call([sys.executable, str(script), '--root', str(hub), 'install', '--project', str(project)])


if __name__ == '__main__':
    raise SystemExit(main())
