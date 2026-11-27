import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from oled_formulas import attachment_gate as gate


class AttachmentBackoffTests(unittest.TestCase):
    def test_two_distinct_slots_and_one_quota_notice(self):
        event = dict(batch=1,target='a',at=100,reason=gate.ENTRY_FAILURE)
        first=gate.record_failure({},event)
        self.assertNotIn('mode',gate.record_failure(first,dict(event,batch=2)))
        self.assertNotIn('mode',gate.record_failure(first,dict(event,batch=2,target='b',at=401)))
        blocked=gate.record_failure(first,dict(event,batch=2,target='b',at=110))
        self.assertEqual((blocked['mode'],blocked['next_check']),('cooldown',1010))
        self.assertEqual(gate.record_failure({},dict(event,reason='附件额度限制：上传文件置灰'))['mode'],'cooldown')

    def test_native_menu_disabled_overrides_hidden_document_input(self):
        from unittest.mock import MagicMock,patch
        page=MagicMock()
        button=page.locator.return_value
        button.count.return_value=1
        button.get_attribute.side_effect=['false','true','true']
        with patch('browser.api.web_card_transport__attachment_entry',side_effect=[
                dict(ready=True,reason='document_input'),dict(ready=False,reason='disabled')]):
            self.assertEqual(gate.probe_menu(page,lambda:None),dict(ready=False,reason='disabled'))
        self.assertEqual(button.evaluate.call_count,2)

    def test_native_probe_requires_enabled_menu_item_and_zip_input(self):
        from unittest.mock import MagicMock,patch
        for enabled in (True,False):
            page=MagicMock()
            button=page.locator.return_value
            button.count.return_value=1
            button.get_attribute.return_value='true'
            option=MagicMock()
            option.is_visible.return_value=True
            option.is_enabled.return_value=enabled
            option.get_attribute.return_value=None
            option.inner_text.return_value='添加照片和文件'
            page.get_by_role.return_value.all.return_value=[option]
            with patch('browser.api.web_card_transport__attachment_entry',return_value=dict(ready=True,reason='document_input')):
                self.assertEqual(gate.probe_menu(page,lambda:None)['ready'],enabled)
            button.evaluate.assert_not_called()

    def test_native_document_input_without_menuitem_role(self):
        from unittest.mock import MagicMock,patch
        ready=dict(ready=True,reason='document_input')
        quota=dict(ready=False,reason='quota',notice='upload limit reached')
        for disabled, final, expected in [(False,ready,'verified_document_input'),(True,ready,'disabled'),(False,quota,'quota')]:
            page=MagicMock()
            button=page.locator.return_value
            button.count.return_value=1
            button.get_attribute.return_value='true'
            button.evaluate.return_value=dict(disabled=disabled,visible_upload_actions=0)
            page.get_by_role.return_value.all.return_value=[]
            with patch('browser.api.web_card_transport__attachment_entry',side_effect=[ready,ready,final]):
                result=gate.probe_menu(page,lambda:None)
            self.assertEqual(result['reason'],expected)
            self.assertEqual(result['ready'],expected=='verified_document_input')

    def test_preflight_recovery_requires_no_transfer_and_is_spent_once(self):
        from unittest.mock import Mock
        from oled_formulas import entry_retry
        from oled_formulas.formula_only import digest
        reason='页面缺少 Chat 模式控件，且不是已有会话'
        with tempfile.TemporaryDirectory() as tmp,sqlite3.connect(':memory:') as db:
            out=Path(tmp)
            db.execute('create table batches(id,state,reason)')
            for n in (1,2,3):
                db.execute("insert into batches values(?,'held',?)",(n,reason))
                folder=out/'batches'/f'{n:06d}';folder.mkdir(parents=True)
                (folder/'batch.zip').write_bytes(b'frozen')
                (folder/'packet.json').write_text(json.dumps(dict(batch=n,sha256=digest(folder/'batch.zip'))))
                (folder/'status.json').write_text(json.dumps(dict(state='blocked',pid=4,reason=reason,last=dict(pid=4,state='temporary_ui'))))
            (out/'batches/000003/attempt.json').write_text('{}')
            traces=Mock(events={'formula-display-2':[{}]});traces.refresh.return_value=True
            entry_retry.recover_preflight(db,out,traces,lambda:True)
            self.assertEqual(db.execute('select state from batches order by id').fetchall(),[('queued',),('held',),('held',)])
            db.execute("update batches set state='held',reason=? where id=1",(reason,))
            entry_retry.recover_preflight(db,out,traces,lambda:True)
            self.assertEqual(db.execute('select state from batches where id=1').fetchone(),('held',))

    def test_restart_and_bound_success(self):
        with tempfile.TemporaryDirectory() as tmp, sqlite3.connect(':memory:') as db:
            d=Path(tmp)
            db.execute('create table batches(id,state)')
            now=time.time()
            for n in (1,2):
                target=f'slot{n}'
                db.execute("insert into batches values(?,'held')",(n,))
                folder=d/'batches'/f'{n:06d}'
                folder.mkdir(parents=True)
                attempt=dict(state='upload_preparation',job_id=f'formula-display-{n}',window_target=target)
                (folder/'attempt.json').write_text(json.dumps(attempt))
                (folder/'status.json').write_text(json.dumps(dict(state='blocked',time=now-10+n,reason=gate.ENTRY_FAILURE,last=dict(target=target))))
            state=gate.load_gate(d,db)
            self.assertEqual(state['mode'],'cooldown')
            self.assertEqual(gate.load_gate(d,db),state)
            trial=dict(batch=2,target=target,at=now)
            receipt=dict(attempt,state='send_intent',at=now+5,temporary=True,zip_sha256='zip')
            self.assertTrue(gate.held_intent(db,receipt,trial))
            self.assertFalse(gate.held_intent(db,dict(receipt,window_target='other'),trial))
            self.assertFalse(gate.trial_success(receipt,trial))
            self.assertFalse(gate.trial_success(dict(receipt,state='submitted',window_target='other'),trial))
            self.assertTrue(gate.trial_success(dict(receipt,state='submitted'),trial))

    def test_recovery_requires_transfer_and_archive_proof_and_is_spent_once(self):
        import hashlib
        from unittest.mock import patch
        from core.api import services__atomic_json as write
        from oled_formulas import entry_retry

        with tempfile.TemporaryDirectory() as tmp, sqlite3.connect(':memory:') as db:
            root = Path(tmp)
            folder = root/'batches/000001'
            folder.mkdir(parents=True)
            bundle = folder/'batch.zip'
            bundle.write_bytes(b'frozen')
            sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
            packet = dict(batch=1,sha256=sha)
            attempt = dict(job_id='formula-display-1',window_target='a',state='upload_preparation',
                           temporary=True,zip_sha256=sha)
            status = dict(state='blocked',time=1,pid=12,last=dict(target='a'),reason=gate.ENTRY_FAILURE)
            write(folder/'attempt.json',attempt)
            write(folder/'status.json',status)
            write(folder/'packet.json',packet)
            release = dict(owner=12,page=dict(target_id='a',url='https://chatgpt.com/',inspection_complete=True,
                composer_available=True,account_ready=True),evidence=dict(job=attempt['job_id'],target='a',attempt=attempt,
                status=status,packet=packet,pool_before=dict(kind='formula_only',state='busy',active_paper_id=attempt['job_id'])))
            write(folder/'unsent-slot-release.json',release)
            binding = dict(lane='formula_only',job_id=attempt['job_id'],target_id='a',owner_pid=12,
                           upload_attempt_id='unique',zip_sha256=sha)
            start = dict(binding,event='upload_started')
            end = dict(binding,event='upload_finished',result='failed',failure_kind='entry_not_ready',attachment={},
                       settle={},zip_identity_mismatch=False,stages=[dict(stage='upload_ready_gate',outcome='failed')])
            tracefile = root/'trace'
            tracefile.write_text(json.dumps(start)+'\n')
            traces = entry_retry.EntryTraces(tracefile)
            db.execute('create table batches(id integer primary key,state,reason)')
            db.execute('create table entry_retries(batch integer primary key, admitted_at real)')
            db.execute("insert into batches values (1,'held',?)",(gate.ENTRY_FAILURE,))
            recovery = dict(mode='ready',last_success=dict(batch=2,target='b',at=1800))
            def resume():
                return entry_retry.resume_one(db,root,{},recovery,lambda:True,2000,traces)
            trial = dict(state='send_intent',temporary=True,job_id='formula-display-2',window_target='b',zip_sha256='trial',at=1801)
            trialfile = root/'batches/000002/attempt.json'
            write(trialfile,trial)
            self.assertIsNone(resume())
            write(trialfile,dict(trial,state='submitted'))
            self.assertIsNone(resume())
            with tracefile.open('a') as stream:
                stream.write(json.dumps(end)+'\n')
            write(folder/'attempt.json',dict(attempt,state='send_intent'))
            self.assertIsNone(resume())
            write(folder/'attempt.json',attempt)
            bundle.write_bytes(b'changed')
            self.assertIsNone(resume())
            bundle.write_bytes(b'frozen')
            with patch.object(entry_retry.os,'rename',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    resume()
            self.assertEqual(resume(),1)
            self.assertEqual(json.loads((folder/'entry-retry/attempt.json').read_bytes()),attempt)
            self.assertEqual(json.loads((folder/'unsent-slot-release.json').read_bytes()),release)
            self.assertEqual(entry_retry.release_path(folder).name,'retry-unsent-slot-release.json')
            self.assertEqual(db.execute('select state from batches').fetchone(),('queued',))
            write(folder/'attempt.json',attempt)
            db.execute("update batches set state='held',reason=?",(gate.ENTRY_FAILURE,))
            self.assertIsNone(resume())
            self.assertEqual(db.execute('select count(*) from entry_retries').fetchone(),(1,))
