import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from oled_formulas.app_queue import admit, gate


class AppQueueTests(unittest.TestCase):
    def test_only_clean_unsent_batches_move_and_restart_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d, closing(sqlite3.connect(':memory:')) as db:
            root = Path(d)
            (root/'batches'/'000002').mkdir(parents=True)
            db.executescript("""create table batches(id integer primary key,state);
                create table pending_collections(batch);create table outputs(batch);
                create table entry_retries(batch);insert into entry_retries values(4);
                insert into pending_collections values(3);insert into outputs values(6);""")
            db.executemany('insert into batches values(?,?)',enumerate(
                ['queued','queued','queued','queued','review','queued','done','active'],1))
            admit(db,root)
            admit(db,root)
            self.assertEqual(dict(db.execute('select id,state from batches')),
                             {1:'app_queued',2:'queued',3:'queued',4:'queued',5:'review',6:'queued',7:'done',8:'active'})

    def test_account_check_requires_authenticated_embedded_app(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp, patch('oled_formulas.app_queue.Path.home',return_value=Path(tmp)):
            home=Path(tmp)/'.codex-chatgpt-web'
            release=home/'versions'/'6.2.0'
            paths=[release/'runtime/bun',release/'app/cli.js']
            for path in paths:
                path.parent.mkdir(parents=True)
                path.touch()
            settings=dict(mode='full',browserHost='launcher',browserInteractionMode='automatic',
                          useTemporaryChats=True,runtimeCommand=[str(p) for p in paths])
            config=home/'config.json'
            config.write_text(json.dumps(settings))
            with patch('oled_formulas.app_queue.subprocess.run') as check:
                check.return_value=SimpleNamespace(returncode=0,stdout='authenticated ChatGPT surface embedded in the launcher')
                self.assertIsNone(gate())
                self.assertEqual(check.call_args.args[0][-2:],['browser','check'])
                check.return_value=SimpleNamespace(returncode=1,stdout='')
                self.assertIn('登录',gate())
                check.reset_mock()
                config.write_text(json.dumps(dict(settings,browserHost='chrome')))
                self.assertIn('内置浏览器',gate())
                check.assert_not_called()

    def test_no_slot_recovery_requires_absence_of_any_transfer(self):
        from hashlib import sha256
        from types import SimpleNamespace
        from oled_formulas.app_queue import archived_unsent
        with tempfile.TemporaryDirectory() as d, closing(sqlite3.connect(':memory:')) as db:
            root=Path(d)
            folder=root/'batches/000012'
            folder.mkdir(parents=True)
            db.execute('create table entry_retries(batch,admitted_at)')
            (folder/'batch.zip').write_bytes(b'frozen')
            (folder/'packet.json').write_text(json.dumps({'batch':12,'sha256':sha256(b'frozen').hexdigest()}))
            (folder/'account-check.json').write_text('{}')
            (folder/'status.json').write_text(json.dumps({'state':'blocked','pid':4,'last':{'state':'checking_account','pid':4},
                                                         'reason':'没有通过原所有者守卫的空闲页'}))
            tr=SimpleNamespace(events={})
            self.assertTrue(archived_unsent(db,root,12,{},tr))
            tr.events['formula-display-12']=[{'event':'upload_started'}]
            self.assertFalse(archived_unsent(db,root,12,{},tr))

    def test_app_only_route_finishes_without_revisiting_legacy_chrome(self):
        from oled_formulas import formula_queue,display_equations
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            control=dict(folder=d,transport='codex_web_gpt',extraction=display_equations.POLICY)
            (root/'formula-only-control.json').write_text(json.dumps(control))
            output=root/display_equations.OUTPUT
            output.mkdir()
            with closing(sqlite3.connect(output/'queue.sqlite3')) as db:
                db.execute('create table batches(id integer primary key,state text,reason text)')
                db.execute("insert into batches values(1,'done',null)")
                db.commit()
            legacy=root/'automatic'
            folder=legacy/'batches'/'000001'
            folder.mkdir(parents=True)
            (folder/'attempt.json').write_text(json.dumps({'state':'submitted','zip_sha256':'old'}))
            with closing(sqlite3.connect(legacy/'queue.sqlite3')) as db:
                db.execute('create table batches(id integer,state text)')
                db.execute("insert into batches values(1,'active')")
                db.commit()
            with (patch.object(formula_queue,'enabled',return_value=True),
                  patch('oled_formulas.app_queue.Path.home',return_value=root),
                  patch('oled_formulas.formula_pilot.run') as chrome,
                  patch('playwright.sync_api.sync_playwright') as cdp):
                formula_queue.run({'catalog_path':str(root/'catalog.sqlite3')},control)
            self.assertEqual(json.loads((output/'app-status.json').read_text())['state'],'finished')
            chrome.assert_not_called()
            cdp.assert_not_called()

    def test_free_slot_refills_while_four_other_jobs_are_still_running(self):
        from threading import Event,Lock
        from oled_formulas import app_queue
        with tempfile.TemporaryDirectory() as tmp, closing(sqlite3.connect(':memory:')) as db:
            root=Path(tmp)
            db.executescript('create table batches(id integer primary key,state,reason);create table crops(batch,paper);')
            for n in range(1,7):
                db.execute("insert into batches values(?,'app_prepared',null)",(n,))
                db.execute("insert into crops values(?,'p')",(n,))
            five, sixth, lock = Event(),Event(),Lock()
            slots = {}
            def dispatch(client,config,folder,output,batch,active,slot,guard):
                with lock:
                    slots[batch]=slot
                    if len(slots)==5: five.set()
                    if batch==6: sixth.set()
                if batch==1:
                    self.assertTrue(five.wait(10))
                elif batch!=6:
                    self.assertTrue(sixth.wait(10))
                return {'state':'executed'}
            def collect(db,control,root,output,batch,receipt):
                app_queue.set_state(db,batch,'done')
            with (patch.object(app_queue,'dispatch_job',side_effect=dispatch),
                  patch.object(app_queue,'collect_job',side_effect=collect),
                  patch.object(app_queue,'Client'),patch('oled_formulas.formula_queue.recover_publications')):
                app_queue.run({'catalog_path':str(root/'catalog')},{'folder':tmp},db,root,lambda:True)
            self.assertEqual(set(slots.values()),set(range(5)))
            self.assertEqual(slots[1],slots[6])
            self.assertEqual(db.execute("select count(*) from batches where state='done'").fetchone(),(6,))

    def test_busy_inspector_needs_recent_same_session_evidence(self):
        from oled_formulas import app_queue as app
        from unittest.mock import Mock
        checks=app.AccountCheck()
        client=Mock()
        health={'pid':123,'ready':True,'active_browser_turns':2}
        client.health.return_value=health
        descriptor = dict(pid=321,partition='app',profile='production',control=dict(endpoint='loopback',token='test'))
        with (patch.object(app,'digest',return_value='bound'),patch.object(app,'read',return_value=descriptor),
              patch.object(app,'gate') as probe,
              patch.object(app.time,'monotonic',return_value=100) as clock):
            probe.return_value=app.INSPECTOR_BUSY
            self.assertEqual(checks.verify(client),app.INSPECTOR_BUSY)
            probe.return_value=None
            self.assertIsNone(checks.verify(client))
            token=checks.generation
            probe.return_value=app.INSPECTOR_BUSY
            clock.return_value=180
            self.assertEqual(checks.verify(client),app.INSPECTOR_BUSY)
            checks.completed(token,{'state':'executed','commands':1})
            descriptor.update(createdAt='later',surfaceTargets=['a new tab'])
            self.assertIsNone(checks.verify(client))
            probe.return_value='请登录'
            self.assertEqual(checks.verify(client),'请登录')
            checks.completed(token,{'state':'executed','commands':1})
            probe.return_value=app.INSPECTOR_BUSY
            self.assertEqual(checks.verify(client),app.INSPECTOR_BUSY)
            probe.return_value=None
            self.assertIsNone(checks.verify(client))
            health['pid']=456
            probe.return_value=app.INSPECTOR_BUSY
            self.assertEqual(checks.verify(client),app.INSPECTOR_BUSY)
