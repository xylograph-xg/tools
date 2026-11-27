import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from oled_formulas.formula_only import CONTROLS, enabled, check_answer

class FormulaTests(unittest.TestCase):
    def test_dispatch_requires_fresh_eligible_unassigned_tab(self):
        from oled_formulas.formula_dispatch import available
        ids = ('busy','cooling','reserved','stale','streaming','draft','free','saved','left')
        windows = {tid:dict(state='ready_blank') for tid in ids}
        windows['busy']['state'] = 'busy'
        windows['saved'].update(state='ready',kind='formula_only',conversation_url='https://chatgpt.com/c/saved')
        windows['left']=dict(windows['saved'])
        checks = [dict(target_id=tid,inspection_complete=True,account_ready=True,
                       checked_at=10 if tid=='stale' else 99,streaming=tid=='streaming',
                       url='https://chatgpt.com/c/saved' if tid=='saved' else 'https://chatgpt.com/',
                       draft='text' if tid=='draft' else '\n') for tid in ids]
        self.assertEqual(available(checks,dict(windows=windows),{'reserved'},{'cooling':120},100),
                         ['free','saved'])

    def test_paper_order_keeps_later_pages_of_earlier_group(self):
        from contextlib import closing
        import sqlite3
        from oled_formulas.formula_dispatch import index_paper_order
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('create table crops(batch integer,paper text)')
            rows=[(1,'a'),(1,'b'),(2,'c'),(3,'a'),(4,'c'),(5,'d')]
            db.executemany('insert into crops values(?,?)',rows)
            index_paper_order(db)
            self.assertEqual(list(db.execute('select batch from formula_paper_order order by first_batch,batch')),
                             [(1,),(3,),(2,),(4,),(5,)])
            self.assertEqual(list(db.execute('select * from crops order by rowid')),rows)

    def test_parallel_dispatch_shares_loop_and_never_assigns_a_tab_twice(self):
        import asyncio
        import sqlite3
        import time
        from contextlib import closing
        from unittest.mock import patch
        from playwright.sync_api import sync_playwright
        from oled_formulas import formula_dispatch
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(':memory:')) as db, sync_playwright() as pw:
            root = Path(directory)
            config = dict(catalog_path=str(root/'catalog.sqlite3'))
            db.executescript("create table batches(id integer primary key,state text,reason text);"
                             "create table pending_collections(batch integer,next_check real);create table crops(batch integer,paper text);")
            db.executemany("insert into batches values(?,'queued',null)", [(i,) for i in range(1,8)])
            tids = list('abcdef')
            (root/'shared-gpt-window.json').write_text(json.dumps(dict(startup_request_id='r',
                    slots=[dict(target_id=t) for t in tids])))
            (root/'browser-start-request.json').write_text(json.dumps(dict(id='r')))
            pool = dict(windows={tid:dict(state='ready_blank') for tid in tids})
            pages = [dict(target_id=tid,checked_at=time.time(),inspection_complete=True,
                          account_ready=True,draft='\n') for tid in tids]
            holding = {}
            visits = []
            peak = []
            def process(batch,target,progress):
                db.execute("update batches set state='active' where id=?",(batch,))
                holding[batch] = target
                visits.append(batch)
                peak.append((len(holding),len(set(holding.values()))))
                pw._sync(asyncio.sleep(.05))
                del holding[batch]
                db.execute("update batches set state='done' where id=?",(batch,))
            with patch.object(formula_dispatch,'observe',return_value=pages), \
                    patch.object(formula_dispatch,'load_pool',return_value=pool), \
                    patch.object(formula_dispatch,'shared_submission_status',return_value=dict(allowed=True)):
                formula_dispatch.dispatch(config,{},db,root,pw,None,lambda:True,process,lambda:None)
            self.assertEqual(sorted(visits),list(range(1,8)))
            self.assertIn((5,5),peak)
            self.assertTrue(all(count==unique for count,unique in peak))

    def test_idle_effort_only_adjusts_owned_empty_available_home(self):
        from oled_formulas.formula_dispatch import idle_effort_candidate
        page = dict(inspection_complete=True,account_ready=True,url='https://chatgpt.com/',
                    effort_control=dict(effort='medium',disabled=False))
        entry = dict(state='ready',kind='formula_only')
        self.assertTrue(idle_effort_candidate(page,entry))
        for change in (dict(streaming=True),dict(attachments=1),dict(draft='draft'),dict(login=True),
                       dict(url='https://chatgpt.com/c/old'),dict(effort_control={'effort':'high'}),
                       dict(effort_control={'effort':'medium','disabled':True})):
            self.assertFalse(idle_effort_candidate(dict(page,**change),entry))
        self.assertFalse(idle_effort_candidate(page,dict(entry,state='busy')))

    def test_held_composer_setting_excludes_sent_or_misattributed_work(self):
        import sqlite3
        from contextlib import closing
        from oled_formulas.formula_dispatch import held_before_send
        with tempfile.TemporaryDirectory() as d, closing(sqlite3.connect(':memory:')) as db:
            root = Path(d)
            folder = root/'batches/000007'
            folder.mkdir(parents=True)
            db.execute('create table batches(id integer,state text)')
            db.execute("insert into batches values(7,'held')")
            entry = dict(kind='formula_only',active_paper_id='formula-display-7')
            receipt = dict(state='upload_preparation',temporary=True,job_id='formula-display-7',
                           window_target='t',zip_sha256='digest')
            (folder/'packet.json').write_text(json.dumps(dict(batch=7,sha256='digest')))
            (folder/'status.json').write_text(json.dumps(dict(state='blocked',last=dict(target='t'))))
            for change, expected in (({},True),({'state':'submitted'},False),({'at':2},False),
                                     ({'window_target':'other'},False),({'zip_sha256':'other'},False)):
                (folder/'attempt.json').write_text(json.dumps(dict(receipt,**change)))
                self.assertEqual(held_before_send(db,root,entry,'t'),expected)

    def test_unsent_slot_release_preserves_held_batch_and_prior_archive(self):
        import sqlite3
        from contextlib import closing, nullcontext
        from unittest.mock import Mock, patch
        from oled_formulas import formula_dispatch as dispatch
        from browser.api import shared_pool_store__load_pool as load
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(':memory:')) as db:
            root = Path(directory)
            folder = root/'batches/000007'
            folder.mkdir(parents=True)
            tid = 't'
            url = 'https://chatgpt.com/?temporary-chat=true'
            previous = dict(active_paper_id='formula-display-6')
            entry = dict(state='busy',kind='formula_only',active_paper_id='formula-display-7',
                         previous_saved_response=previous)
            pool_file = root/'gpt-window-pool.json'
            pool_file.write_text(json.dumps(dict(windows={tid:entry})))
            db.execute('create table batches(id integer,state text)')
            db.execute("insert into batches values(7,'held')")
            bundle = folder/'batch.zip'
            bundle.write_bytes(b'frozen')
            sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
            (folder/'packet.json').write_text(json.dumps(dict(batch=7,sha256=sha)))
            (folder/'status.json').write_text(json.dumps(dict(state='blocked',last=dict(target=tid))))
            receipt = dict(state='upload_preparation',job_id='formula-display-7',window_target=tid,
                           temporary=True,zip_sha256=sha,prompt='batch '+sha)
            (folder/'attempt.json').write_text(json.dumps(receipt))
            check = dict(target_id=tid,url=url,account_ready=True,inspection_complete=True,composer_available=True)
            page = Mock(url=url)
            cfg = dict(catalog_path=str(root/'catalog'))
            with patch('browser.api.web_page_observer__responsive_lock',return_value=nullcontext()), \
                    patch('oled_formulas.formula_pilot.saved_formula_response',return_value=True), \
                    patch('browser.api.shared_window_owner__require_reusable'), patch.object(dispatch,'require_slot'), \
                    patch.object(dispatch,'shared_submission_status',return_value={'allowed':True}), \
                    patch.object(dispatch,'enumerate_pages',return_value={'pages':{tid:page}}), \
                    patch('browser.api.shared_page_health__snapshot_page',side_effect=[check,dict(check,draft='mine'),check,check]):
                dispatch.release_unsent_slots(cfg,{},db,None,None,[check],load(pool_file),root,lambda:True)
                self.assertEqual(load(pool_file)['windows'][tid],entry)
                dispatch.release_unsent_slots(cfg,{},db,None,None,[check],load(pool_file),root,lambda:True)
            released = json.loads((folder/'unsent-slot-release.json').read_bytes())
            self.assertTrue(dispatch.historical_slot_receipt({},root,7,'held',tid,receipt))
            self.assertFalse(dispatch.historical_slot_receipt({},root,7,'active',tid,receipt))
            self.assertFalse(dispatch.historical_slot_receipt({},root,7,'held',tid,dict(receipt,state='submitted')))
            folder8=root/'batches/000008'
            folder8.mkdir()
            receipt8=dict(receipt,job_id='formula-display-8')
            (folder8/'batch.zip').write_bytes(bundle.read_bytes())
            (folder8/'attempt.json').write_text(json.dumps(receipt8))
            (folder8/'packet.json').write_text(json.dumps(dict(batch=8,sha256=sha)))
            (folder8/'status.json').write_bytes((folder/'status.json').read_bytes())
            db.execute("insert into batches values(8,'held')")
            current=dict(entry,active_paper_id='formula-display-8')
            pool_file.write_text(json.dumps(dict(windows={tid:current})))
            with patch('browser.api.web_page_observer__responsive_lock',return_value=nullcontext()), patch(
                    'oled_formulas.formula_pilot.saved_formula_response',return_value=True), patch(
                    'browser.api.shared_window_owner__require_reusable'),patch.object(dispatch,'require_slot'),patch.object(
                    dispatch,'shared_submission_status',return_value={'allowed':True}),patch.object(
                    dispatch,'enumerate_pages',return_value={'pages':{tid:page}}),patch(
                    'browser.api.shared_page_health__snapshot_page',return_value=check):
                bad=dict(released,evidence=dict(released['evidence'],target='other'))
                (folder/'unsent-slot-release.json').write_text(json.dumps(bad))
                dispatch.release_unsent_slots(cfg,{},db,None,None,[check],load(pool_file),root,lambda:True)
                self.assertEqual(load(pool_file)['windows'][tid],current)
                (folder/'unsent-slot-release.json').write_text(json.dumps(released))
                dispatch.release_unsent_slots(cfg,{},db,None,None,[check],load(pool_file),root,lambda:True)
                self.assertEqual(load(pool_file)['windows'][tid]['state'],'ready_blank')
            self.assertEqual(db.execute('select state from batches').fetchone(),('held',))
            updated = load(pool_file)['windows'][tid]
            self.assertEqual(updated['state'],'ready_blank')
            self.assertEqual(updated['previous_saved_response'],previous)
            self.assertNotIn('never_submitted',updated)
            self.assertEqual(json.loads(Path(updated['unsent_slot_release']).read_text())['evidence']['attempt'],receipt8)

    def test_completed_turn_requires_single_stable_candidate(self):
        from oled_formulas.formula_pilot import completed_formula_text
        snapshot = dict(inspection_complete=True,terminal_complete=True,streaming=False,
                        answer_element_count=1,answer_texts=['answer'],user_texts=['request'])
        self.assertEqual(completed_formula_text(snapshot),'answer')
        for changed in (dict(terminal_complete=False),dict(streaming=True),dict(errors=['error']),
                        dict(answer_texts=[]),dict(terminal_stopped=True),dict(user_texts=['a','b'])):
            self.assertEqual(completed_formula_text(dict(snapshot,**changed)),'')

    def test_reused_blank_requires_the_original_completed_formula_receipt(self):
        from oled_formulas.formula_pilot import saved_formula_blank
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)/'display-equations/batches/000001'
            folder.mkdir(parents=True)
            raw = folder/'response.txt'
            raw.write_text('saved')
            sha = hashlib.sha256(raw.read_bytes()).hexdigest()
            url = 'https://chatgpt.com/c/example?temporary-chat=true'
            receipt = dict(state='raw_saved',temporary=True,job_id='formula-display-1',
                           window_target='target',url=url,raw_sha256=sha)
            (folder/'attempt.json').write_text(json.dumps(receipt))
            saved = dict(kind='formula_only',active_paper_id=receipt['job_id'],raw_path=str(raw),
                         conversation_url=url,raw_sha256=sha)
            entry = dict(state='ready_blank',previous_saved_response=saved)
            control = dict(batch=3,folder=d)
            self.assertTrue(saved_formula_blank(control,'target',entry))
            self.assertFalse(saved_formula_blank(control,'other',entry))
            self.assertFalse(saved_formula_blank(control,'target',dict(entry,state='busy')))
            raw.write_text('changed')
            self.assertFalse(saved_formula_blank(control,'target',entry))

    def test_legacy_archived_batch_requires_its_original_prompt_zip_and_number(self):
        from oled_formulas.formula_queue import PROMPT
        from oled_formulas.formula_pilot import saved_formula_response
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)/'automatic/batches/000001'
            folder.mkdir(parents=True)
            raw = folder/'response.txt'
            raw.write_text('answer')
            bundle = folder/'batch.zip'
            bundle.write_bytes(b'original')
            sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
            url = 'https://chatgpt.com/c/test?temporary-chat=true'
            saved = dict(kind='formula_only',active_paper_id='formula-batch-1',raw_path=str(raw),
                         raw_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),conversation_url=url)
            receipt = dict(window_target='t',temporary=True,state='raw_saved',url=url,
                           zip_sha256=sha,prompt=PROMPT+sha,raw_sha256=saved['raw_sha256'])
            (folder/'packet.json').write_text(json.dumps(dict(batch=1,sha256=sha)))
            for change, expected in (({},True),({'prompt':'other'},False),({'job_id':'other'},False),
                                     ({'window_target':'other'},False),({'state':'submitted'},False)):
                (folder/'attempt.json').write_text(json.dumps(dict(receipt,**change)))
                self.assertEqual(saved_formula_response(dict(folder=directory),'t',saved),expected)
            (folder/'attempt.json').write_text(json.dumps(receipt))
            bundle.write_bytes(b'changed')
            self.assertFalse(saved_formula_response(dict(folder=directory),'t',saved))

    def test_loading_recovery_rechecks_live_page_and_navigates_only_once(self):
        import sqlite3
        from contextlib import closing
        from unittest.mock import Mock, patch
        from oled_formulas import formula_reload as repair
        url = 'https://chatgpt.com/c/test?temporary-chat=true'
        entry = dict(state='ready',conversation_url=url,active_paper_id='formula-display-1',raw_sha256='s')
        pool = dict(windows={'t':entry})
        check = dict(target_id='t',url=url,checked_at=200,inspection_complete=True,
                     page_load=dict(ready_state='loading',started_at=1,navigation_type='reload'))
        for change in (dict(draft='mine'),dict(login=True),dict(verification=True),dict(uploading=True),
                       dict(streaming=True),dict(url='https://chatgpt.com/'),dict(checked_at=5)):
            self.assertIsNone(repair.stalled_load(dict(check,**change),entry,100))
        with tempfile.TemporaryDirectory() as directory, closing(sqlite3.connect(':memory:')) as db:
            root = Path(directory)
            db.execute('create table batches(state text)')
            policy = dict(enabled=True,startup_stalled_after_seconds=100,check_interval_seconds=30)
            cfg = dict(catalog_path=str(root/'db'),web_cards=dict(shared_window=dict(health_repair=policy)))
            page = Mock(url=url)
            observed = {}
            with patch.object(repair,'saved_formula_response',return_value=True), \
                    patch.object(repair,'require_slot'), patch.object(repair,'load_pool',return_value=pool), \
                    patch.object(repair,'enumerate_pages',return_value={'pages':{'t':page}}), \
                    patch.object(repair,'snapshot_page',side_effect=[dict(check,login=True),dict(check,checked_at=250)]):
                for stamp in (200,220,235,250,300):
                    repair.recover_load(cfg,{},db,None,[dict(check,checked_at=stamp)],pool,root,observed,lambda:True)
                page.goto.assert_called_once_with(url,wait_until='commit',timeout=12000)
                journals = list((root/'page-load-recovery').glob('*.json'))
                self.assertEqual(len(journals),1)
                self.assertEqual(json.loads(journals[0].read_text())['state'],'navigation_returned')

    def test_jsonl_language_label_is_only_removed_before_a_valid_object(self):
        from oled_formulas.formula_pilot import response_objects
        self.assertEqual(response_objects('jsonl{"latex":"jsonl"}'),[{'latex':'jsonl'}])
        for broken in ('jsonl broken','jsonlines{}','jsonl{} truncated'):
            with self.assertRaises(ValueError):
                response_objects(broken)

    def test_adjacent_json_objects_preserve_math_and_reject_partial_replies(self):
        from oled_formulas.formula_pilot import response_objects
        item = dict(latex=r'\frac{a}{b}', reason='}{')
        text = json.dumps(item)
        self.assertEqual(response_objects('```jsonl\n'+text+text+'\n```'),[item,item])
        for bad in (text+'{',text+' trailing','['+text+']'):
            with self.assertRaises(ValueError):
                response_objects(bad)

    def test_pdf_small_type_qualifier_flags_missing_token(self):
        from oled_formulas.display_equations import transcription_check
        lines = [dict(id=1,text='X',bbox=[10,20,20,40]),dict(id=2,text='dT',bbox=[20,15,26,25])]
        item = dict(line_ids=[1,2],latex='X^{T}')
        self.assertEqual(transcription_check(item,lines)['missing_pdf_tokens'],['dT'])
        item['latex'] = 'X^{dT}'
        self.assertEqual(transcription_check(item,lines)['transcription_status'],'unverified')

    def test_vector_symbol_at_left_edge_is_kept_without_crossing_whitespace(self):
        from PIL import Image, ImageDraw
        from oled_formulas.display_equations import include_edge_symbols
        image = Image.new('L',(1000,100),255)
        draw = ImageDraw.Draw(image)
        draw.polygon([(94,40),(102,60),(86,60)],outline=0)
        draw.rectangle((54,40,62,60),fill=0)
        left,_,_,_ = include_edge_symbols(image,[98,300,250,700])
        self.assertGreater(left,62)
        self.assertLess(left,86)

    def test_mode_requires_all_original_pauses(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            config={'catalog_path':str(root/'catalog.sqlite3')}
            self.assertFalse(enabled(config))
            for n in CONTROLS:(root/n).write_text('{"paused_by_user":true}')
            hashes={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in CONTROLS}
            (root/'formula-only-control.json').write_text(json.dumps(dict(enabled=True,pause_hashes=hashes)))
            self.assertTrue(enabled(config))
            (root/CONTROLS[0]).write_text('{"paused_by_user":true,"newer":true}')
            self.assertFalse(enabled(config))
    def test_packet_coverage(self):
        job={'id':'j','keys_json':'["i"]'}
        evidence=[dict(id='i',page=2)]
        item=dict(id='i',page=2,type='equation',latex='x=y')
        ok=dict(job='j',items=[item])
        self.assertEqual(check_answer(json.dumps(ok),job,evidence),ok)
        for result in [dict(job='k',items=[item]),dict(job='j',items=[]),dict(job='j',items=[item,item]),
                       dict(job='j',items=[dict(item,page=3)])]:
            with self.assertRaises(ValueError):check_answer(json.dumps(result),job,evidence)

    def test_panel_controls_only_the_registered_pilot(self):
        from unittest.mock import patch
        from oled_formulas.formula_only import control_pilot, digest
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            config = {'catalog_path': str(base / 'catalog.sqlite3')}
            for name in CONTROLS:
                (base / name).write_text('{"paused_by_user": true}')
            hashes = {name: digest(base / name) for name in CONTROLS}
            packet = base / 'two-papers.zip'
            packet.write_bytes(b'packet')
            request = dict(mode='temporary_pilot', enabled=True, pilot_folder=d,
                           pilot_zip_sha256=digest(packet), pause_hashes=hashes)
            path = base / 'formula-only-control.json'
            path.write_text(json.dumps(request))
            with patch('subprocess.run') as launch:
                launch.return_value.returncode = 0
                control_pilot(config, False)
                self.assertFalse(enabled(config))
                launch.assert_not_called()
                control_pilot(config, True)
                self.assertEqual(json.loads(path.read_text()), request)
                self.assertEqual(launch.call_args.args[0][1], 'kickstart')
                (base / 'attempt.json').write_text('{}')
                with self.assertRaises(ValueError):
                    control_pilot(config, True)
                self.assertEqual(launch.call_count, 1)
            self.assertEqual(hashes, {name: digest(base / name) for name in CONTROLS})

    def test_temporary_locked_picker_requires_exact_model_and_high(self):
        from unittest.mock import MagicMock, patch
        from oled_formulas.formula_pilot import temporary_settings
        page = MagicMock()
        picker = page.get_by_role.return_value
        picker.count.return_value = 1
        picker.is_visible.return_value = True
        picker.is_enabled.return_value = False
        picker.get_attribute.return_value = 'high'
        with patch('oled_formulas.formula_pilot.temporary', return_value=True):
            picker.inner_text.return_value = '6 High'
            with self.assertRaises(ValueError):
                temporary_settings(page, 'GPT-6.2')
            picker.inner_text.return_value = '6.2 High'
            self.assertEqual(temporary_settings(page, 'GPT-6.2')['model'], 'GPT-6.2')
            picker.get_attribute.return_value = 'medium'
            with self.assertRaises(ValueError):
                temporary_settings(page, 'GPT-6.2')

    def test_multi_paper_batch_preserves_multiple_equations_and_non_equations(self):
        import sqlite3
        import zipfile
        from contextlib import closing
        from oled_formulas.formula_pilot import save_formulas
        from oled_formulas.formula_queue import publish
        from oled_formulas.formula_only import digest
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/'articles').mkdir()
            inputs = []
            for paper in ('a', 'b'):
                (root/'articles'/(paper+'.json')).write_text(json.dumps(
                    dict(title=paper,source_path='/'+paper,source_sha256=paper)))
                inputs.append(dict(paper_id=paper,pdf_page=1,crop_id='1',source_sha256=paper))
            with zipfile.ZipFile(root/'batch.zip','w') as bundle:
                bundle.writestr('manifest.json',json.dumps(inputs))
            results = [dict(inputs[0],kind='equation',latex=x,python_rhs=x) for x in ('x','y')]
            results.append(dict(inputs[1],kind='non_equation'))
            (root/'response.txt').write_text('\n'.join(map(json.dumps,results)))
            receipt = dict(zip_sha256=digest(root/'batch.zip'),model={'model':'GPT-6.2'})
            save_formulas(dict(batch=1,folder=d),root,receipt,lambda *args,**kwargs:None)
            self.assertEqual(len((root/'formulas.jsonl').read_text().splitlines()),2)
            with closing(sqlite3.connect(':memory:')) as db:
                db.executescript("create table outputs(paper,batch,records,primary key(paper,batch));create table batches(id,state,reason);insert into batches values(1,'active',null);")
                for _ in range(2):
                    publish(db,root,root,1,root)
                self.assertEqual(db.execute('select state from batches').fetchone()[0],'done')
                self.assertEqual(len(json.loads((root/'by-paper/a.json').read_text())['formulas']),2)
                self.assertEqual(len(json.loads((root/'by-paper/b.json').read_text())['other_crops']),1)
