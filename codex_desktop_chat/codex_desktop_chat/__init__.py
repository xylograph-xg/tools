"""Reusable native Codex Chat transport; does not use Codex CLI/app-server models."""
from .core import ChatGPTDesktop
from .errors import DesktopChatError
from .bundles import prepare_upload_bundle
__version__ = "1.0.0"
__all__ = ["ChatGPTDesktop", "DesktopChatError", "ask_once", "create_session", "prepare_upload_bundle"]

def create_session(provider="codex-chat", **kwargs):
    if provider != "codex-chat":
        raise ValueError("Only explicit provider='codex-chat' is supported; no automatic fallback")
    return ChatGPTDesktop(**kwargs)

def ask_once(prompt, files=None, answer_timeout=900, *, model="GPT-6", thinking_high=True,
             state_dir=None, foreground=False, poll_interval=10, upload_timeout=180, bundle_dir=None):
    from .attachments import validate_files
    validate_files(files)
    with ChatGPTDesktop(model=model,thinking_high=thinking_high,state_dir=state_dir,
                        foreground=foreground,poll_interval=poll_interval,bundle_dir=bundle_dir) as chat:
        return chat.ask(prompt,files=files,answer_timeout=answer_timeout,upload_timeout=upload_timeout)
