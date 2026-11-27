import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile

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




    def test_disjoint_box_requires_unique_printed_equation_number(self):
        from oled_formulas.display_equations import locate
        item=dict(layout='display',bbox=[10,10,120,30],line_ids=[1,2],equation_label='(1)')
        rows=[dict(id=1,text='x = y',bbox=[120,300,180,330]),dict(id=2,text='(1)',bbox=[350,300,380,330])]
        self.assertGreater(locate(item,rows)[1],290)
        with self.assertRaises(ValueError):locate(item,rows+[dict(id=3,text='(1)',bbox=[350,400,380,430])])
