import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

from oled_formulas.display_equations import crop_results, locate


class DisplayEquations(unittest.TestCase):
    def test_number_is_optional_and_math_inside_a_sentence_is_rejected(self):
        math_line = dict(id=1,text='I = I₀ exp(−t/τ)',bbox=[150,220,390,245])
        item = dict(layout='display',line_ids=[1],bbox=[148,218,392,247])
        box = locate(item,[math_line])
        self.assertLess(box[0],150)
        self.assertGreater(box[3],245)
        for text in ('where I = I₀', 'Fig. 2', '(1)', 'The luminous intensity equals I at time t.'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                locate(item,[dict(math_line,text=text)])
        with self.assertRaises(ValueError):
            locate(dict(item,line_ids=[]),[dict(math_line,text='for t = 0,',bbox=[110,220,450,245])])

    def test_no_files_for_inline_or_empty_regions(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            image = Image.new('RGB',(500,500),'white')
            ImageDraw.Draw(image).text((80,115),'I = I0',fill='black')
            png = io.BytesIO()
            image.save(png,format='PNG')
            with zipfile.ZipFile(folder/'batch.zip','w') as bundle:
                bundle.writestr('page.png',png.getvalue())
                bundle.writestr('layout.json','[]')
            page = dict(paper_id='p',pdf_page=1,crop_id='P0001',image='page.png',layout='layout.json')
            item = dict(page,kind='equation',latex='I=I_0',layout='display',line_ids=[],bbox=[150,210,390,280])
            records = [dict(item),dict(item,layout='inline'),dict(item,bbox=[100,500,400,570])]
            crop_results(folder,[page],records)
            self.assertEqual([r['kind'] for r in records],['equation','uncertain','uncertain'])
            self.assertEqual(len(list((folder/'equations').glob('*.png'))),1)

    def test_missing_layout_requires_isolated_math_evidence(self):
        line = dict(id=1, text='I ∝ exp(−d/L)', bbox=[410,100,570,130])
        item = dict(kind='equation', bbox=[425,107,585,137], line_ids=[1])
        self.assertLess(locate(item,[line])[0], 410)
        for other in (dict(id=2,text='where',bbox=[100,100,150,130]),
                      dict(id=2,text='caption',bbox=[650,100,750,130])):
            with self.assertRaises(ValueError):
                locate(item,[line,other])
        for changes in (dict(layout='inline'),dict(line_ids=[]),dict(bbox=[10,10,20,20])):
            with self.assertRaises(ValueError):
                locate(dict(item,**changes),[line])

    def test_oled_scope_and_unfrozen_mixed_batch(self):
        import sqlite3
        from contextlib import closing
        from unittest.mock import patch
        from oled_formulas.api import oled_candidate
        from oled_formulas import display_equations as display
        for title in ('water-cooled device','A pooled analysis'):
            self.assertFalse(oled_candidate(title,''))
        for term in ('OLED','PHOLEDs','WOLED','qd-oled','organic light-emitting diodes'):
            self.assertTrue(oled_candidate('water-cooled',term))
        with tempfile.TemporaryDirectory() as tmp, closing(sqlite3.connect(':memory:')) as db:
            root=Path(tmp)
            db.executescript("""create table batches(id integer primary key,state,reason);
                insert into batches values(1,'active',null);
                create table crops(batch,paper,crop);
                insert into crops values(1,'oled','P0001'),(1,'cooled','P0001');""")
            rows=[dict(id='oled',title='PHOLED'),dict(id='cooled',title='cooled liquid')]
            with patch('core.api.literature_catalog__source_records',return_value=rows), patch.object(display,'allowed',return_value=False):
                with self.assertRaisesRegex(ValueError,'oled'):
                    display.build_packet(db,{'catalog_path':'fixture'},root,root/'batch',1)
            self.assertEqual(db.execute('select paper,batch from crops order by batch').fetchall(),[('oled',1),('cooled',2)])
            self.assertEqual(db.execute('select state from batches where id=2').fetchone(),('held',))
