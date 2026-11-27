"""CLI stdout is exactly one JSON result; status never submits or creates a chat."""
import argparse
import json
from pathlib import Path
import sys
from . import ChatGPTDesktop, DesktopChatError, prepare_upload_bundle
from .backend import NativeBackend
from .state import ReceiptStore

def main():
    parser=argparse.ArgumentParser(description="Native Codex Chat tool (text and attachments)")
    parser.add_argument("command",choices=("status","verify","ask","submit","collect","verify-attachments","prepare"),nargs="?",default="status")
    parser.add_argument("--prompt-file",type=Path,help="UTF-8 prompt; avoids text in process arguments")
    parser.add_argument("--file",action="append",type=Path,default=[],help="Absolute attachment path; repeat for multiple files")
    parser.add_argument("--bundle-dir",type=Path)
    parser.add_argument("--upload-timeout",type=float,default=180)
    parser.add_argument("--state-dir",type=Path)
    parser.add_argument("--window-id",type=int)
    parser.add_argument("--receipt-id")
    parser.add_argument("--model",default="GPT-6",choices=("GPT-6","GPT-5.6 Sol"))
    parser.add_argument("--foreground",action="store_true",help="Explicitly allow foreground UI/keyboard use")
    parser.add_argument("--answer-timeout",type=float,default=900)
    parser.add_argument("--poll-interval",type=float,default=10)
    args=parser.parse_args()
    if args.file and args.command not in ("ask","submit","prepare"):
        parser.error("--file only applies to ask/submit/prepare")
    try:
        if args.command=="prepare":
            result={"ok":True,"result":prepare_upload_bundle(args.file,bundle_dir=args.bundle_dir)}
        elif args.command=="status":
            result={"ok":True,"provider":"codex-chat","attachments_supported":True,"native":NativeBackend().call("windows")}
        else:
            if args.command in ("ask","submit") and not args.prompt_file:
                parser.error("--prompt-file is required for ask/submit")
            window=args.window_id
            if args.command=="collect":
                if not args.receipt_id or not args.state_dir:
                    parser.error("collect requires --receipt-id and --state-dir")
                r=ReceiptStore(args.state_dir).load(args.receipt_id); window=r["window_id"]
            if args.command in ("verify","verify-attachments") and window is None:
                parser.error("verify/verify-attachments requires --window-id")
            with ChatGPTDesktop(new_chat=args.command in ("ask","submit"),window_id=window,
                                model=args.model,foreground=args.foreground,state_dir=args.state_dir,
                                poll_interval=args.poll_interval,bundle_dir=args.bundle_dir) as chat:
                if args.command=="verify": value=chat.verify_settings()
                elif args.command=="verify-attachments": value=chat.verify_attachment_channel()
                elif args.command=="collect": value=chat.collect(args.receipt_id,answer_timeout=args.answer_timeout)
                else:
                    prompt=args.prompt_file.read_text(encoding="utf-8")
                    value=chat.submit(prompt,files=args.file,upload_timeout=args.upload_timeout)
                    if args.command=="ask": value=chat.collect(value,answer_timeout=args.answer_timeout)
                result={"ok":True,"provider":"codex-chat","result":value,"window_id":chat.window_id}
        print(json.dumps(result,ensure_ascii=False))
        return 0
    except DesktopChatError as e:
        print(json.dumps({"ok":False,"error":e.as_dict()},ensure_ascii=False))
        return 2
    except (OSError,ValueError) as e:
        print(json.dumps({"ok":False,"error":{"code":"invalid_input","message":str(e),"may_have_sent":False}},ensure_ascii=False))
        return 2

if __name__=="__main__": sys.exit(main())
