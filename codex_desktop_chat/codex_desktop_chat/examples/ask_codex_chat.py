"""Explicit, standalone text example. Does not start or alter the paper pipeline."""
import argparse
import json
from pathlib import Path
from codex_desktop_chat import ask_once, DesktopChatError

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prompt-file',required=True,type=Path)
    parser.add_argument('--file',action='append',type=Path,default=[])
    parser.add_argument('--state-dir',required=True,type=Path)
    parser.add_argument('--foreground',action='store_true',required=True)
    args=parser.parse_args()
    try:
        answer=ask_once(args.prompt_file.read_text(encoding='utf-8'),state_dir=args.state_dir,foreground=args.foreground,files=args.file)
        print(json.dumps({'ok':True,'answer':answer},ensure_ascii=False))
    except DesktopChatError as e:
        print(json.dumps({'ok':False,'error':e.as_dict()},ensure_ascii=False));return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
