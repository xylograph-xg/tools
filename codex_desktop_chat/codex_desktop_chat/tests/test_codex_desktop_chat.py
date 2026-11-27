"""Safety contract tests: no real UI, external prompts, or production data."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from codex_desktop_chat import ChatGPTDesktop,DesktopChatError,create_session
from codex_desktop_chat.core import _answer,_sha,_busy,_complete,_find
from codex_desktop_chat.state import ReceiptStore

def node(i,role,value='',title='',parent=0,**kw):
    return {'id':i,'parent':parent,'role':role,'title':title,'description':'','value':value,
            'enabled':True,'x':0,'y':i*20,'width':200,'height':18,**kw}

def answer_tree(prompt='wire',answer='ANSWER',complete=True,busy=False):
    n=[node(0,'AXWindow',parent=-1),node(1,'AXStaticText',prompt),
       node(2,'AXHeading',title='ChatGPT 说：'),node(3,'AXStaticText','ChatGPT 说：',parent=2),
       node(4,'AXGroup'),node(5,'AXStaticText',answer,parent=4),node(6,'AXGroup'),
       node(7,'AXButton',title='复制',parent=6)]
    if complete:n.append(node(8,'AXStaticText','回答已完成'))
    if busy:n.append(node(9,'AXButton',title='停止'))
    return {'pid':10,'window_id':20,'nodes':n}

class ReadBackend:
    def __init__(self,snapshot):self.window_id=20;self.tree=snapshot;self.mutations=[]
    def snapshot(self):return self.tree
    def press(self,*a,**kw):self.mutations.append((a,kw));raise AssertionError('Collection must never submit')

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)

    def session(self,tree,stage='sent'):
        backend=ReadBackend(tree)
        c=ChatGPTDesktop(new_chat=False,window_id=20,state_dir=self.folder,backend=backend,poll_interval=1)
        c.pid=10;c._entered=True
        r={'schema_version':1,'id':'a'*32,'window_id':20,'pid':10,'stage':stage,'wire_prompt':'wire','wire_sha256':_sha('wire')}
        c.store.save(r);c._pending=r['id']
        return c,r,backend

    def test_exact_unique_prompt_required(self):
        with self.assertRaises(DesktopChatError):_answer(answer_tree('different'),'wire')
        tree=answer_tree();tree['nodes'].append(node(12,'AXStaticText','wire'))
        with self.assertRaises(DesktopChatError):_answer(tree,'wire')

    def test_long_full_answer_not_truncated(self):
        text='中文 20%\n'+('αβγ x=1; '*100)
        self.assertEqual(_answer(answer_tree(answer=text),'wire'),text)

    def test_inline_fragment_order_is_preserved(self):
        tree=answer_tree(answer='{"a":');tree['nodes'].insert(6,node(10,'AXStaticText','false}',parent=4,y=100))
        self.assertEqual(_answer(tree,'wire'),'{"a":false}')

    def test_completion_cannot_be_inferred_from_disabled_stop(self):
        tree=answer_tree(complete=False,busy=True);tree['nodes'][-1]['enabled']=False
        self.assertTrue(_busy(tree));self.assertFalse(_complete(tree))

    def test_completed_result_archived_before_return(self):
        c,r,b=self.session(answer_tree(answer='{"ok":true}'))
        with patch('codex_desktop_chat.core.time.sleep'):
            answer=c.collect(r,answer_timeout=2)
        saved=c.store.load(r['id'])
        self.assertEqual(saved['stage'],'completed');self.assertEqual(saved['answer_sha256'],_sha(answer))
        self.assertFalse(saved['scientific_verified']);self.assertEqual(b.mutations,[])
        self.assertIsNone(c._pending)

    def test_unknown_receipt_can_only_collect(self):
        c,r,b=self.session(answer_tree(),stage='unknown')
        with patch('codex_desktop_chat.core.time.sleep'):
            self.assertEqual(c.collect(r,answer_timeout=2),'ANSWER')
        self.assertEqual(b.mutations,[])

    def test_timeout_preserves_pending_and_never_returns_partial(self):
        c,r,b=self.session(answer_tree(answer='partial',complete=False))
        with self.assertRaises(DesktopChatError) as raised:c.collect(r,answer_timeout=.01)
        self.assertEqual(raised.exception.code,'answer_timeout');self.assertTrue(raised.exception.may_have_sent)
        self.assertEqual(c.store.load(r['id'])['stage'],'sent');self.assertEqual(c._pending,r['id'])
        self.assertEqual(b.mutations,[])

    def test_other_window_or_changed_input_receipt_rejected(self):
        c,r,_=self.session(answer_tree());r['window_id']=21;c.store.save(r)
        with self.assertRaises(DesktopChatError):c.collect(r,answer_timeout=1)
        r['window_id']=20;r['wire_prompt']='changed';c.store.save(r)
        with self.assertRaises(DesktopChatError):c.collect(r,answer_timeout=1)

    def test_existing_draft_not_overwritten(self):
        c,r,b=self.session(answer_tree())
        with self.assertRaises(DesktopChatError):
            c._empty_draft({'nodes':[node(1,'AXTextArea','private user draft',title='询问 ChatGPT')]})
        self.assertEqual(b.mutations,[])

    def test_history_named_new_chat_not_navigation(self):
        tree={'nodes':[node(1,'AXButton',title='新聊天'),node(2,'AXButton',title='新聊天',description='新聊天')]}
        self.assertEqual(_find(tree,'AXButton','新聊天')['id'],1)

    def test_invalid_attachments_rejected_before_ui(self):
        c,r,b=self.session(answer_tree())
        with self.assertRaises((FileNotFoundError,ValueError)):c.submit('prompt',files=['/private/nonexistent-test-source.pdf'])
        self.assertEqual(b.mutations,[])

    def test_pending_request_cannot_submit_again(self):
        c,r,b=self.session(answer_tree());c.foreground=True
        with self.assertRaises(DesktopChatError) as e:c.submit('retry')
        self.assertEqual(e.exception.code,'pending_request');self.assertEqual(b.mutations,[])

    def test_corrupted_receipts_block(self):
        store=ReceiptStore(self.folder);(self.folder/('b'*32+'.json')).write_text('{broken')
        with self.assertRaises(DesktopChatError):store.pending()

    def test_saved_answer_hash_is_checked(self):
        c,r,_=self.session(answer_tree(),stage='completed');r.update(answer='tampered',answer_sha256=_sha('original'));c.store.save(r)
        with self.assertRaises(DesktopChatError):c.collect(r)

    def test_multiple_receipts_have_separate_window_ids(self):
        store=ReceiptStore(self.folder)
        for key,wid in [('a',20),('b',21)]:
            store.save({'schema_version':1,'id':key*32,'window_id':wid,'stage':'sent'})
        self.assertEqual({r['window_id'] for r in store.pending()},{20,21})

    def test_foreground_authorization_and_provider_are_explicit(self):
        with self.assertRaises(ValueError):create_session('qwen',state_dir=self.folder)
        c=ChatGPTDesktop(state_dir=self.folder)
        with self.assertRaises(DesktopChatError) as e:c.__enter__()
        self.assertEqual(e.exception.code,'foreground_required')

if __name__=='__main__':unittest.main()
