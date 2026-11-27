import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from oled_formulas.formula_pilot import confirm_empty_answer
from oled_formulas.formula_queue import publish, recover_publications
from oled_formulas.formula_results import check_python


class ReportRegressions(unittest.TestCase):
    def test_training_candidates_and_printed_labels(self):
        from oled_formulas.formula_results import training_view
        from oled_formulas.display_equations import transcription_check
        good=dict(latex='x',crop_path='crop',transcription_status='unverified',python_status='unavailable')
        rows=[good,dict(good,visual_review_required=True),dict(good,python_status='needs_review'),
              dict(good,transcription_status='needs_review')]
        view=training_view({'title':'Charge transport in OLEDs'},rows)
        self.assertEqual(len(view['training_candidates']),1)
        self.assertEqual(view['training_formulas'],[])
        self.assertFalse(training_view({'title':'Switch OLED for rehabilitation'},rows)['training_candidates'])
        r=dict(line_ids=[1,2,3],latex='x',equation_label='(Eq. 2.2)')
        lines=[dict(id=1,text='x',bbox=[0,0,10,20]),dict(id=2,text='(Eq. 2.2).',bbox=[0,0,10,8]),
               dict(id=3,text='eff',bbox=[0,0,10,8])]
        self.assertEqual(transcription_check(r,lines)['missing_pdf_tokens'],['eff'])
        self.assertIn('Eq',transcription_check(dict(r,equation_label='3'),lines)['missing_pdf_tokens'])

    def test_blank_wait_requires_contiguous_confirmations_and_resumes_only_original(self):
        from oled_formulas.formula_pilot import prolonged_empty_answer
        from oled_formulas.formula_dispatch import resume_visible_answers
        from core.api import services__atomic_json as write
        with tempfile.TemporaryDirectory() as tmp,sqlite3.connect(':memory:') as db:
            out=Path(tmp);folder=out/'batches/000001';folder.mkdir(parents=True)
            rec=dict(job_id='formula-display-1',at=10,window_target='slot',zip_sha256='z',
                     url='https://chatgpt.com/c/6b086820-5c10-83ed-8c51-c06dcc993662',state='submitted')
            page=dict(inspection_complete=True,account_ready=True,target_id='slot',url=rec['url'],
                      user_texts=['request'],streaming=False,answer_element_count=0)
            for ts in range(100,1900,100):
                self.assertFalse(prolonged_empty_answer(folder,rec,dict(page,checked_at=ts)))
            self.assertTrue(prolonged_empty_answer(folder,rec,dict(page,checked_at=1900)))
            self.assertFalse(prolonged_empty_answer(folder,rec,dict(page,checked_at=1910,streaming=True)))
            write(folder/'attempt.json',rec)
            db.executescript("create table batches(id,state,reason);create table pending_collections(batch primary key,next_check);")
            db.execute("insert into batches values(1,'review','原会话连续半小时无回答节点，等待原页出现正文')")
            resume_visible_answers(db,out,[dict(page,target_id='other',answer_texts=['result'])])
            self.assertEqual(db.execute('select state from batches').fetchone(),('review',))
            resume_visible_answers(db,out,[dict(page,answer_texts=['result'])])
            self.assertEqual(db.execute('select state from batches').fetchone(),('awaiting_answer',))

    def test_scientific_training_receipt_is_bound_to_saved_formula(self):
        from oled_formulas.formula_results import verified_latex
        with tempfile.TemporaryDirectory() as tmp:
            crop=Path(tmp)/'crop';crop.write_bytes(b'image')
            row=dict(paper_id='p',source_batch=2,pdf_page=3,crop_path=str(crop),latex='x=y',
                     transcription_status='unverified',python_status='unavailable')
            check=dict(paper_id='p',batch=2,pdf_page=3,latex_sha256=hashlib.sha256(b'x=y').hexdigest(),
                       raw_sha256='raw',crop_sha256=hashlib.sha256(b'image').hexdigest(),page_evidence='page 3',
                       display_verified=True,latex_verified=True,scientific_verified=True)
            review=dict(schema='oled-scientific-review-v1',reviewer='independent',topic_verified=True,
                        topic_evidence='device theory',source_sha256='pdf',items=[check])
            def approve(item, receipt):
                return verified_latex(dict(source_sha256='pdf'),[item],receipt,[dict(batch=2,raw_sha256='raw')])
            self.assertEqual(approve(row,review)[0]['latex'],'x=y')
            self.assertFalse(approve(row,dict(review,items=[check,check])))
            self.assertFalse(approve(dict(row,visual_review_required=True),review))
            crop.write_bytes(b'changed')
            self.assertFalse(approve(row,review))

    def test_code_is_validated_without_execution(self):
        samples = {'math.sqrt(x**2 + y**2)':True, 'math.pi*r**2':True,
                   'math.sin()':False, 'math.exp(x,y)':False, 'np.array([x])':False, '(a,b)':False, 'sum(x for x in xs)':False,
                   '__import__("os").system(x)':False, 'x.y':False}
        for expr, ok in samples.items():
            with self.subTest(expr=expr):
                item = dict(python_rhs=expr)
                check_python(item)
                self.assertEqual(bool(item['python_rhs']),ok)
                if not ok:self.assertEqual(item['rejected_python_rhs'],expr)

    def test_empty_terminal_requires_two_stationary_observations(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            url='https://chatgpt.com/c/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
            rec=dict(window_target='t',url=url,job_id='formula-display-5',at=1,zip_sha256='sha')
            page=dict(target_id='t',url=url,user_texts=['q'],inspection_complete=True,terminal_complete=True,
                      answer_element_count=1,streaming=False,draft='\n',checked_at=100)
            self.assertFalse(confirm_empty_answer(folder,rec,page))
            self.assertFalse(confirm_empty_answer(folder,rec,dict(page,checked_at=140,streaming=True)))
            self.assertFalse(confirm_empty_answer(folder,rec,dict(page,checked_at=141)))
            self.assertTrue(confirm_empty_answer(folder,rec,dict(page,checked_at=171)))
            self.assertFalse(confirm_empty_answer(folder,rec,dict(page,url='https://chatgpt.com/')))

    def test_publish_recovery_and_partial_coverage(self):
        with tempfile.TemporaryDirectory() as d, sqlite3.connect(':memory:') as db:
            root=Path(d);output=root/'display-equations';folder=output/'batches/000001'
            folder.mkdir(parents=True);(root/'articles').mkdir()
            pdf=root/'source.pdf';pdf.write_bytes(b'fixture')
            sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
            def store(p,v):p.write_text(json.dumps(v))
            store(root/'articles/a.json',dict(title='paper',source_sha256=sha(pdf),source_path=str(pdf)))
            db.executescript("""create table outputs(paper,batch,records,primary key(paper,batch));
                create table crops(batch,job,paper,crop);create table batches(id,state,reason);
                create table result_versions(batch primary key,version);create table pending_collections(batch,next_check);
                insert into batches values(1,'active',null),(2,'held','review');
                insert into crops values(1,'page','a','P0001'),(2,'page','a','P0002');""")
            row=dict(paper_id='a',pdf_page=1,crop_id='P0001',source_sha256=sha(pdf))
            with zipfile.ZipFile(folder/'batch.zip','w') as z:z.writestr('manifest.json',json.dumps([row]))
            (folder/'response.txt').write_text('raw')
            store(folder/'packet.json',dict(batch=1,policy='display-pages-v1',sha256=sha(folder/'batch.zip')))
            store(folder/'attempt.json',dict(state='raw_saved',job_id='formula-display-1',raw_sha256=sha(folder/'response.txt'),
                                             zip_sha256=sha(folder/'batch.zip')))
            store(folder/'records.jsonl',dict(row,kind='equation',python_rhs='np.array([x])',latex='x'))
            with patch('oled_formulas.formula_queue.render_paper',side_effect=OSError('disk')):
                with self.assertRaises(OSError):publish(db,root,output,1,folder)
            self.assertEqual(db.execute('select state from batches where id=1').fetchone(),('publishing',))
            recover_publications(db,root,output,lambda:True)
            result=json.loads((output/'by-paper/a.json').read_bytes())
            self.assertEqual(result['missing_pages'],[2])
            self.assertFalse(result['complete'])
            self.assertEqual(result['failed_batches_at_export'],[2])
            self.assertEqual(result['formulas'][0]['python_status'],'needs_review')
            self.assertEqual(len(result['source_batches']),1)
            self.assertEqual(db.execute('select state from batches where id=1').fetchone(),('done',))
            from oled_formulas.formula_queue import refresh_image_reviews
            rec=json.loads((folder/'attempt.json').read_bytes())
            rec.update(at=1,window_target='original',url='https://chatgpt.com/c/1234',temporary=True)
            store(folder/'attempt.json',rec)
            note=dict(checked_at=2,target='wrong',url=rec['url'],zip_sha256=rec['zip_sha256'],job_id=rec['job_id'],image_health={'image_notice':True})
            db.execute('create table image_review_publications(batch primary key,evidence_sha256)')
            store(folder/'observed-image-warning.json',note)
            refresh_image_reviews(db,root,output,lambda:True)
            self.assertIsNone(db.execute('select batch from image_review_publications').fetchone())
            store(folder/'observed-image-warning.json',dict(note,target='original'))
            refresh_image_reviews(db,root,output,lambda:True)
            result=json.loads((output/'by-paper/a.json').read_bytes())
            self.assertTrue(result['review_items'][0]['visual_review_required'])
            self.assertEqual(result['formulas'][0]['source_batch'],1)
            self.assertFalse(result['training_formulas'])
            with patch('oled_formulas.formula_queue.render_paper',side_effect=AssertionError('duplicate')):
                refresh_image_reviews(db,root,output,lambda:True)
            # The raw packet may cover every page while contradicting itself.
            positive = dict(row, kind='equation', latex='x=y', python_rhs='y')
            store(folder/'observed-image-warning.json', {})
            negative = dict(row, kind='non_equation', reason='text only')
            (folder/'records.jsonl').write_text('\n'.join(map(json.dumps, (negative,positive))))
            publish(db,root,output,1,folder)
            result = json.loads((output/'by-paper/a.json').read_bytes())
            self.assertEqual(db.execute('select state from batches where id=1').fetchone(), ('review',))
            self.assertEqual(result['conflict_pages'], [1])
            self.assertEqual(result['formulas'], [])
            self.assertEqual(len(result['review_items']), 2)
            self.assertEqual(result['review_items'][1]['unverified_python_rhs'], 'y')
            self.assertFalse(result['review_items'][1]['python_rhs'])
            store(folder/'records.jsonl',positive)
            publish(db,root,output,1,folder)
            result = json.loads((output/'by-paper/a.json').read_bytes())
            self.assertEqual(result['review_items'][0]['python_mapping_issues'], ['unconfirmed_target'])
            self.assertEqual(result['formulas'][0]['python_rhs'], '')
            pdf.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'指纹'):publish(db,root,output,1,folder)

    def test_home_recovery_requires_stable_empty_target_and_receipt(self):
        from contextlib import nullcontext
        from unittest.mock import MagicMock
        from oled_formulas import formula_reload as recovery
        from core.api import services__atomic_json as write
        import time
        with tempfile.TemporaryDirectory() as tmp, sqlite3.connect(':memory:') as db:
            root=Path(tmp); path=root/'gpt-window-pool.json'; tid='slot'
            url='https://chatgpt.com/'
            entry=dict(state='ready',kind='formula_only',active_paper_id='formula-display-7',
                       raw_path='/raw',raw_sha256='saved',conversation_url=url+'c/original')
            write(path,dict(windows={tid:entry}))
            db.execute('create table batches(id,state)')
            page=MagicMock(url=url)
            now=time.time()
            base=dict(target_id=tid,url=url,inspection_complete=True,account_ready=True,account_authenticated=True,composer_available=True,
                      page_load=dict(ready_state='complete',started_at=1))
            seen={}
            def sample(age,**fields):
                check=dict(base,checked_at=now+age,**fields)
                recovery.adopt_completed_homes({'catalog_path':str(root/'catalog')},{},db,None,None,[check],recovery.load_pool(path),root,set(),seen,lambda:True)
            with patch('browser.api.web_page_observer__responsive_lock',return_value=nullcontext()), \
                 patch('browser.api.web_card_pool__shared_submission_status',return_value={'allowed':True}), \
                 patch.object(recovery,'completed_home',side_effect=lambda *args:dict(entry)), \
                 patch.object(recovery,'require_slot'),patch.object(recovery,'enumerate_pages',return_value={'pages':{tid:page}}), \
                 patch.object(recovery,'snapshot_page',return_value=dict(base,checked_at=now+71)):
                sample(0);sample(29);sample(30,draft='new');sample(40);sample(69)
                self.assertEqual(json.loads(path.read_bytes())['windows'][tid],entry)
                sample(71)
            blank=json.loads(path.read_bytes())['windows'][tid]
            self.assertEqual(blank['state'],'ready_blank')
            self.assertEqual(blank['previous_saved_response']['raw_sha256'],'saved')
            self.assertFalse(blank['never_submitted'])

    def test_terminal_evidence_stays_on_original_assistant_turn(self):
        from unittest.mock import MagicMock
        from oled_formulas.formula_pilot import terminal_evidence
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            receipt = dict(window_target='slot',url='https://chatgpt.com/c/original',zip_sha256='zip',job_id='job')
            page = MagicMock(url=receipt['url'])
            page.evaluate.return_value = dict(assistant_count=1,turns=[dict(innerText='',textContent='',innerHTML='')])
            snap = dict(target_id='slot',url=page.url,inspection_complete=True,streaming=False,user_texts=['original'],
                        terminal_complete=True,checked_at=1)
            self.assertFalse(terminal_evidence(page,folder,receipt,dict(snap,url='https://chatgpt.com/')))
            page.evaluate.assert_not_called()
            self.assertTrue(terminal_evidence(page,folder,receipt,snap))
            self.assertEqual(json.loads((folder/'terminal-answer-dom.json').read_bytes())['dom']['assistant_count'],1)


    def test_disjoint_box_requires_unique_printed_equation_number(self):
        from oled_formulas.display_equations import locate
        item=dict(layout='display',bbox=[10,10,120,30],line_ids=[1,2],equation_label='(1)')
        rows=[dict(id=1,text='x = y',bbox=[120,300,180,330]),dict(id=2,text='(1)',bbox=[350,300,380,330])]
        self.assertGreater(locate(item,rows)[1],290)
        with self.assertRaises(ValueError):locate(item,rows+[dict(id=3,text='(1)',bbox=[350,400,380,430])])
