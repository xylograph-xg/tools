from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import unittest

from oled_formulas.pro_menu import INTERVAL, ProMenu


class ProMenuTests(unittest.TestCase):
    def test_single_window_cadence_across_restart_and_preservation(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            state = root/'policy.json'
            traces = root/'captures'
            def capture(trace, stamp, maximum, lock):
                folder = traces/(trace+'-turn')
                folder.mkdir(parents=True)
                rec = dict(version=2, traceId=trace, capturedAt=datetime.fromtimestamp(stamp, timezone.utc).isoformat())
                (folder/'04-session-verified.json').write_text(json.dumps(dict(rec, checkpoint='session-verified')))
                menu = folder/'07-effort-slider-visible.json'
                slider = dict(min=0, max=maximum, power=True, enabled=True,
                              ticks=[dict(locked=None)]*maximum+[dict(locked=lock)])
                menu.write_text(json.dumps(dict(rec, checkpoint='effort-slider-visible',state=dict(effortSliders=[slider]))))
                os.utime(menu,(stamp,stamp))
            policy = ProMenu(state,traces)
            due = policy.state['next_probe_at']
            capture('old', due-1, 4, False)
            policy.observe(due)
            self.assertEqual(policy.state['source'], 'user_reported')
            capture('one', due+1, 4, False)
            capture('two', due+3, 3, None)
            policy.observe(due+5)
            self.assertEqual((policy.state['trace'],policy.state['pro_slots']), ('two',[]))
            policy = ProMenu(state,traces)
            second = policy.state['next_probe_at']
            self.assertEqual(second, due+5+INTERVAL)
            capture('three', second+0.5, 4, None)
            policy.observe(second-1)
            self.assertEqual(policy.state['trace'],'two')
            policy.observe(second+1)
            self.assertEqual(policy.state['pro_slots'],[0])
            capture('four', second+INTERVAL+2, 4, True)
            policy.observe(second+INTERVAL+3)
            self.assertFalse(policy.state['pro_available'])
            self.assertEqual(policy.state['pro_slots'],[0])
            policy.retire_slot(0,'failed')
            self.assertEqual(ProMenu(state,traces).state['pro_slots'],[])
