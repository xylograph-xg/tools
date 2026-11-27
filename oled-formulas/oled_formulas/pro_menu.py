"""Read one App-native effort menu per interval under the formula owner lock."""
from datetime import datetime
import json
from pathlib import Path
import time

from core.api import services__atomic_json as write

INTERVAL = 3 * 3600


def read_menu(folder, since, now):
    """Only read the menu from a fresh, session-verified App turn (6.2 slider layout)."""
    slider_file = next(folder.glob('*-effort-slider-visible.json'), None)
    session_file = next(folder.glob('*-session-verified.json'), None)
    if not slider_file or not session_file:
        return None
    menu = json.loads(slider_file.read_bytes())
    session = json.loads(session_file.read_bytes())
    trace = menu['traceId']
    captured = datetime.fromisoformat(menu['capturedAt'].replace('Z', '+00:00')).timestamp()
    if not (max(since, now-60) <= captured <= now and menu['version'] == 2
            and menu['checkpoint'] == 'effort-slider-visible' and trace == session['traceId']
            and session['checkpoint'] == 'session-verified' and folder.name.startswith(trace+'-')):
        return None
    sliders = menu['state']['effortSliders']
    if len(sliders) != 1:
        return None
    slider = sliders[0]
    if (slider['min'] != 0 or slider['max'] not in (3, 4) or (slider['power'] and slider['enabled'] is not True)
            or len(slider['ticks']) != slider['max'] + 1):
        return None
    # The native 6.2 helper uses index four for Pro. On its enabled power
    # slider, omitted lock attributes mean unlocked, as in the helper's cr().
    offered = False
    if slider['max'] == 4:
        locked = slider['ticks'][4]['locked']
        if type(locked) is not bool and not (locked is None and slider['power'] is True):
            return None
        offered = locked is not True
    return dict(pro_available=offered, trace=trace, captured_at=captured)


class ProMenu:
    def __init__(self, path, diagnostics):
        self.path, self.diagnostics = path, diagnostics
        self.retry_at = 0
        if path.exists():
            self.state = json.loads(path.read_bytes())
        else:
            self.state = dict(pro_available=False, source='user_reported',
                              next_probe_at=time.time()+INTERVAL, pro_slots=[])
            write(self.path, self.state)

    def observe(self, now):
        due = self.state['next_probe_at']
        if now < max(due, self.retry_at):
            return
        self.retry_at = now + 5
        try:
            # Select a single recent menu; a busy or idle App may have none yet.
            latest = max((path for path in self.diagnostics.glob('*/*-effort-slider-visible.json')
                          if max(due, now-60) <= path.stat().st_mtime <= now),
                         key=lambda path: path.stat().st_mtime, default=None)
            if latest:
                evidence = read_menu(latest.parent, due, now)
                if evidence is not None:
                    offered = evidence.pop('pro_available')
                    slots = self.state['pro_slots'].copy()
                    if offered:
                        candidate = next((slot for slot in range(5) if slot not in slots), None)
                        if candidate is not None:
                            slots.append(candidate)
                    state = dict(pro_available=offered, source='app_menu', next_probe_at=now+INTERVAL,
                                 pro_slots=slots, **evidence)
                    write(self.path, state)
                    self.state = state
        except (OSError, KeyError, ValueError, TypeError):
            # A partial capture has no evidentiary value. Keep serving non-Pro.
            return

    def retire_slot(self, slot, job):
        if slot in self.state['pro_slots']:
            state = dict(self.state, pro_slots=[i for i in self.state['pro_slots'] if i != slot],
                         last_failed_job=job)
            write(self.path, state)
            self.state = state
