"""Audit regressions use synthetic inputs only; never operate the App."""
import shutil
import stat
import tempfile
import unittest
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from codex_desktop_chat.bundles import prepare_upload_bundle, verify_bundle
from codex_desktop_chat.core import _answer, _complete
from codex_desktop_chat.errors import DesktopChatError
from codex_desktop_chat.tests import test_codex_desktop_chat as fixtures
answer_tree, node = fixtures.answer_tree, fixtures.node

class TurnTests(unittest.TestCase):
    setUp = fixtures.SafetyTests.setUp
    session = fixtures.SafetyTests.session
    def test_later_turn_never_collected_for_original(self):
        tree=answer_tree(answer='ORIGINAL')
        tree['nodes'] += [node(20,'AXHeading',title='你说：'),node(21,'AXStaticText','later'),
                          node(22,'AXHeading',title='ChatGPT 说：'),node(23,'AXGroup'),
                          node(24,'AXStaticText','UNRELATED',parent=23),node(25,'AXStaticText','回答已完成')]
        c,r,b=self.session(tree)
        with patch('codex_desktop_chat.core.time.sleep'):
            self.assertEqual(c.collect(r,answer_timeout=1),'ORIGINAL')
        self.assertEqual(b.mutations,[])

    def test_ambiguous_assistant_turns_refused(self):
        tree=answer_tree();tree['nodes'].append(node(20,'AXHeading',title='ChatGPT said:'))
        with self.assertRaises(DesktopChatError):_answer(tree,'wire')

    def test_historical_completion_does_not_complete_target(self):
        tree=answer_tree(complete=False)
        tree['nodes'].insert(1,node(30,'AXStaticText','回答已完成'))
        self.assertFalse(_complete(tree,'wire'))
        c,r,b=self.session(tree)
        with self.assertRaises(DesktopChatError) as e:c.collect(r,answer_timeout=.01)
        self.assertEqual(e.exception.code,'answer_timeout')
        self.assertEqual(c.store.load(r['id'])['stage'],'sent')

    def test_delayed_anchor_only_waits_and_collects(self):
        c,r,b=self.session(answer_tree(),stage='unknown')
        with patch.object(b,'snapshot',side_effect=[{'pid':10,'window_id':20,'nodes':[]},answer_tree(),answer_tree()]), patch('codex_desktop_chat.core.time.sleep'):
            self.assertEqual(c.collect(r,answer_timeout=1),'ANSWER')
        self.assertEqual(b.mutations,[])

    def test_absent_anchor_times_out_without_resend(self):
        c,r,b=self.session({'pid':10,'window_id':20,'nodes':[]},stage='unknown')
        with self.assertRaises(DesktopChatError) as e:c.collect(r,answer_timeout=.01)
        self.assertEqual(e.exception.code,'answer_timeout')
        self.assertEqual(c.store.load(r['id'])['stage'],'unknown')
        self.assertEqual(b.mutations,[])

    def test_code_text_area_is_not_silently_dropped(self):
        tree=answer_tree(answer='Code:')
        tree['nodes'].insert(6,node(10,'AXTextArea','print(123)\nprint(456)',parent=4,y=150))
        self.assertEqual(_answer(tree,'wire'),'Code:\nprint(123)\nprint(456)')

    def test_start_and_settings_require_permission_before_mutation(self):
        c,r,b=self.session(answer_tree());c._pending=None
        for operation in (c.start_new_chat,c.verify_settings):
            with self.assertRaises(DesktopChatError) as e:operation()
            self.assertEqual(e.exception.code,'foreground_required')
        self.assertEqual(b.mutations,[])

    def test_terminal_receipt_cannot_return_to_submitting(self):
        c,r,_=self.session(answer_tree(),stage='completed')
        r['stage']='submitting'
        with self.assertRaises(DesktopChatError):c.store.save(r)
        self.assertEqual(c.store.load(r['id'])['stage'],'completed')

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.out=self.root/'out'
        self.source=self.root/'paper.txt';self.source.write_text('AUTHENTIC')
    def pack(self):return prepare_upload_bundle([self.source],bundle_dir=self.out)
    def test_self_consistent_wrong_source_cache_is_rejected(self):
        original=self.pack();self.source.write_text('REPLACED')
        other=self.pack();shutil.copyfile(other['zip_path'],original['zip_path'])
        self.source.write_text('AUTHENTIC')
        with self.assertRaises(DesktopChatError) as e:self.pack()
        self.assertEqual(e.exception.code,'bundle_identity_mismatch')
    def test_wrong_prepacked_cache_is_rejected(self):
        source=self.root/'source.zip'
        with zipfile.ZipFile(source,'w') as z:z.writestr('a','authentic')
        first=prepare_upload_bundle([source],bundle_dir=self.out)
        with zipfile.ZipFile(first['zip_path'],'w') as z:z.writestr('a','wrong')
        with self.assertRaises(DesktopChatError):prepare_upload_bundle([source],bundle_dir=self.out)
    def test_symlink_zip_rejected(self):
        path=self.root/'link.zip';info=zipfile.ZipInfo('link');info.create_system=3
        info.external_attr=(stat.S_IFLNK|0o777)<<16
        with zipfile.ZipFile(path,'w') as z:z.writestr(info,'../../outside')
        with self.assertRaises(DesktopChatError):verify_bundle(path)
    def test_concurrent_publication_matches_source(self):
        with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda _:self.pack(),range(16)))
        self.assertEqual(len({r['zip_sha256'] for r in results}),1)
        self.assertEqual(len(list(self.out.glob('*.zip'))),1)
        self.assertEqual(list(self.out.glob('.packing-*')),[])
