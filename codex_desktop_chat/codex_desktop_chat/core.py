"""Desktop Chat sessions. Each owns a window; only short UI operations serialize."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import os
import time
import uuid
from .backend import NativeBackend
from .errors import DesktopChatError
from .bundles import prepare_upload_bundle, default_bundle_dir
from .attachments import validate_files, snapshot_files, verify_snapshots, attachment_names, upload_evidence, choose_file, formal_attachment_evidence, image_file_names, channel_issue
from .state import ReceiptStore, desktop_lock, atomic_json

def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _now():
    return datetime.now(timezone.utc).isoformat()

def _label(node):
    return node.get("title") or node.get("description") or node.get("value") or ""

def _visible(node):
    return node.get("width", 0) > 1 and node.get("height", 0) > 1

def _find(snapshot, role, label=None, *, visible=True):
    found = [n for n in snapshot["nodes"] if n["role"] == role
             and (label is None or label in (n.get("title"), n.get("description"), n.get("value")))
             and (not visible or _visible(n))]
    if role == "AXButton" and label == "新聊天":
        # Sidebar history may contain conversations literally titled 新聊天. The navigation
        # button has no AXDescription; history entries carry their conversation title.
        found = [n for n in found if not n.get("description")]
    if len(found) != 1:
        raise DesktopChatError("ambiguous_element", f"Expected unique {role}/{label}, found {len(found)}")
    return found[0]

def _query(node):
    q = {"role": node["role"], "title": node.get("title", ""),
         "description": node.get("description", "") }
    if not node.get("title") and not node.get("description") and node.get("value"):
        q["value"] = node["value"]
    return q

ASSISTANT_LABELS = ("ChatGPT 说：", "ChatGPT said:")
USER_LABELS = ("你说：", "您说：", "You said:")
COMPLETION_LABELS = ("回答已完成", "Response completed")

def _response_span(snapshot, wire_prompt):
    """Bind one assistant turn to an exact request; refuse ambiguous layouts."""
    nodes = snapshot["nodes"]
    matches = [i for i,n in enumerate(nodes) if n["role"] == "AXStaticText" and n.get("value") == wire_prompt]
    if not matches:
        raise DesktopChatError("anchor_pending", "Formal request is not rendered yet; only read-only waiting is allowed")
    if len(matches) != 1:
        raise DesktopChatError("conversation_mismatch", "Formal request anchor is ambiguous")
    anchor = matches[0]
    end = next((i for i in range(anchor+1,len(nodes))
                if nodes[i]["role"] == "AXHeading" and _label(nodes[i]) in USER_LABELS), len(nodes))
    headers = [i for i in range(anchor+1,end) if nodes[i]["role"] == "AXHeading" and _label(nodes[i]) in ASSISTANT_LABELS]
    if not headers:return None
    if len(headers) != 1:
        raise DesktopChatError("answer_layout_unknown", "Multiple assistant turns without a supported user boundary")
    heading = headers[0]
    parent = nodes[heading]["parent"]
    siblings = [i for i in range(heading+1,end) if nodes[i]["parent"] == parent]
    if not siblings:return None
    start = siblings[0]
    if nodes[start]["role"] != "AXGroup":
        raise DesktopChatError("answer_layout_unknown", "Answer container layout changed")
    stop = next((i for i in range(start+1,end) if nodes[i]["parent"] == parent), end)
    return heading, start, stop, end

def _answer(snapshot, wire_prompt):
    span = _response_span(snapshot, wire_prompt)
    if span is None:return None
    _,start,stop,_ = span
    if any(n["role"] in ("AXTable", "AXImage", "AXMath") for n in snapshot["nodes"][start+1:stop]):
        raise DesktopChatError("answer_layout_unknown", "Non-text response content requires a verified structured adapter")
    text_nodes = [n for n in snapshot["nodes"][start+1:stop]
                  if n["role"] in ("AXStaticText", "AXTextArea", "AXTextField") and n.get("value")]
    if not text_nodes:return None
    # Editable/code containers with textual descendants cannot safely be flattened twice.
    for n in text_nodes:
        if n["role"] != "AXStaticText" and any(t.get("parent") == n.get("id") for t in text_nodes):
            raise DesktopChatError("answer_layout_unknown", "Nested text representation needs an explicit adapter")
    parts=[]; previous=None
    for n in text_nodes:
        if previous and n.get("y",0) > previous.get("y",0)+max(previous.get("height",0),1)*.5:
            parts.append("\n")
        parts.append(n["value"]); previous=n
    return "".join(parts)

def _busy(snapshot):
    return any(n["role"] == "AXButton" and _label(n) in ("停止", "停止生成", "Stop")
               and _visible(n) for n in snapshot["nodes"])

def _complete(snapshot, wire_prompt=None):
    if wire_prompt is not None:
        span = _response_span(snapshot, wire_prompt)
        if span is None:return False
        heading,_,_,end = span
        snapshot = {"nodes":snapshot["nodes"][heading+1:end]}
    return any(n["role"] == "AXStaticText" and n.get("value") in COMPLETION_LABELS
               for n in snapshot["nodes"])

class ChatGPTDesktop:
    """Public synchronous interface, modeled after ChatGPTWeb.

    Sessions create independent windows by default. An explicit bound window is required
    for collection after restart. UI transactions share a lock; model generation runs in parallel.
    Native attachments wait for verified readiness; no implicit model fallback or automatic resend.
    """
    provider = "codex-chat"

    def __init__(self, new_chat=True, thinking_high=True, *, model="GPT-6", state_dir=None,
                 foreground=False, window_id=None, poll_interval=10, max_windows=20, backend=None, bundle_dir=None):
        if model not in ("GPT-6", "GPT-5.6 Sol"):
            raise ValueError("Supported exact models: GPT-6, GPT-5.6 Sol")
        if thinking_high is not True:
            raise ValueError("This release verifies High only")
        if not isinstance(poll_interval,(int,float)) or not 1 <= poll_interval <= 60:
            raise ValueError("poll_interval must be 1..60 seconds")
        if not isinstance(max_windows,int) or not 1 <= max_windows <= 20:
            raise ValueError("max_windows must be 1..20")
        if window_id is not None and (not isinstance(window_id,int) or window_id <= 0):
            raise ValueError("window_id must be a positive native window number")
        self.new_chat, self.model, self.foreground = new_chat, model, foreground
        self.poll_interval, self.max_windows = poll_interval, max_windows
        folder = state_dir or os.environ.get("CODEX_CHAT_STATE_DIR") or Path.home()/"Library/Application Support/codex-desktop-chat"
        self.store = ReceiptStore(folder)
        self.bundle_dir = Path(bundle_dir or default_bundle_dir()).expanduser().resolve()
        self.backend = backend or NativeBackend()
        self.backend.window_id = window_id
        self.window_id = window_id
        self.pid = None; self.settings = None; self._entered = False; self._pending = None

    def __enter__(self):
        if self.new_chat and not self.foreground:
            raise DesktopChatError("foreground_required", "Pass foreground=True to authorize desktop UI use")
        with desktop_lock():
            if self.window_id is None:
                if not self.new_chat:
                    raise DesktopChatError("window_required", "Resume/read existing sessions using an explicit window_id")
                before = self.backend.call("windows")
                ids = {w["id"] for w in before["windows"]}
                self.backend.call("new_window", allow_foreground=True, max_windows=self.max_windows)
                deadline = time.monotonic()+10
                while True:
                    after = self.backend.call("windows")
                    added = [w["id"] for w in after["windows"] if w["id"] not in ids and isinstance(w["id"],int)]
                    if len(added) == 1:
                        self.window_id = self.backend.window_id = added[0]
                        atomic_json(self.store.folder / "windows" / (uuid.uuid4().hex+".json"),
                                    {"window_id":self.window_id,"pid":after["pid"],"created_at":_now(),"owned":True})
                        break
                    if len(added) > 1 or time.monotonic() >= deadline:
                        raise DesktopChatError("window_identity_unknown", "New window cannot be uniquely bound; do not blindly open another")
                    time.sleep(.2)
            snapshot = self.backend.snapshot()
            self.pid = snapshot["pid"]
            self._entered = True
            if self.new_chat:
                self._start_new_chat_locked()
            else:
                pending = [r for r in self.store.pending() if r.get("window_id") == self.window_id]
                if len(pending)>1:
                    raise DesktopChatError("receipt_conflict", "Multiple unresolved requests claim this window")
                self._pending = pending[0]["id"] if pending else None
        return self

    def __exit__(self, *exc):
        self._entered = False
        # Never close, navigate, or cancel a sent/unknown request on exit.

    def _require(self):
        if not self._entered:
            raise DesktopChatError("session_not_open", "Use a with block to open this desktop session")

    def _snapshot(self):
        s = self.backend.snapshot()
        if s["pid"] != self.pid or s.get("window_id") != self.window_id:
            raise DesktopChatError("conversation_mismatch", "Original app/window identity changed")
        return s

    def _authorize_ui(self):
        if not self.foreground:
            raise DesktopChatError("foreground_required", "Pass foreground=True before any desktop UI action")

    def _press(self, role, label, **guards):
        self._authorize_ui()
        deadline=time.monotonic()+8
        while True:
            s = self._snapshot()
            try:
                n = _find(s,role,label)
                break
            except DesktopChatError as e:
                # Wait for newly opened windows/menus to expose controls; never repeat actions.
                if "found 0" not in str(e) or time.monotonic()>=deadline: raise
                time.sleep(.2)
        return self.backend.press(_query(n),expected_pid=self.pid,allow_foreground=True,**guards)

    def _empty_draft(self, snapshot):
        editors = [n for n in snapshot["nodes"] if n["role"] == "AXTextArea" and _visible(n)]
        if len(editors) > 1:
            raise DesktopChatError("ambiguous_editor", "Multiple visible editors")
        if editors:
            e = editors[0]; value = e.get("value", "")
            if value.strip() not in ("", "询问 ChatGPT", "使用 ChatGPT Work", "Ask ChatGPT"):
                raise DesktopChatError("draft_protected", "Existing user draft is protected")

    def _start_new_chat_locked(self):
        self._authorize_ui()
        if self._pending or any(r.get("window_id")==self.window_id for r in self.store.pending()):
            raise DesktopChatError("pending_request", "Collect or reconcile the original request before opening a new chat")
        deadline=time.monotonic()+10
        while True:
            snapshot = self._snapshot()
            if any(n["role"]=="AXTextArea" for n in snapshot["nodes"]): break
            if time.monotonic()>deadline: raise DesktopChatError("editor_unavailable","Window editor did not load")
            time.sleep(.2)
        self._empty_draft(snapshot)
        if any(n["role"]=="AXButton" and _label(n).startswith("移除") for n in snapshot["nodes"]):
            raise DesktopChatError("attachment_protected","Existing composer attachments are protected")
        if _busy(snapshot):
            raise DesktopChatError("pending_request", "An active answer protects this window")
        self._press("AXButton","新聊天")
        deadline=time.monotonic()+10
        while True:
            s=self._snapshot()
            try:
                chat=_find(s,"AXCheckBox","聊天")
                work=_find(s,"AXCheckBox","工作")
                _find(s,"AXTextArea","询问 ChatGPT")
                if chat.get("value")=="1" and work.get("value")=="0":
                    self._empty_draft(s)
                    break
            except DesktopChatError:
                pass
            if time.monotonic()>deadline:
                raise DesktopChatError("chat_mode_required","Fresh Chat mode was not verified")
            time.sleep(.2)
        self.settings=self._verify_settings_locked()

    def start_new_chat(self):
        self._require()
        with desktop_lock(): self._start_new_chat_locked()

    def _verify_settings_locked(self):
        self._authorize_ui()
        self.backend.call("activate",allow_foreground=self.foreground,expected_pid=self.pid)
        if not self.foreground:
            raise DesktopChatError("foreground_required","Model menu inspection requires foreground=True")
        self._press("AXPopUpButton","选择 ChatGPT 模型")
        self._press("AXMenuItem","选择模型")
        snapshot=self._snapshot()
        selected=_find(snapshot,"AXMenuItem",self.model)
        if selected.get("value")!="1":
            self.backend.press(_query(selected),expected_pid=self.pid,allow_foreground=True)
            # Re-open model list to verify selection; a click alone is not evidence.
            self._press("AXMenuItem","选择模型")
            selected=_find(self._snapshot(),"AXMenuItem",self.model)
            if selected.get("value")!="1":
                raise DesktopChatError("model_mismatch","Exact model selection did not take")
        self.backend.press(_query(selected),expected_pid=self.pid,allow_foreground=True)
        snapshot=self._snapshot()
        high=any(n["role"]=="AXStaticText" and n.get("value", "").startswith("高，第") for n in snapshot["nodes"])
        if not high:
            raise DesktopChatError("strength_mismatch","High was not verified; adjust the app manually")
        # Escape on the exact native window closes the menu, without editing input.
        self.backend.escape()
        return {"mode":"Chat","model":self.model,"thinking":"High","verified_at":_now()}

    def verify_settings(self):
        self._require()
        if self._pending:
            raise DesktopChatError("pending_request","Do not change menus during an unresolved request")
        with desktop_lock():
            self.settings=self._verify_settings_locked()
            return dict(self.settings)

    def submit(self, prompt, files=None, *, upload_timeout=180):
        self._require()
        paths=validate_files(files)
        if not isinstance(upload_timeout,(int,float)) or isinstance(upload_timeout,bool) or not 1<=upload_timeout<=3600:
            raise ValueError("upload_timeout must be 1..3600 seconds")
        if not isinstance(prompt,str) or not prompt.strip() or len(prompt.encode("utf-16-le"))//2 > 31500:
            raise ValueError("prompt must contain 1..31500 UTF-16 units")
        if not self.foreground:
            raise DesktopChatError("foreground_required","Pass foreground=True for typing/submission")
        if self._pending:
            raise DesktopChatError("pending_request","Original request is still pending; do not resend")
        bundle=prepare_upload_bundle(paths,bundle_dir=self.bundle_dir) if paths else None
        upload_paths=[Path(bundle["zip_path"])] if bundle else []
        with desktop_lock():
            if self._pending or any(r.get("window_id")==self.window_id for r in self.store.pending()):
                raise DesktopChatError("pending_request","Unresolved receipt protects this window")
            s=self._snapshot(); self._empty_draft(s)
            if paths:
                issue=channel_issue(s) or self._stored_attachment_issue()
                if issue:
                    atomic_json(self.store.folder/"channel"/"issue.json",{**issue,"observed_at":_now(),"blocked":True})
                    raise DesktopChatError("attachment_quota",issue["message"])
            if _busy(s): raise DesktopChatError("conversation_busy","Window is generating a previous response")
            if attachment_names(s): raise DesktopChatError("attachment_protected","Existing composer attachments are protected")
            self.settings=self._verify_settings_locked()
            receipt_id=uuid.uuid4().hex
            wire=prompt+" [Desktop request identity: "+receipt_id+"; ignore this identity when answering.]"
            if bundle:
                wire+=" [The attachment is a ZIP: extract it, check its file list, and read the enclosed materials. If extraction or any file cannot be read, state that explicitly; do not assume its contents.]"
            receipt={"schema_version":1,"id":receipt_id,"window_id":self.window_id,"pid":self.pid,
                     "stage":"preparing","created_at":_now(),"prompt":prompt,"prompt_sha256":_sha(prompt),
                     "wire_prompt":wire,"wire_sha256":_sha(wire),"settings":self.settings,"files":[],"upload_bundle":bundle}
            self._pending=receipt_id; self.store.save(receipt)
        clicked=False
        try:
            receipt['files']=snapshot_files(upload_paths,self.store.folder/'inputs'/receipt_id) if paths else []
            self.store.save(receipt)
            with desktop_lock():
                self._empty_draft(self._snapshot())
                self.backend.type_text(wire,expected_pid=self.pid)
                deadline=time.monotonic()+10
                while True:
                    editor=_find(self._snapshot(),"AXTextArea","询问 ChatGPT")
                    if editor.get("value") in (wire,wire+"\n"): break
                    if time.monotonic()>deadline: raise DesktopChatError("draft_mismatch","Typed request did not exactly match; not sent")
                    time.sleep(.2)
            upload_deadline=time.monotonic()+upload_timeout
            expected=[]
            for item in receipt['files']:
                if time.monotonic()>upload_deadline: raise DesktopChatError("attachment_timeout","Upload budget expired; message not sent")
                verify_snapshots([item])
                with desktop_lock():
                    editor=_find(self._snapshot(),"AXTextArea","询问 ChatGPT")
                    if editor.get('value') not in (wire,wire+'\n'): raise DesktopChatError('draft_mismatch','Draft changed before upload')
                    receipt.update(stage='uploading',uploading_file=item['name']); self.store.save(receipt)
                    choose_file(self.backend,item['snapshot_path'],self.pid)
                expected.append(item['name']); stable=0
                while time.monotonic()<upload_deadline:
                    with desktop_lock(timeout=min(30,max(.1,upload_deadline-time.monotonic()))):
                        evidence=upload_evidence(self._snapshot(),expected)
                    stable=stable+1 if evidence['ready'] else 0
                    if stable>=2:
                        item.update(upload_ready=True,upload_verified_at=_now())
                        self.store.save(receipt); break
                    time.sleep(min(1,max(0,upload_deadline-time.monotonic())))
                else: raise DesktopChatError('attachment_timeout','Attachment never reached stable ready state; message not sent')
            # Upload/poll waits run outside the shared UI lock: other sessions may submit/collect.
            with desktop_lock():
                verify_snapshots(receipt['files'])
                if expected and not upload_evidence(self._snapshot(),expected)['ready']:
                    raise DesktopChatError('attachment_not_ready','Attachments not ready immediately before send')
                self.settings=self._verify_settings_locked()
                receipt.update(stage="submitting",settings=self.settings,attachment_send_guard={"names":expected,"hashes":{f["name"]:f["sha256"] for f in receipt["files"]},"checked_at":_now()}); self.store.save(receipt)
                clicked=True
                self._press("AXButton","发送",draft_equals=wire,attachment_names=expected)
                deadline=time.monotonic()+15
                while True:
                    s=self._snapshot()
                    anchors=[n for n in s["nodes"] if n["role"]=="AXStaticText" and n.get("value")==wire]
                    if len(anchors)==1 and formal_attachment_evidence(s,wire,expected,image_file_names(receipt["files"])):
                        receipt.update(stage="sent",sent_at=_now(),formal_attachments_verified=bool(expected)); self.store.save(receipt)
                        return dict(receipt)
                    if time.monotonic()>deadline: raise DesktopChatError("submission_unknown","Formal exact request/attachments were not confirmed")
                    time.sleep(.3)
        except Exception as e:
            receipt.update(stage="unknown" if clicked else "not_sent",error=str(e),error_code=getattr(e,'code','submission_failed'),failed_at=_now())
            try:
                self.store.save(receipt)
            except Exception as persistence_error:
                raise DesktopChatError("receipt_persistence_failed", f"Original failure: {e}; receipt save failed: {persistence_error}", receipt_id=receipt_id, may_have_sent=clicked) from e
            if not clicked: self._pending=None
            raise DesktopChatError(getattr(e,"code","submission_failed"),str(e),receipt_id=receipt_id,may_have_sent=clicked) from e

    def collect(self, receipt, answer_timeout=900):
        self._require()
        if not isinstance(answer_timeout,(int,float)) or answer_timeout <= 0:
            raise ValueError("answer_timeout must be positive seconds")
        receipt_id=receipt if isinstance(receipt,str) else receipt["id"]
        r=self.store.load(receipt_id)
        if r.get("window_id")!=self.window_id or r.get("pid")!=self.pid or _sha(r.get("wire_prompt", ""))!=r.get("wire_sha256"):
            raise DesktopChatError("receipt_mismatch","Receipt/window/prompt fingerprint mismatch",receipt_id=receipt_id,may_have_sent=True)
        if r["stage"]=="completed":
            if _sha(r.get("answer", "")) != r.get("answer_sha256"):
                raise DesktopChatError("receipt_corrupt","Saved answer fingerprint mismatch")
            return r["answer"]
        if r["stage"] not in ("sent","unknown","submitting"):
            raise DesktopChatError("not_submitted","Receipt is not an unresolved submitted request")
        self._pending=receipt_id
        deadline=time.monotonic()+answer_timeout; last=None; stable=0
        while time.monotonic()<deadline:
            try:
                with desktop_lock(timeout=min(30,max(.1,deadline-time.monotonic()))):
                    s=self._snapshot()
                    verify_snapshots(r.get("files",[]))
                    answer=_answer(s,r["wire_prompt"])
                    if not formal_attachment_evidence(s,r["wire_prompt"],[f["name"] for f in r.get("files",[])],image_file_names(r.get("files",[]))):
                        raise DesktopChatError("attachment_receipt_mismatch","Original formal attachments were not confirmed")
                    done=_complete(s,r["wire_prompt"]) and not _busy(s)
            except DesktopChatError as e:
                if e.code == "anchor_pending":
                    stable=0; last=None
                    time.sleep(min(self.poll_interval,max(0,deadline-time.monotonic())))
                    continue
                raise DesktopChatError(e.code,str(e),receipt_id=receipt_id,may_have_sent=True) from e
            if answer and done:
                stable=stable+1 if answer==last else 1; last=answer
                if stable>=2:
                    r.update(stage="completed",answer=answer,answer_sha256=_sha(answer),completed_at=_now(),
                             scientific_verified=False,production_contract_complete=False)
                    self.store.save(r); self._pending=None
                    issue=channel_issue(s)
                    if issue: atomic_json(self.store.folder/"channel"/"issue.json",{**issue,"observed_at":_now(),"blocked":True})
                    return answer
            else: stable=0; last=None
            time.sleep(min(self.poll_interval,max(0,deadline-time.monotonic())))
        raise DesktopChatError("answer_timeout","Answer not fully collected; original window and receipt retained",
                               receipt_id=receipt_id,may_have_sent=True)

    def ask(self, prompt, files=None, answer_timeout=900, *, upload_timeout=180):
        return self.collect(self.submit(prompt,files=files,upload_timeout=upload_timeout),answer_timeout=answer_timeout)

    def _stored_attachment_issue(self):
        path=self.store.folder/"channel"/"issue.json"
        if not path.exists(): return None
        try:
            import json
            value=json.loads(path.read_text())
            if not isinstance(value,dict) or not isinstance(value.get("blocked"),bool): raise ValueError("Invalid channel issue")
            if value["blocked"] and (value.get("code")!="attachment_quota" or not isinstance(value.get("message"),str) or not isinstance(value.get("pid"),int) or not isinstance(value.get("window_id"),int)):
                raise ValueError("Invalid quota evidence")
            return value if value["blocked"] else None
        except (OSError,ValueError) as e:
            raise DesktopChatError("channel_state_corrupt","Attachment channel state needs manual reconciliation") from e

    def verify_attachment_channel(self):
        """Explicit read-only UI recheck; absence of a banner is not proof of successful upload."""
        self._require()
        with desktop_lock():
            previous=self._stored_attachment_issue()
            if previous:
                old=self.backend.window_id
                try:
                    self.backend.window_id=previous["window_id"]
                    snapshot=self.backend.snapshot()
                finally: self.backend.window_id=old
                if snapshot["pid"]!=previous["pid"]:
                    raise DesktopChatError("conversation_mismatch","Original quota window/App changed; reconcile manually")
            else: snapshot=self._snapshot()
            issue=channel_issue(snapshot)
            atomic_json(self.store.folder/"channel"/"issue.json",{**(issue or {}),"observed_at":_now(),"blocked":bool(issue)})
            return {"blocked":bool(issue),"issue":issue,"upload_success_proven":False}

    def status(self):
        self._require()
        with desktop_lock():
            s=self._snapshot()
            return {"provider":self.provider,"pid":self.pid,"window_id":self.window_id,
                    "generating":_busy(s),"pending_receipt_id":self._pending,"settings":self.settings,
                    "attachments_supported":True,"attachment_issue":channel_issue(s) or self._stored_attachment_issue()}
