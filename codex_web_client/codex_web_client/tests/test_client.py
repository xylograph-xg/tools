import concurrent.futures
import fcntl
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from codex_web_client.api import Client


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.client = Client(Path(self.temp.name) / "state")

    def evidence(self, text, *, command=False, message=None, completed=True, exited=True):
        c = self.client
        c._save("a", "sending")
        d = c._receipt_dir("a")
        d.mkdir(exist_ok=True)
        (d / "answer.txt").write_text(text)
        items = [{"type": "agent_message", "text": message if message is not None else text}]
        if command:
            items.insert(0, {"type": "command_execution", "exit_code": 0})
        events = [{"type": "item.completed", "item": i} for i in items]
        if completed:
            events.append({"type": "turn.completed"})
        (d / "events.jsonl").write_text("".join(json.dumps(e)+"\n" for e in events))
        if exited:
            (d / "cli-exit-0").touch()
        return Client(c.root).run_once()

    def test_finished_without_command(self):
        self.client.submit("a", "read", require_command=True)
        self.assertEqual(self.evidence("tool rejected")["reason"], "missing_successful_command")
        self.assertEqual(self.client.run_once()["state"], "idle")

    def test_incomplete(self):
        self.client.submit("a", "read")
        self.assertEqual(self.evidence("partial", completed=False)["state"], "review")

    def test_mixed_answer(self):
        self.client.submit("a", "read")
        self.assertEqual(self.evidence("one", message="another")["state"], "review")

    def test_unknown_exit(self):
        self.client.submit("a", "read")
        self.assertEqual(self.evidence("value", exited=False)["reason"], "interrupted_without_confirmed_exit")

    def test_recover_and_reuse(self):
        c = self.client
        c.submit("a", "x", expected="test", require_command=True)
        self.assertEqual(self.evidence("test", command=True)["state"], "verified")
        self.assertEqual(c.submit("a", "x", expected="test", require_command=True)["state"], "verified")
        with self.assertRaises(ValueError):
            c.submit("a", "changed")
        self.assertEqual(c.run_once()["state"], "idle")

    def test_json_accept(self):
        self.client.submit("a", "x", json_match={"paper": "A"})
        self.assertEqual(self.evidence('{"paper":"A","extra":2}')["state"], "verified")

    def test_json_reject_wrong_type_or_duplicate(self):
        for text in ['{"n":true}', '{"n":1,"n":1}', 'malformed']:
            with self.subTest(text=text):
                self.client.submit("a", "json", json_match={"n":1})
                self.assertEqual(self.evidence(text)["state"], "review")

    def test_lock_and_offline(self):
        c = self.client
        c.submit("a", "read")
        with (c.root/"worker.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.assertEqual(c.run_once()["state"], "busy")
        with patch.object(c, "health", return_value={"ready":False}), patch("shutil.which",return_value="/bin/false"):
            self.assertEqual(c.run_once()["state"], "unavailable")
        self.assertEqual(c.get("a")["state"], "queued")

    def test_concurrent_submission(self):
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            receipts = list(pool.map(lambda _:self.client.submit("a", "read"), range(12)))
        self.assertTrue(all(r["state"] == "queued" for r in receipts))
        self.assertEqual(self.client.counts(), {"queued": 1})

    def fake_cli(self, body):
        path = Path(self.temp.name) / "codex"
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o700)
        return str(path)

    def test_timeout_is_not_replayed(self):
        cli = self.fake_cli("sleep 10")
        c = self.client
        c.timeout = 1
        c.submit("a", "read", require_command=True)
        with patch.object(c, "health", return_value={"ready":True}), patch("shutil.which", return_value=cli):
            self.assertEqual(c.run_once()["reason"], "TimeoutExpired")
            self.assertEqual(c.run_once()["state"], "idle")

    def test_exited_zero_without_events(self):
        cli = self.fake_cli("exit 0")
        c = self.client
        c.submit("a", "read", require_command=True)
        with patch.object(c, "health", return_value={"ready":True}), patch("shutil.which", return_value=cli):
            self.assertEqual(c.run_once()["state"], "review")
            self.assertEqual(c.run_once()["state"], "idle")

    def test_backoff_persists_across_workers_and_clears_on_success(self):
        c = self.client
        c.submit("a", "x")
        c.submit("b", "y")
        c._save("a", "review", "unknown")
        c = Client(c.root)
        self.assertEqual(c.run_once()["state"], "cooldown")
        self.assertEqual(c.get("b")["state"], "queued")
        c._save("b", "answered", answer="y")
        self.assertEqual(c.dispatch_status()["consecutive_reviews"], 0)

    def test_guarded_images_frozen_select_exact_job(self):
        c = self.client
        image = Path(self.temp.name)/'page.jpg'
        image.write_bytes(b'original')
        c.submit('older','other')
        c.submit('job','read',images=[image],guarded=True)
        with patch.object(c,'health',return_value={'ready':True}), patch('shutil.which',return_value='/bin/false'):
            self.assertEqual(c.run_once(key='job')['reason'],'send_guard_required')
            self.assertEqual(c.run_once(key='job',before_send=lambda key:'paused')['reason'],'paused')
            self.assertEqual(c.get('job')['state'],'queued')
            image.write_bytes(b'changed')
            self.assertEqual(c.run_once(key='job',before_send=lambda key:None)['reason'],'frozen_image_changed')
        self.assertEqual(c.get('older')['state'],'queued')

    def test_pro_then_extra_high_then_high_with_persistent_quota_evidence(self):
        c = self.client
        c.submit("a", "read", guarded=True)
        for model,effort,label in [("gpt-6-pro","max","GPT-6 Pro"),("gpt-6.2-sol","xhigh","Extra High"),
                                   ("gpt-6.2-sol","high","High")]:
            failure = {"type":"turn.failed","error":{"message":f"You reached the limit for {label}. The message was not sent."}}
            cli = self.fake_cli("case \"$*\" in *'model_reasoning_effort="+chr(34)+effort+chr(34)
                                +" -m chatgpt-web/"+model+"'*) ;; *) exit 9;; esac\n"
                                +"echo '"+json.dumps(failure)+"'\nexit 1")
            c = Client(c.root)
            with patch.object(c,"health",return_value={"ready":True}),patch("shutil.which",return_value=cli):
                receipt = c.run_once(key="a",before_send=lambda key:None,pro_first=True)
                self.assertEqual(receipt["reason"],"model_quota_before_send")
                self.assertEqual(c.get("a")["effort"],effort)
        with patch.object(c,"health",return_value={"ready":True}),patch("shutil.which",return_value=cli):
            self.assertEqual(c.run_once(key="a",before_send=lambda key:None,pro_first=True)["reason"],"all_model_tiers_exhausted")
        self.assertEqual(c.get("a")["state"],"queued")
        self.assertEqual(len(list(c._receipt_dir("a").glob("attempt-*/events.jsonl"))),3)

    def test_general_limit_and_uncertain_submission_never_retry_job(self):
        from codex_web_client.api import _quota_error, PRO_FIRST
        path = Path(self.temp.name)/"events.jsonl"
        def check(message):
            path.write_text(json.dumps({"type":"turn.failed","error":{"message":message}}))
            return _quota_error(path,PRO_FIRST[0])
        self.assertIsNone(check("GPT-6 Pro attachment limit reached. The message was not sent."))
        self.assertIsNone(check("GPT-6 Pro may have reached the usage limit."))
        self.assertFalse(check("You've reached the GPT-6 Pro usage limit.")[1])

    def test_app_upload_quota_blocks_next_dispatch_across_models_and_restart(self):
        import time
        failure = {'type':'turn.failed','error':{'message':'upload_quota_exceeded'}}
        cli = self.fake_cli("echo '"+json.dumps(failure)+"'\nexit 1")
        c = self.client
        c.submit('a','read',guarded=True)
        c.submit('b','read',guarded=True)
        with patch.object(c,'health',return_value={'ready':True}),patch('shutil.which',return_value=cli):
            self.assertEqual(c.run_once(key='a',before_send=lambda key:None,pro_first=True)['reason'],
                             'app_account_or_attachment_quota')
        result = Client(c.root).run_once(key='b',before_send=lambda key:None,pro_first=True)
        self.assertEqual(result['state'],'cooldown')
        self.assertGreater(result['next_dispatch_at'],time.time()+895)

    def test_five_parallel_keys_keep_exclusive_job_and_slot_locks(self):
        from threading import Barrier, Event
        c = self.client
        for key in 'abcdef':
            c.submit(key,'read',guarded=True)
        ready, release = Barrier(6), Event()
        def guard(key):
            ready.wait(timeout=10)
            release.wait(timeout=10)
            return 'paused'
        with (patch.object(c,'health',return_value={'ready':True,'active_browser_turns':0}),
              patch('shutil.which',return_value='/bin/false'),
              concurrent.futures.ThreadPoolExecutor(5) as workers):
            futures = [workers.submit(c.run_once,key=k,parallel_slot=n,before_send=guard)
                       for n,k in enumerate('abcde')]
            try:
                ready.wait(timeout=10)
                self.assertEqual(c.run_once(key='f',parallel_slot=0,before_send=guard)['state'],'busy')
                self.assertEqual(c.run_once()['state'],'busy')
            finally:
                release.set()
            self.assertTrue(all(f.result()['reason']=='paused' for f in futures))
        with patch.object(c,'health',return_value={'ready':True,'active_browser_turns':5}):
            self.assertEqual(c.run_once(key='a',parallel_slot=0,before_send=lambda k:None)['state'],'unavailable')
        self.assertEqual(c.counts(),{'queued':6})
        with (c._receipt_dir('a')/'worker.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            self.assertEqual(c.run_once(key='a',parallel_slot=2,before_send=guard)['state'],'busy')

    def test_parallel_success_keeps_another_jobs_quota_cooldown(self):
        c=self.client
        for key in 'ab':
            c.submit(key,'read',guarded=True)
        c._save('a','review','quota',minimum_delay=900)
        deadline=c.dispatch_status()['next_dispatch_at']
        c._save('b','executed',parallel=True)
        self.assertEqual(c.dispatch_status()['next_dispatch_at'],deadline)

    def test_absent_pro_starts_extra_high_then_high_on_unsent_tier_quota(self):
        c = self.client
        c.submit('job','read',guarded=True)
        for effort, label in [('xhigh','Extra High'),('high','High')]:
            event = dict(type='turn.failed',error={'message':f'{label} quota exhausted. The message was not sent.'})
            cli = self.fake_cli("echo '"+json.dumps(event)+"'\nexit 1")
            with patch.object(c,'health',return_value={'ready':True}),patch('shutil.which',return_value=cli):
                result = c.run_once(key='job',before_send=lambda _:None,pro_first=True,allow_pro=False)
            self.assertEqual(result['reason'],'model_quota_before_send')
            self.assertEqual(c.get('job')['effort'],effort)
        with patch.object(c,'health',return_value={'ready':True}),patch('shutil.which',return_value=cli):
            self.assertEqual(c.run_once(key='job',before_send=lambda _:None,pro_first=True,
                                        allow_pro=False)['reason'],'all_model_tiers_exhausted')
