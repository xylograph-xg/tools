"""Durable receipts and one global lock for the shared desktop window."""
from pathlib import Path
from contextlib import contextmanager
import fcntl
import json
import os
import tempfile
import time
from typing import TypedDict, Literal
from .errors import DesktopChatError

Stage = Literal["preparing", "uploading", "submitting", "sent", "unknown", "not_sent", "completed"]

class Receipt(TypedDict, total=False):
    id: str
    schema_version: int
    stage: Stage
    window_id: int
    pid: int
    wire_prompt: str
    wire_sha256: str
    answer: str
    answer_sha256: str

TRANSITIONS = {
    "preparing": {"preparing", "uploading", "submitting", "not_sent"},
    "uploading": {"uploading", "submitting", "not_sent"},
    "submitting": {"submitting", "sent", "unknown", "not_sent", "completed"},
    "sent": {"sent", "unknown", "completed"},
    "unknown": {"unknown", "completed"},
    "not_sent": {"not_sent"},
    "completed": {"completed"},
}

TERMINAL = {"completed", "not_sent"}

def atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".receipt-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n"); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)

class ReceiptStore:
    def __init__(self, folder):
        self.folder = Path(folder).expanduser().resolve()
        self.folder.mkdir(mode=0o700, parents=True, exist_ok=True)

    def path(self, receipt_id):
        if not isinstance(receipt_id, str) or len(receipt_id) != 32 or any(c not in "0123456789abcdef" for c in receipt_id):
            raise DesktopChatError("invalid_receipt", "Receipt id must be 32 hexadecimal characters")
        return self.folder / f"{receipt_id}.json"

    def save(self, receipt: Receipt):
        if receipt.get("schema_version") != 1 or receipt.get("stage") not in TRANSITIONS:
            raise DesktopChatError("invalid_receipt", "Unsupported receipt schema or stage")
        path = self.path(receipt["id"])
        if path.exists():
            previous = self.load(receipt["id"])
            if receipt["stage"] not in TRANSITIONS[previous["stage"]]:
                raise DesktopChatError("invalid_receipt_transition", "Receipt stage cannot move backwards or resend")
        atomic_json(self.path(receipt["id"]), receipt)

    def load(self, receipt_id):
        try:
            value = json.loads(self.path(receipt_id).read_text())
            if value.get("id") != receipt_id or value.get("schema_version") != 1 or value.get("stage") not in TRANSITIONS:
                raise ValueError("Invalid receipt schema")
            return value
        except (OSError, ValueError, AttributeError, TypeError) as e:
            raise DesktopChatError("receipt_corrupt", f"Receipt cannot be read: {receipt_id}") from e

    def pending(self):
        out = []
        for p in self.folder.glob("*.json"):
            value = self.load(p.stem)
            if value.get("stage") not in TERMINAL:
                out.append(value)
        return out

@contextmanager
def desktop_lock(timeout=30):
    # Fixed path across all callers/state_dir choices. Serializes short UI transactions only; generation and polling waits never hold it.
    path = Path(tempfile.gettempdir()) / f"codex-desktop-chat-{os.getuid()}.lock"
    with path.open("a") as lock:
        limit = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= limit:
                    raise DesktopChatError("desktop_busy", "Another caller owns the desktop Chat window")
                time.sleep(.1)
        try: yield
        finally: fcntl.flock(lock, fcntl.LOCK_UN)
