"""Persistent, single-dispatch client for the local Codex Web GPT bridge (POSIX)."""
import contextlib
import fcntl
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import subprocess
import time

MODEL = "chatgpt-web/gpt-6.2-sol"
DEFAULT_STATE = Path.home() / ".local" / "state" / "codex-web-client"
FINAL = {"answered", "executed", "verified"}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _unique_fields(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate JSON field")
    return result


# Slugs and effort values supported by the local Web GPT 6.2 catalog.
PRO_FIRST = (("chatgpt-web/gpt-6-pro", "max"), (MODEL, "xhigh"), (MODEL, "high"))


def _room_for_turn(health):
    turns = health.get("active_browser_turns")
    return health["ready"] and type(turns) is int and 0 <= turns < 5


def _terminal_error(events):
    """Only the CLI's terminal error can classify a failed attempt."""
    messages = []
    progressed = False
    try:
        with events.open(encoding="utf-8") as stream:
            for line in stream:
                event = json.loads(line)
                if event["type"] in ("item.started", "item.completed", "turn.completed"):
                    progressed = True
                if event["type"] == "turn.failed":
                    messages.append(event["error"]["message"])
    except (OSError, ValueError, TypeError, KeyError):
        return None
    if len(messages) != 1 or not isinstance(messages[0], str):
        return None
    return messages[0], progressed


def _quota_error(events, profile):
    error = _terminal_error(events)
    if error is None:
        return None
    note, progressed = error
    if re.search(r"attachment|upload|file size|context length|account quota|附件|上传|账户额度|may have|might have", note, re.I):
        return None
    model = {PRO_FIRST[0]: r"GPT[- ]6(?: Astra)? Pro",
             PRO_FIRST[1]: r"(?:extra[- ]high|xhigh|超高)",
             PRO_FIRST[2]: r"(?<!extra )(?<!extra-)(?<!x)\bhigh\b|高强度"}[profile]
    exhausted = r"(?:reached|hit|exceeded|exhausted|used up|用完|耗尽|已达|达到)"
    quota = r"(?:limit|quota|allowance|上限|额度|限额)"
    if not re.search(model, note, re.I) or not (
            re.search(exhausted + r".{0,90}" + quota, note, re.I)
            or re.search(quota + r".{0,90}" + exhausted, note, re.I)):
        return None
    unsent = not progressed and bool(re.search(
        r"(?:pending (?:message|prompt)|(?:message|prompt)) was not sent|before the prompt was sent|提示未发送|消息未发送",
        note, re.I))
    return note[:1500], unsent


def _evaluate(events_file, answer_file, spec):
    completed = 0
    failed = False
    native = 0
    message = None
    with events_file.open(encoding="utf-8") as stream:
        for line in stream:
            e = json.loads(line)
            kind = e["type"]
            if kind == "turn.completed":
                completed += 1
            elif kind == "turn.failed":
                failed = True
            elif kind == "item.completed":
                item = e["item"]
                if item["type"] == "agent_message":
                    message = item.get("text")
                if item["type"] == "command_execution" and item.get("exit_code") == 0:
                    native += 1
    answer = answer_file.read_text(encoding="utf-8").strip() if answer_file.exists() else ""
    if completed != 1 or failed or not answer or not isinstance(message, str) or message.strip() != answer:
        return "review", "incomplete_or_inconsistent_answer", native, answer
    if spec["require_command"] and not native:
        return "review", "missing_successful_command", native, answer
    if spec.get("json_match") is not None:
        try:
            fields = json.loads(answer, object_pairs_hook=_unique_fields)
            if not isinstance(fields, dict) or not all(
                k in fields and _json(fields[k]) == _json(v) for k, v in spec["json_match"].items()
            ):
                return "review", "json_fields_mismatch", native, answer
        except (ValueError, RecursionError):
            return "review", "invalid_json", native, answer
        return "verified", None, native, answer
    if spec["expected"] is not None:
        if answer != spec["expected"]:
            return "review", "answer_mismatch", native, answer
        return "verified", None, native, answer
    return ("executed" if spec["require_command"] else "answered"), None, native, answer


class Client:
    """Use one persistent state directory for every producer and worker of a queue."""

    def __init__(self, state_dir=DEFAULT_STATE, *, port=17841, timeout=240):
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("invalid port")
        if type(timeout) is not int or not 1 <= timeout <= 86400:
            raise ValueError("timeout must be 1..86400 seconds")
        self.port = port
        self.timeout = timeout
        self.root = Path(state_dir).expanduser().resolve()
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.root.stat().st_mode & 0o077 or self.root.stat().st_uid != os.getuid():
            raise ValueError("state directory must be owned by you and private (0700)")
        self.db = self.root / "jobs.sqlite3"
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, spec TEXT NOT NULL, state TEXT NOT NULL,
                reason TEXT, commands INTEGER NOT NULL DEFAULT 0, answer TEXT,
                created REAL NOT NULL, updated REAL NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS model_attempts (
                job TEXT NOT NULL, number INTEGER NOT NULL, model TEXT NOT NULL, effort TEXT NOT NULL,
                quota_note TEXT, next_probe REAL, PRIMARY KEY(job,number))""")
            db.execute("CREATE INDEX IF NOT EXISTS queue_order ON jobs(state,created,id)")
            db.execute("""CREATE TABLE IF NOT EXISTS dispatch (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                failures INTEGER NOT NULL, next_at REAL NOT NULL)""")
            db.execute("INSERT OR IGNORE INTO dispatch VALUES(1,0,0)")

    @contextlib.contextmanager
    def _connect(self):
        with contextlib.closing(sqlite3.connect(self.db, timeout=15)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db

    def health(self):
        """Probe the loopback service directly, without a proxy, redirects or credentials."""
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            conn.request("GET", "/healthz")
            response = conn.getresponse()
            if response.status != 200:
                return {"ready": False, "reason": f"http_{response.status}"}
            data = json.loads(response.read(65537))
            fields = ("version", "pid", "mode", "active_http_turns", "active_browser_turns")
            return {**{k: data.get(k) for k in fields},
                    "ready": data.get("status") == "ok" and data.get("accepting_turns") is True
                             and data.get("mode") == "full"}
        except (OSError, http.client.HTTPException, ValueError, AttributeError) as exc:
            return {"ready": False, "reason": type(exc).__name__}
        finally:
            conn.close()

    def submit(self, key, prompt, *, workdir=None, require_command=False, expected=None, json_match=None,
               images=(), guarded=False):
        """Enqueue locally. Repeating an identical key and input returns the original receipt."""
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", key):
            raise ValueError("key must be 1..100 ASCII letters, digits, underscores or hyphens")
        if not isinstance(prompt, str) or not prompt.strip() or type(require_command) is not bool:
            raise ValueError("invalid prompt or require_command")
        if expected is not None and (not isinstance(expected, str) or not expected or expected.strip() != expected):
            raise ValueError("expected must be a nonempty string without outer whitespace")
        if json_match is not None:
            if expected is not None or not isinstance(json_match, dict) or not json_match or not all(
                isinstance(k, str) for k in json_match
            ):
                raise ValueError("supply either expected or a nonempty json_match object")
        cwd = Path(workdir).expanduser().resolve() if workdir is not None else None
        if cwd is not None and not cwd.is_dir():
            raise ValueError("workdir does not exist")
        if type(guarded) is not bool or not isinstance(images, (list, tuple)) or len(images) > 10:
            raise ValueError("invalid guarded flag or image list (maximum 10)")
        extras = {}
        if images:
            frozen = []
            for name in images:
                path = Path(name).expanduser().resolve(strict=True)
                if not path.is_file():
                    raise ValueError("image is not a file")
                frozen.append([str(path), hashlib.sha256(path.read_bytes()).hexdigest()])
            extras["images"] = frozen
        if guarded:
            extras["guarded"] = True
        spec = _json(dict(prompt=prompt, workdir=str(cwd) if cwd else None,
                          port=self.port, model=MODEL, effort="high",
                          require_command=require_command, expected=expected, json_match=json_match, **extras))
        now = time.time()
        with self._connect() as db:
            db.execute("INSERT OR IGNORE INTO jobs(id,spec,state,created,updated) VALUES(?,?,'queued',?,?)",
                       (key, spec, now, now))
            if db.execute("SELECT spec FROM jobs WHERE id=?", (key,)).fetchone()[0] != spec:
                raise ValueError("key already belongs to a different request")
        return self.get(key)

    def get(self, key):
        with self._connect() as db:
            row = db.execute("SELECT id,state,reason,commands,answer,created,updated FROM jobs WHERE id=?",
                             (key,)).fetchone()
            if row is None:
                raise KeyError(key)
            result = dict(row)
            attempt = db.execute("SELECT model,effort FROM model_attempts WHERE job=? ORDER BY number DESC LIMIT 1",
                                 (key,)).fetchone()
            if attempt:
                result.update(attempt)
            return result

    def counts(self):
        with self._connect() as db:
            return dict(db.execute("SELECT state,count(*) FROM jobs GROUP BY state").fetchall())

    def dispatch_status(self):
        with self._connect() as db:
            row = db.execute("SELECT failures,next_at FROM dispatch WHERE singleton=1").fetchone()
            return {"consecutive_reviews": row["failures"], "next_dispatch_at": row["next_at"]}

    def _save(self, key, state, reason=None, commands=0, answer=None, *, minimum_delay=0, parallel=False):
        with self._connect() as db:
            db.execute("UPDATE jobs SET state=?,reason=?,commands=?,answer=?,updated=? WHERE id=?",
                       (state, reason, commands, answer, time.time(), key))
            if state == "review":
                failures = db.execute("SELECT failures FROM dispatch WHERE singleton=1").fetchone()[0] + 1
                delay = max(minimum_delay, min(300, 30 * 2 ** min(failures - 1, 4)))
                db.execute("UPDATE dispatch SET failures=?,next_at=max(next_at,?) WHERE singleton=1",
                           (failures, time.time() + delay))
            elif state in FINAL:
                db.execute("UPDATE dispatch SET failures=0,next_at=0 WHERE singleton=1 AND (? OR next_at<=?)",
                           (not parallel,time.time()))
        return self.get(key)

    def _receipt_dir(self, key):
        return self.root / ("job-" + hashlib.sha256(key.encode()).hexdigest())

    def _finish(self, key, spec, folder, *, parallel=False):
        try:
            state, reason, commands, answer = _evaluate(folder / "events.jsonl", folder / "answer.txt", spec)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            return self._save(key, "review", "unreadable_or_partial_receipt")
        return self._save(key, state, reason, commands, answer, parallel=parallel)

    def run_once(self, *, before_send=None, key=None, pro_first=False, parallel_slot=None, allow_pro=True):
        """Dispatch at most one queued task or reconcile one interrupted task. Never replays a send."""
        parallel = parallel_slot is not None
        if parallel and (type(parallel_slot) is not int or not 0 <= parallel_slot < 5 or not key or not before_send):
            raise ValueError("parallel dispatch requires a slot 0..4, a key and a send guard")
        with contextlib.ExitStack() as stack:
            paths = [(self.root / "worker.lock", fcntl.LOCK_SH if parallel else fcntl.LOCK_EX)]
            if parallel:
                job_dir = self._receipt_dir(key)
                job_dir.mkdir(mode=0o700, exist_ok=True)
                paths.extend([(self.root / f"worker-{parallel_slot}.lock", fcntl.LOCK_EX),
                              (job_dir / "worker.lock", fcntl.LOCK_EX)])
            lock_fds = []
            try:
                for path, mode in paths:
                    lock = stack.enter_context(path.open("a"))
                    fcntl.flock(lock, mode | fcntl.LOCK_NB)
                    lock_fds.append(lock.fileno())
            except BlockingIOError:
                return {"state": "busy"}
            with self._connect() as db:
                row = db.execute("""SELECT id,spec,state FROM jobs WHERE state IN ('sending','queued') AND (? IS NULL OR id=?)
                    ORDER BY CASE state WHEN 'sending' THEN 0 ELSE 1 END,created,id LIMIT 1""", (key, key)).fetchone()
            if row is None:
                return {"state": "idle"}
            key, spec = row["id"], json.loads(row["spec"])
            if (parallel or pro_first) and (not spec.get("guarded") or before_send is None):
                raise ValueError("pro_first requires a guarded job and a send guard")
            folder = self._receipt_dir(key)
            with self._connect() as db:
                last = db.execute("SELECT max(number) FROM model_attempts WHERE job=?", (key,)).fetchone()[0]
            if row["state"] == "sending" and last:
                folder = folder / f"attempt-{last}"
            if row["state"] == "sending":
                if not (folder / "cli-exit-0").is_file():
                    return self._save(key, "review", "interrupted_without_confirmed_exit")
                return self._finish(key, spec, folder, parallel=parallel)
            dispatch = self.dispatch_status()
            if dispatch["next_dispatch_at"] > time.time():
                return {"state": "cooldown", **dispatch}
            if spec["port"] != self.port:
                return {"state": "unavailable", "reason": "worker_port_mismatch", "id": key}
            binary = shutil.which("codex")
            if not binary:
                return {"state": "unavailable", "reason": "codex_cli_missing", "id": key}
            health = self.health()
            if not health["ready"]:
                return {"state": "unavailable", "reason": "bridge_not_ready", "id": key}
            if parallel and not _room_for_turn(health):
                return {"state":"unavailable","reason":"App 暂无可用并行位置","id":key}
            model, effort = spec["model"], spec["effort"]
            if pro_first:
                with self._connect() as db:
                    held = {(r[0],r[1]):r[2] for r in db.execute("""SELECT model,effort,max(next_probe)
                        FROM model_attempts WHERE next_probe>? GROUP BY model,effort""", (time.time(),))}
                tiers = PRO_FIRST if allow_pro else PRO_FIRST[1:]
                profile = next((p for p in tiers if p not in held), None)
                if profile is None:
                    return {"state":"cooldown", "reason":"all_model_tiers_exhausted", "next_at":min(held[p] for p in tiers)}
                model, effort = profile
                number = (last or 0) + 1
                folder = folder / f"attempt-{number}"
            folder.mkdir(mode=0o700, parents=True, exist_ok=True)
            if spec["workdir"]:
                cwd = Path(spec["workdir"])
                if not cwd.is_dir():
                    return self._save(key, "not_sent", "workdir_missing")
            else:
                cwd = folder / "work"
                cwd.mkdir(mode=0o700, exist_ok=True)
            args = [binary, "exec", "--skip-git-repo-check", "-s", "read-only", "-C", str(cwd),
                    "-c", 'model_provider="openai"', "-c", f'openai_base_url="http://127.0.0.1:{self.port}/v1"',
                    "-c", f'model_reasoning_effort="{effort}"', "-m", model,
                    "--json", "-o", str(folder / "answer.txt"), "-"]
            if spec.get("guarded") and before_send is None:
                return {"state": "unavailable", "reason": "send_guard_required", "id": key}
            for name, sha in spec.get("images", []):
                path = Path(name)
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
                    return self._save(key, "not_sent", "frozen_image_changed")
                args[-1:-1] = ["--image", name]
            if before_send is not None:
                reason = before_send(key)
                if reason:
                    return {"state": "unavailable", "reason": reason, "id": key}
            if parallel:
                health = self.health()
                if not _room_for_turn(health):
                    return {"state":"unavailable","reason":"App 暂无可用并行位置","id":key}
            with (folder / "events.jsonl").open("wb") as output, (folder / "stderr.log").open("wb") as error:
                with self._connect() as db:
                    if parallel:
                        db.execute("BEGIN IMMEDIATE")
                        now = time.time()
                        if db.execute("SELECT next_at FROM dispatch WHERE singleton=1").fetchone()[0] > now:
                            return {"state":"cooldown","reason":"App 队列冷却"}
                        if pro_first and db.execute("""SELECT 1 FROM model_attempts
                                WHERE model=? AND effort=? AND next_probe>? LIMIT 1""",(model,effort,now)).fetchone():
                            return {"state":"cooldown","reason":"模型额度等待复查"}
                    if pro_first:
                        db.execute("INSERT INTO model_attempts(job,number,model,effort) VALUES(?,?,?,?)",
                                   (key,number,model,effort))
                    db.execute("UPDATE jobs SET state='sending',reason=NULL,updated=? WHERE id=?", (time.time(),key))
                try:
                    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=output, stderr=error,
                                            cwd=cwd, start_new_session=True, pass_fds=tuple(lock_fds))
                except OSError as exc:
                    return self._save(key, "not_sent", type(exc).__name__)
                try:
                    proc.communicate(input=spec["prompt"].encode(), timeout=self.timeout)
                except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                    self._save(key, "review", type(exc).__name__)
                    if isinstance(exc, KeyboardInterrupt):
                        raise
                    return self.get(key)
            if proc.returncode:
                quota = _quota_error(folder / "events.jsonl", profile) if pro_first else None
                if quota:
                    note, unsent = quota
                    with self._connect() as db:
                        db.execute("UPDATE model_attempts SET quota_note=?,next_probe=? WHERE job=? AND number=?",
                                   (note,time.time()+900,key,number))
                        if unsent:
                            db.execute("UPDATE jobs SET state='queued',reason=?,updated=? WHERE id=?",
                                       ("model_quota_before_send",time.time(),key))
                    if unsent:
                        return {"state":"cooldown", "reason":"model_quota_before_send", "id":key}
                if pro_first:
                    terminal = _terminal_error(folder / "events.jsonl")
                    if terminal and re.search(
                            r"upload_quota_exceeded|attachment upload limit (?:was )?(?:exceeded|reached)|"
                            r"insufficient_quota|account quota (?:exhausted|exceeded)", terminal[0], re.I):
                        return self._save(key, "review", "app_account_or_attachment_quota", minimum_delay=900)
                return self._save(key, "review", f"cli_exit_{proc.returncode}")
            (folder / "cli-exit-0").touch(exist_ok=False)
            return self._finish(key, spec, folder, parallel=parallel)
