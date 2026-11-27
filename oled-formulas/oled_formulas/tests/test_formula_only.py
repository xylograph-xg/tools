import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from oled_formulas.formula_only import CONTROLS, enabled, check_answer

class FormulaTests(unittest.TestCase):

    def test_paper_order_keeps_later_pages_of_earlier_group(self):
        from contextlib import closing
        import sqlite3
        from oled_formulas.formula_queue import index_paper_order
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('create table crops(batch integer,paper text)')
            rows=[(1,'a'),(1,'b'),(2,'c'),(3,'a'),(4,'c'),(5,'d')]
            db.executemany('insert into crops values(?,?)',rows)
            index_paper_order(db)
            self.assertEqual(list(db.execute('select batch from formula_paper_order order by first_batch,batch')),
                             [(1,),(3,),(2,),(4,),(5,)])
            self.assertEqual(list(db.execute('select * from crops order by rowid')),rows)









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
