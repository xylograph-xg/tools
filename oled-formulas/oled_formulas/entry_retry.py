"""Admit a proven pre-transfer failure once, after a later successful trial."""
import json
import os
import time

from core.api import control__read_record as read, services__atomic_json as write

from . import attachment_gate


def release_path(folder):
    marker = read(folder / 'entry-retry' / 'original.json')
    if marker.get('phase') == 'admitted':
        return folder / 'retry-unsent-slot-release.json'
    return folder / 'unsent-slot-release.json'


class EntryTraces:
    """Read append-only transfer evidence once, then consume just new complete lines."""
    def __init__(self, path):
        self.path = path
        self.identity = None
        self.offset = 0
        self.events = {}

    def refresh(self):
        with self.path.open('rb') as stream:
            stat = os.fstat(stream.fileno())
            identity = (stat.st_dev, stat.st_ino)
            if self.identity != identity or stat.st_size < self.offset:
                self.events.clear()
                self.offset = 0
                self.identity = identity
            stream.seek(self.offset)
            for line in stream:
                if not line.endswith(b'\n'):
                    return False
                if b'formula-display-' in line:
                    event = json.loads(line)
                    job = event.get('job_id', '')
                    if event.get('lane') == 'formula_only' and job.startswith('formula-display-'):
                        seen = self.events.setdefault(job, [])
                        if len(seen) < 3:
                            seen.append(event)
                self.offset += len(line)
        return True

    def verified(self, attempt, status):
        events = self.events.get(attempt['job_id'], [])
        if len(events) != 2:
            return None
        first, last = events
        binding = dict(job_id=attempt['job_id'], target_id=attempt['window_target'],
                       zip_sha256=attempt['zip_sha256'], owner_pid=status.get('pid'))
        if (not binding['owner_pid'] or any(event.get(k) != v for k, v in binding.items() for event in events)
                or first.get('event') != 'upload_started' or last.get('event') != 'upload_finished'
                or not first.get('upload_attempt_id') or first['upload_attempt_id'] != last.get('upload_attempt_id')
                or last.get('failure_kind') != 'entry_not_ready' or last.get('result') != 'failed'
                or last.get('attachment') != {} or last.get('settle') != {} or last.get('zip_identity_mismatch') is not False
                or [(v.get('stage'), v.get('outcome')) for v in last.get('stages', [])] != [('upload_ready_gate', 'failed')]):
            return None
        return events


