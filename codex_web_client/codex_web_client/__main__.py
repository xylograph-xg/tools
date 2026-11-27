import argparse
import json
from pathlib import Path
import sys
import time

from .api import Client, DEFAULT_STATE, FINAL


def main():
    parser = argparse.ArgumentParser(description="Codex Web GPT persistent Python client")
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--port", type=int, default=17841)
    parser.add_argument("--timeout", type=int, default=240)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status")
    get = sub.add_parser("get")
    get.add_argument("key")
    add = sub.add_parser("submit")
    add.add_argument("key")
    src = add.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt")
    src.add_argument("--prompt-file", type=Path)
    add.add_argument("--workdir", type=Path)
    add.add_argument("--require-command", action="store_true")
    verify = add.add_mutually_exclusive_group()
    verify.add_argument("--expected")
    verify.add_argument("--json-match", type=json.loads)
    work = sub.add_parser("work")
    work.add_argument("--once", action="store_true")
    args = parser.parse_args()
    client = Client(args.state_dir, port=args.port, timeout=args.timeout)
    if args.action == "work":
        delay = 1
        while True:
            receipt = client.run_once()
            state = receipt["state"]
            if args.once or state not in {"busy", "idle", "unavailable", "cooldown"}:
                print(json.dumps(receipt, ensure_ascii=False), flush=True)
            if args.once:
                return 0 if state in FINAL | {"idle"} else 1
            if state in {"busy", "idle", "unavailable", "cooldown"}:
                time.sleep(delay)
                delay = min(delay * 2, 30)
            else:
                delay = 1
    if args.action == "status":
        result = {"app": client.health(), "jobs": client.counts(), "dispatch": client.dispatch_status()}
    elif args.action == "get":
        result = client.get(args.key)
    else:
        prompt = args.prompt_file.read_text(encoding="utf8") if args.prompt_file else args.prompt
        result = client.submit(args.key, prompt, workdir=args.workdir,
                               require_command=args.require_command, expected=args.expected, json_match=args.json_match)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
