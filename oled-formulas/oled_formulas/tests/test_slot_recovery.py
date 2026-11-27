import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from oled_formulas.slot_recovery import own_draft, stopped_text, upload_pair


class SlotRecoveryTests(unittest.TestCase):
    def test_clean_only_matching_unsent_content(self):
        receipt=dict(prompt='actual prompt',zip_sha256='abc')
        page=dict(inspection_complete=True,account_authenticated=True,composer_available=True,streaming=False,
                  uploading=False,url='https://chatgpt.com/?temporary-chat=true',draft='actual prompt',
                  attachment_names=['abc.zip'],errors=['上传未成功'])
        self.assertTrue(own_draft(page,receipt))
        self.assertTrue(own_draft(dict(page,draft='actualprompt'),dict(receipt,prompt='actual\nprompt')))
        self.assertFalse(own_draft(dict(page,draft='actual other prompt'),receipt))
        for change in [dict(draft='new input'), dict(attachment_names=['abc.zip','other.zip']),dict(streaming=True),
                       dict(user_texts=['submitted']),dict(verification=True),dict(uploading=True),dict(quota=True)]:
            self.assertFalse(own_draft(dict(page,**change),receipt))

    def test_finished_upload_identity_must_match_before_cleanup(self):
        receipt=dict(job_id='formula-display-1',window_target='t',zip_sha256='abc')
        fields=dict(lane='formula_only',job_id=receipt['job_id'],owner_pid=777,target_id='t',zip_sha256='abc',
                    zip_name='abc.zip',upload_attempt_id='first')
        start=dict(fields,event='upload_started')
        end=dict(fields,event='upload_finished',result='failed',attachment=dict(confirmed_new=True,expected='abc.zip'))
        self.assertTrue(upload_pair([start,end],receipt,dict(pid=777)))
        self.assertFalse(upload_pair([start,dict(end,upload_attempt_id='other')],receipt,dict(pid=777)))
        self.assertFalse(upload_pair([start,end,start],receipt,dict(pid=777)))
        self.assertFalse(upload_pair([start,end],receipt,dict(pid=7)))

    def test_unavailable_release_verifies_original_and_returned_evidence(self):
        from unittest.mock import patch
        from oled_formulas import unavailable_slots as slots
        from oled_formulas.formula_only import digest
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);journal=folder/'slot-recovery';journal.mkdir()
            self.assertFalse(slots.released(folder,'other','tid'))
            (journal/'returned-home.html').write_text('original blank')
            (journal/'returned-home.png').write_bytes(b'empty page')
            first=dict(at=1,identity={'url':'home'})
            final=dict(checked_at=31,url='home',target_id='tid')
            rec=dict(job='j',target='tid',authorization={'receipt':'pinned'},requeue_allowed=False,first=first,final=final,
                     html_sha256=digest(journal/'returned-home.html'),png_sha256=digest(journal/'returned-home.png'))
            (journal/'released.json').write_text(json.dumps(rec))
            with patch.object(slots,'authorized',return_value=rec['authorization']):
                self.assertTrue(slots.released(folder,'j','tid'))
                self.assertFalse(slots.released(folder,'j','another'))
                (journal/'returned-home.html').write_text('changed')
                self.assertFalse(slots.released(folder,'j','tid'))

    def test_stopped_text_requires_exact_raw_and_every_frozen_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            rows=[dict(crop_id='P0001',paper_id='a',pdf_page=1),dict(crop_id='P0002',paper_id='a',pdf_page=2)]
            rec=dict(job_id='formula-display-1')
            with zipfile.ZipFile(folder/'batch.zip','w') as z:z.writestr('manifest.json',json.dumps(rows))
            def check(records):
                raw='\n'.join(json.dumps(r) for r in records)
                (folder/'stopped-answer.json').write_text(json.dumps(dict(receipt=rec,text=[raw])))
                view=dict(terminal_stopped=True,answer_texts=[raw])
                self.assertIsNone(stopped_text(folder,rec,dict(view,answer_texts=['different text'])))
                return stopped_text(folder,rec,view)
            good=[dict(r,kind='non_equation') for r in rows]
            self.assertTrue(check(good))
            self.assertIsNone(check(good[:1]))
            self.assertIsNone(check([good[0],dict(rows[1],kind='equation',latex='x')]))
