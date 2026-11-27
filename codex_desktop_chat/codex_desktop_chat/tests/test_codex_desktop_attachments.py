"""Meaningful attachment guards and full staged submission without external traffic."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from codex_desktop_chat import ChatGPTDesktop,DesktopChatError
from codex_desktop_chat.attachments import validate_files,snapshot_files,verify_snapshots,upload_evidence,formal_attachment_evidence,channel_issue
from codex_desktop_chat.tests.test_codex_desktop_chat import node

class FakeBackend:
    def __init__(self, failure=False):
        self.window_id=20;self.draft='询问 ChatGPT\n';self.files=[];self.progress=0;self.failure=failure;self.sent=False;self.calls=[]
    def snapshot(self):
        ns=[node(0,'AXWindow',parent=-1),node(1,'AXGroup')]
        ns+=[node(2,'AXTextArea',self.draft,title='询问 ChatGPT',parent=1)]
        if not self.sent:
            for name in self.files: ns.append(node(len(ns),'AXButton',title='移除“'+name+'”',parent=1))
            if self.progress:
                ns.append(node(len(ns),'AXProgressIndicator',title='正在上传 '+self.files[-1],parent=1));self.progress-=1
            if self.failure and self.files: ns.append(node(len(ns),'AXStaticText','上传未成功',parent=1))
        ns.append(node(len(ns),'AXButton',title='发送',parent=1))
        if self.sent:
            g=len(ns);ns.append(node(g,'AXGroup'))
            ns.append(node(len(ns),'AXStaticText',self.draft,parent=g))
            for name in self.files:ns.append(node(len(ns),'AXStaticText',name,parent=g))
        return {'pid':10,'window_id':20,'nodes':ns}
    def type_text(self,text,**kw):self.draft=text;self.calls.append('type')
    def press(self,query,**kw):
        self.calls.append(('press',kw));self.sent=True
        if kw.get('attachment_names')!=self.files:raise AssertionError('Native send must receive exact attachment guard')
    def upload(self,path):self.files.append(Path(path).name);self.progress=1;self.calls.append(('upload',str(path)))

class AttachmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.folder=Path(self.temp.name)
        self.file=self.folder/'source.txt';self.file.write_text('unique synthetic content')
    def composer(self,names=('file.pdf',),progress=False,error=False,enabled=True):
        b=FakeBackend(failure=error);b.files=list(names);b.progress=int(progress)
        s=b.snapshot();s['nodes'][-1]['enabled']=enabled;return s
    def test_absolute_existing_regular_unique_files(self):
        for files in ('/bad', ['relative.txt'],[self.folder],[self.file,self.file]):
            with self.assertRaises((ValueError,FileNotFoundError)):validate_files(files)
        self.assertEqual(validate_files([self.file]),[self.file.resolve()])
    def test_empty_and_oversized_rejected(self):
        p=self.folder/'empty';p.touch()
        with self.assertRaises(ValueError):validate_files([p])
        with self.file.open('wb') as f:f.truncate(64*1024*1024+1)
        with self.assertRaises(ValueError):validate_files([self.file])
    def test_frozen_snapshot_and_mutation_guard(self):
        files=snapshot_files([self.file],self.folder/'inputs');self.file.write_text('source changes after capture')
        verify_snapshots(files)
        Path(files[0]['snapshot_path']).write_text('changed snapshot')
        with self.assertRaises(DesktopChatError):verify_snapshots(files)
    def test_ready_send_button_cannot_override_progress(self):
        e=upload_evidence(self.composer(progress=True),['file.pdf'])
        self.assertTrue(e['uploading']);self.assertFalse(e['ready'])
    def test_foreign_missing_duplicate_disabled_not_ready(self):
        with self.assertRaises(DesktopChatError):upload_evidence(self.composer(names=['foreign.pdf']),['file.pdf'])
        with self.assertRaises(DesktopChatError):upload_evidence(self.composer(names=['file.pdf','file.pdf']),['file.pdf'])
        self.assertFalse(upload_evidence(self.composer(names=[]),['file.pdf'])['ready'])
        self.assertFalse(upload_evidence(self.composer(enabled=False),['file.pdf'])['ready'])
    def test_failed_upload_never_ready(self):
        with self.assertRaises(DesktopChatError) as e:upload_evidence(self.composer(error=True),['file.pdf'])
        self.assertEqual(e.exception.code,'attachment_upload_failed')
    def test_sidebar_old_failures_do_not_block_composer(self):
        s=self.composer();s['nodes'].append(node(50,'AXStaticText','旧聊天上传失败',parent=0))
        self.assertTrue(upload_evidence(s,['file.pdf'])['ready'])
    def test_formal_receipt_does_not_use_composer_as_proof(self):
        s=self.composer();s['nodes'].append(node(50,'AXStaticText','wire',parent=0))
        self.assertFalse(formal_attachment_evidence(s,'wire',['file.pdf']))
    def session(self,b):
        c=ChatGPTDesktop(new_chat=False,window_id=20,foreground=True,state_dir=self.folder/'receipts',backend=b,poll_interval=1,bundle_dir=self.folder/'zips')
        c._entered=True;c.pid=10;c._verify_settings_locked=lambda:{'model':'GPT-6','thinking':'High'};return c
    def test_complete_staged_upload_then_exact_guarded_send(self):
        b=FakeBackend();c=self.session(b)
        with patch('codex_desktop_chat.core.choose_file',side_effect=lambda backend,path,pid:backend.upload(path)),patch('codex_desktop_chat.core.time.sleep'):
            r=c.submit('read attached token',files=[self.file],upload_timeout=5)
        self.assertEqual(r['stage'],'sent');self.assertTrue(r['formal_attachments_verified']);self.assertTrue(r['files'][0]['upload_ready'])
        import zipfile
        with zipfile.ZipFile(r['files'][0]['snapshot_path']) as z:self.assertEqual(z.read('source.txt').decode(),self.file.read_text())
        self.assertTrue(b.sent);self.assertEqual(c.store.load(r['id'])['files'],r['files'])
    def test_failed_upload_archived_no_send_no_retry(self):
        b=FakeBackend(failure=True);c=self.session(b)
        with patch('codex_desktop_chat.core.choose_file',side_effect=lambda backend,path,pid:backend.upload(path)):
            with self.assertRaises(DesktopChatError) as e:c.submit('read',files=[self.file],upload_timeout=5)
        self.assertFalse(b.sent);self.assertFalse(e.exception.may_have_sent)
        saved=c.store.load(e.exception.receipt_id)
        self.assertEqual(saved['stage'],'not_sent');self.assertEqual(saved['error_code'],'attachment_upload_failed')
        self.assertEqual(sum(isinstance(x,tuple) and x[0]=='upload' for x in b.calls),1)
    def test_two_files_have_separate_snapshots_and_exact_send_guard(self):
        second=self.folder/'other.txt';second.write_text('second unique content')
        b=FakeBackend();c=self.session(b)
        with patch('codex_desktop_chat.core.choose_file',side_effect=lambda backend,path,pid:backend.upload(path)),patch('codex_desktop_chat.core.time.sleep'):
            r=c.submit('read both',files=[self.file,second],upload_timeout=5)
        self.assertEqual(len(b.files),1);self.assertEqual(len(r['files']),1)
        import zipfile
        with zipfile.ZipFile(r['files'][0]['snapshot_path']) as z:
            self.assertEqual(z.read('source.txt').decode(),self.file.read_text());self.assertEqual(z.read('other.txt').decode(),second.read_text())
    def test_anonymous_image_requires_bound_count_and_image_evidence(self):
        s={'nodes':[node(0,'AXWindow',parent=-1),node(1,'AXGroup'),node(2,'AXHeading',title='你说：',parent=1),node(3,'AXButton',title='用户附件',parent=1),node(4,'AXStaticText','wire',parent=1),node(5,'AXHeading',title='ChatGPT 说：',parent=1),node(6,'AXStaticText','missing.pdf',parent=1)]}
        self.assertFalse(formal_attachment_evidence(s,'wire',['A.png']))
        self.assertTrue(formal_attachment_evidence(s,'wire',['A.png'],['A.png']))
        self.assertFalse(formal_attachment_evidence(s,'wire',['A.png','B.png'],['A.png','B.png']))
        self.assertFalse(formal_attachment_evidence(s,'wire',['missing.pdf']))

    def test_observed_quota_blocks_new_files_without_resending(self):
        b=FakeBackend();c=self.session(b)
        from codex_desktop_chat.state import atomic_json
        atomic_json(c.store.folder/'channel'/'issue.json',{'blocked':True,'code':'attachment_quota','message':'你目前已用完附件额度。','pid':10,'window_id':20})
        with self.assertRaises(DesktopChatError) as e:c.submit('new',files=[self.file])
        self.assertEqual(e.exception.code,'attachment_quota');self.assertEqual(b.calls,[])
    def test_native_quota_is_an_observation_not_a_reset_guarantee(self):
        s=self.composer();s.update(pid=10,window_id=20)
        s['nodes'].append(node(100,'AXStaticText','你目前已用完附件额度。或在 15:15 后重试。'))
        issue=channel_issue(s)
        self.assertEqual(issue['code'],'attachment_quota');self.assertNotIn('resets_at',issue)
    def test_corrupt_channel_state_blocks_attachments(self):
        b=FakeBackend();c=self.session(b);p=c.store.folder/'channel'/'issue.json';p.parent.mkdir();p.write_text('{')
        with self.assertRaises(DesktopChatError) as e:c.submit('new',files=[self.file])
        self.assertEqual(e.exception.code,'channel_state_corrupt');self.assertEqual(b.calls,[])

    def test_existing_attachments_protected_before_typing(self):
        b=FakeBackend();b.files=['private.pdf'];c=self.session(b)
        with self.assertRaises(DesktopChatError) as e:c.submit('prompt',files=[self.file])
        self.assertEqual(e.exception.code,'attachment_protected');self.assertEqual(b.calls,[])

if __name__=='__main__':unittest.main()