def resume_one(db, output, control, gate, active, now, traces):
    from .formula_dispatch import historical_slot_receipt

    if gate.get('mode') != 'ready' or not active():
        return
    success = gate.get('last_success') or {}
    number = success.get('batch')
    if not isinstance(number, int) or not success.get('target') or not isinstance(success.get('at'), (int, float)):
        return
    receipt = read(output / 'batches' / f'{number:06d}' / 'attempt.json')
    if not attachment_gate.trial_success(receipt, success):
        return

    reasons=(attachment_gate.ENTRY_FAILURE,'后台发送按钮不可用，未发送','附件上传失败')
    candidates = db.execute("""select id,reason from batches where state='held' and reason in (?,?,?)
        and not exists(select 1 from entry_retries where batch=batches.id) order by id""", reasons).fetchall()
    if not candidates or not traces.refresh():
        return
    for batch,reason in candidates:
        folder = output / 'batches' / f'{batch:06d}'
        marker = folder / 'entry-retry' / 'original.json'
        old = read(marker)
        current_path = folder / 'attempt.json'
        current = read(current_path)
        attempt = old.get('attempt') if old else current
        status = read(folder / 'status.json')
        failed_at = status.get('time')
        if (not attempt or (current and current != attempt) or status.get('reason') != reason
                or not isinstance(failed_at, (int, float)) or not failed_at < success['at'] <= now
                or now - failed_at < attachment_gate.BACKOFF):
            continue
        release = folder / 'unsent-slot-release.json'
        if not historical_slot_receipt(control, output, batch, 'held', attempt.get('window_target'), attempt, release):
            continue
        transfer = traces.verified(attempt, status)
        if reason!=attachment_gate.ENTRY_FAILURE:
            from .slot_recovery import own_draft, upload_pair
            from .formula_only import digest
            restored=read(folder/'slot-recovery/page.json')
            events=traces.events.get(attempt['job_id'],[])
            expected=('ok','none') if reason=='后台发送按钮不可用，未发送' else ('failed','settle_timeout')
            if (restored.get('receipt')!=attempt or not own_draft(restored.get('view',{}),attempt)
                    or not upload_pair(events,attempt,status) or
                    (events[-1].get('result'),events[-1].get('failure_kind'))!=expected or
                    events[-1].get('zip_identity_mismatch') is not False or any(
                    not (folder/'slot-recovery'/f).is_file() or digest(folder/'slot-recovery'/f)!=restored.get(k)
                    for f,k in [('page.html','html_sha256'),('page.png','png_sha256')])):
                continue
            transfer=events
        if not transfer:
            continue
        evidence = dict(attempt=attempt, status=status, packet=read(folder/'packet.json'), release=read(release),
                        upload_events=transfer)
        if old and any(old.get(k) != v for k, v in evidence.items()):
            continue
        if not active():
            return
        if not old:
            old = dict(evidence, phase='prepared', recovery_trial=success, prepared_at=now)
            write(marker, old)
        archived = marker.parent / 'attempt.json'
        if current_path.exists():
            if archived.exists() or read(current_path) != attempt:
                continue
            os.rename(current_path, archived)
        if read(archived) != attempt or not active():
            continue
        # Mark the next receipt generation before exposing the batch to a worker.
        # A crash here resumes the same admission. Both database writes commit together.
        if old.get('phase') != 'admitted':
            write(marker, dict(old, phase='admitted', queued_at=now))
        with db:
            changed = db.execute("update batches set state='queued',reason=null where id=? and state='held' and reason=?",
                                 (batch, reason)).rowcount
            if changed:
                db.execute('insert into entry_retries(batch,admitted_at) values (?,?)', (batch, now))
                return batch


def recover_preflight(db, output, traces, active):
    """A failed local UI check cannot consume an upload. Recover each proven input once."""
    reasons=('页面缺少 Chat 模式控件，且不是已有会话','没有找到 ChatGPT 输入框')
    db.execute('create table if not exists preflight_recoveries(batch integer primary key,admitted real)')
    rows=db.execute("""select id,reason from batches where state='held' and reason in (?,?)
                       and id not in (select batch from preflight_recoveries) order by id""",reasons).fetchall()
    if not rows or not traces.refresh():
        return
    from .formula_only import digest
    for n,reason in rows:
        if not active():
            return
        folder=output/'batches'/f'{n:06d}'
        if any((folder/p).exists() for p in ('attempt.json','entry-retry','response.txt','records.jsonl')) or traces.events.get(f'formula-display-{n}'):
            continue
        status=read(folder/'status.json');last=status.get('last') or {}
        packet=read(folder/'packet.json')
        if (status.get('state')!='blocked' or status.get('reason')!=reason or not status.get('pid')
                or status['pid']!=last.get('pid') or last.get('state') not in ('checking_account','temporary_ui','checking_model')
                or packet.get('batch')!=n or not packet.get('sha256') or packet['sha256']!=digest(folder/'batch.zip')):
            continue
        evidence=dict(batch=n,status=status,packet=packet,upload_events=[])
        old=read(folder/'preflight-recovery.json')
        if old and old!=evidence:
            continue
        write(folder/'preflight-recovery.json',evidence)
        with db:
            if db.execute("update batches set state='queued',reason=null where id=? and state='held' and reason=?",(n,reason)).rowcount:
                db.execute('insert into preflight_recoveries values(?,?)',(n,time.time()))
