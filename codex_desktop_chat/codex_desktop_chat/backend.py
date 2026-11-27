"""Private macOS transport. JSON over stdin; no shell interpolation or clipboard."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import tempfile
import fcntl
from .errors import DesktopChatError

class NativeBackend:
    def __init__(self, bundle_id="com.openai.codex", *, helper_path=None):
        self.bundle_id = bundle_id
        self.window_id = None
        self.helper_path = Path(helper_path or os.environ.get("CODEX_CHAT_NATIVE_HELPER", "")) if (helper_path or os.environ.get("CODEX_CHAT_NATIVE_HELPER")) else None

    def _helper(self):
        if platform.system() != "Darwin":
            raise DesktopChatError("unsupported_platform", "This transport requires macOS")
        if self.helper_path:
            if not self.helper_path.is_file():
                raise DesktopChatError("missing_helper", str(self.helper_path))
            return self.helper_path
        source = Path(__file__).with_name("native.swift")
        if not source.is_file():
            raise DesktopChatError("missing_native_resource", "Installed package lacks native.swift")
        key = hashlib.sha256(source.read_bytes()).hexdigest()[:20]
        cache = Path(tempfile.gettempdir()) / f"codex-chat-native-{os.getuid()}"
        cache.mkdir(mode=0o700, parents=True, exist_ok=True)
        target = cache / f"helper-{key}"
        with (cache / "build.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if not target.is_file():
                temp = target.with_suffix(".building")
                try:
                    result = subprocess.run(["/usr/bin/swiftc", "-module-cache-path", str(cache / "modules"),
                                             str(source), "-o", str(temp)], capture_output=True, text=True, timeout=180)
                    if result.returncode:
                        raise DesktopChatError("build_failed", result.stderr[-4000:])
                    os.replace(temp, target)
                finally:
                    temp.unlink(missing_ok=True)
        return target

    def call(self, op, *, timeout=30, **args):
        request = {"op": op, "bundle_id": self.bundle_id, **args}
        if self.window_id is not None and op not in {"windows", "new_window"}:
            request["window_id"] = self.window_id
        try:
            result = subprocess.run([str(self._helper())], input=json.dumps(request, ensure_ascii=False),
                                    capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as e:
            raise DesktopChatError("native_timeout", f"Native operation {op} timed out") from e
        except OSError as e:
            raise DesktopChatError("native_unavailable", str(e)) from e
        try:
            payload = json.loads(result.stdout)
        except ValueError as e:
            raise DesktopChatError("native_protocol", result.stderr[-1000:] or "No JSON from helper") from e
        if not payload.get("ok"):
            raise DesktopChatError(payload.get("code", "native_error"), payload.get("message", "Native operation failed"))
        return payload

    def snapshot(self):
        return self.call("snapshot")

    def press(self, query, **guards):
        return self.call("press", query=query, **guards)

    def type_text(self, text, **guards):
        return self.call("type", query={"role": "AXTextArea", "label": "询问 ChatGPT"},
                         text=text, allow_foreground=True, timeout=max(30, len(text) * .05 + 10), **guards)

    def escape(self):
        # The unique window is the semantic target; typing never depends on coordinates.
        return self.call("key", query={"role": "AXWindow"}, keycode=53, allow_foreground=True)
