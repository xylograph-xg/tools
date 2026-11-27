"""Read archived pre-transfer evidence for App admission."""
import json
import os
from core.api import control__read_record as read

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


def empty_formula_home(check):
    return (check.get('inspection_complete') and check.get('account_ready') and check.get('composer_available')
            and check.get('url') in ('https://chatgpt.com/', 'https://chatgpt.com/?temporary-chat=true')
            and not (check.get('draft') or '').strip()
            and not any(check.get(key) for key in ('attachments','uploading','streaming','user_texts','answer_texts',
                        'answer_element_count','errors','quota','login','verification','account_ui_blocked')))


def historical_slot_receipt(control,output,batch,state,tid,receipt,original_release=None):
    """A prior assignment ceases to reserve this tab only after verifiable local archiving."""
    from .formula_only import digest
    folder=output/'batches'/f'{batch:06d}'
    job=f'formula-display-{batch}'
    packet=read(folder/'packet.json')
    if (state not in ('held','review') or receipt.get('window_target')!=tid or receipt.get('job_id')!=job
            or receipt.get('temporary') is not True or packet.get('batch')!=batch or not packet.get('sha256')
            or packet['sha256']!=receipt.get('zip_sha256') or not (folder/'batch.zip').is_file()
            or digest(folder/'batch.zip')!=packet['sha256']):
        return False
    if state!='held' or receipt.get('state')!='upload_preparation' or any(
            key in receipt for key in ('at','url','click_settings')):
        return False
    record=read(original_release or release_path(folder))
    evidence=record.get('evidence') or {}
    before=evidence.get('pool_before') or {}
    page=record.get('page') or {}
    status=read(folder/'status.json')
    return (evidence.get('job')==job and evidence.get('target')==tid and evidence.get('attempt')==receipt
            and evidence.get('packet')==packet and evidence.get('status')==status and status.get('state')=='blocked'
            and (status.get('last') or {}).get('target')==tid and before.get('kind')=='formula_only'
            and before.get('active_paper_id')==job and before.get('state')=='busy' and record.get('owner')
            and page.get('target_id')==tid and empty_formula_home(page))
