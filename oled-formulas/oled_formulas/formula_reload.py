"""Recover the same GET after repeated observations of a stalled, empty document."""
import hashlib
import json
import os
from pathlib import Path
import time

from core.api import services__atomic_json as write
from browser.api import browser_inventory__enumerate_pages as enumerate_pages
from .formula_pilot import exact_user_turn, saved_formula_response
from browser.api import shared_page_health__snapshot_page as snapshot_page
from browser.api import shared_pool_store__load_pool as load_pool
from browser.api import shared_window_owner__require_slot as require_slot


def stalled_load(check, entry, minimum_age):
    load = check.get('page_load') or {}
    started = load.get('started_at')
    if (not check.get('inspection_complete') or load.get('ready_state')!='loading'
            or load.get('navigation_type')!='reload' or not isinstance(started,(int,float))
            or check['checked_at']-started<minimum_age or (check.get('draft') or '').strip()
            or any(check.get(k) for k in ('composer_available','user_texts','answer_element_count',
                'attachments','uploading','streaming','login','verification','quota','errors','account_ui_blocked'))):
        return None
    url = check.get('url')
    if entry.get('state')=='ready_blank' and url=='https://chatgpt.com/':
        saved = entry.get('previous_saved_response') or {}
    elif entry.get('state')=='ready' and url and url==entry.get('conversation_url'):
        saved = entry
    else:
        return None
    return (check['target_id'],url,started,saved.get('active_paper_id'),saved.get('raw_sha256'))


def recover_load(config,control,db,browser,checks,pool,output,observed,active):
    policy = config.get('web_cards',{}).get('shared_window',{}).get('health_repair',{})
    if not policy.get('enabled'):
        return
    minimum_age = policy['startup_stalled_after_seconds']
    current = {}
    for check in checks:
        tid = check['target_id']
        entry = pool['windows'].get(tid,{})
        signature = stalled_load(check,entry,minimum_age)
        if not signature:
            continue
        first = observed.get(signature,check['checked_at'])
        current[signature] = first
        if check['checked_at']-first<policy['check_interval_seconds']:
            continue
        saved = entry if entry.get('state')=='ready' else entry.get('previous_saved_response',{})
        identity = hashlib.sha256(json.dumps([tid,check['url'],signature[3:]]).encode()).hexdigest()
        journal = output/'page-load-recovery'/(identity+'.json')
        if journal.exists() or not saved_formula_response(control,tid,saved):
            continue
        if db.execute("select 1 from batches where state='active' limit 1").fetchone():
            continue
        try:
            require_slot(config,browser,tid)
            page = enumerate_pages(browser)['pages'].get(tid)
            if page is None:
                continue
            live = snapshot_page(tid,page)
            require_slot(config,browser,tid)
        except (ValueError, RuntimeError, TimeoutError, KeyError):
            continue
        base = Path(config['catalog_path']).parent
        if (not active() or page.url!=check['url'] or load_pool(base/'gpt-window-pool.json')['windows'].get(tid)!=entry
                or stalled_load(live,entry,minimum_age)!=signature):
            continue
        receipt = dict(state='intent',target=tid,url=page.url,owner=os.getpid(),job=signature[3],
                       raw_sha256=signature[4],load_started_at=signature[2],first_observation=first,
                       checked_at=live['checked_at'],requested_at=time.time())
        write(journal,receipt)
        try:
            page.goto(receipt['url'],wait_until='commit',timeout=12000)
            receipt.update(state='navigation_returned',observed_url=page.url)
        except Exception as exc:
            receipt.update(state='navigation_unconfirmed',error=str(exc)[:350])
        write(journal,dict(receipt,finished_at=time.time()))
    observed.clear()
    observed.update(current)


def reconcile_saved_slots(config, control, db, browser, pw, checks, pool, output, reserved, active):
    """Finish an interrupted pool update only while the original answer is still on its target."""
    import re
    from core.api import control__read_record as read
    from browser.api import shared_pool_store__save_pool as save_pool
    from browser.api import shared_window_owner__require_reusable as require_reusable
    from browser.api import web_page_observer__responsive_lock as responsive_lock
    path = Path(config['catalog_path']).parent/'gpt-window-pool.json'
    for check in checks:
        tid = check['target_id']
        entry = pool['windows'].get(tid,{})
        if (tid in reserved or entry.get('state')!='busy' or entry.get('kind')!='formula_only'
                or not check.get('inspection_complete') or not check.get('answer_texts')
                or not check.get('account_ready') or (check.get('draft') or '').strip() or any(check.get(k) for k in
                        ('attachments','uploading','streaming','login','verification','quota','errors'))):
            continue
        job = entry.get('active_paper_id','')
        if job=='temporary-pilot':
            folder = Path(control['folder'])/'temporary-pilot'
        else:
            match = re.fullmatch(r'formula-display-([1-9][0-9]*)',job)
            if not match or db.execute('select state from batches where id=?',(int(match[1]),)).fetchone()!=('done',):
                continue
            folder = output/'batches'/f'{int(match[1]):06d}'
        receipt = read(folder/'attempt.json')
        candidate = dict(entry,state='ready',conversation_url=receipt.get('url'),
                         raw_path=str(folder/'response.txt'),raw_sha256=receipt.get('raw_sha256'))
        if not candidate['conversation_url'] or check.get('url')!=candidate['conversation_url']:
            continue
        try:
            with responsive_lock(pw,timeout=1):
                current=load_pool(path)
                if current['windows'].get(tid)!=entry or not saved_formula_response(control,tid,candidate):
                    continue
                require_slot(config,browser,tid)
                page=enumerate_pages(browser)['pages'][tid]
                if not active() or page.url!=candidate['conversation_url']:
                    continue
                fresh=snapshot_page(tid,page)
                if (not fresh.get('inspection_complete') or not fresh.get('account_ready')
                        or not exact_user_turn(page,receipt['prompt']).get('exact')
                        or (fresh.get('draft') or '').strip()
                        or any(fresh.get(k) for k in ('attachments','uploading','streaming','login','verification','quota','errors'))):
                    continue
                require_reusable(page,candidate)
                require_slot(config,browser,tid)
                if active() and page.url==candidate['conversation_url']:
                    current['windows'][tid]=candidate
                    save_pool(path,current)
        except (ValueError,RuntimeError,TimeoutError,OSError):
            continue


def completed_home(control, db, output, tid, entry):
    """Bind the archived result to this target and its actual published batch."""
    import re
    from core.api import control__read_record as read
    from .formula_results import frozen_pages
    if entry.get('kind') != 'formula_only':
        return None
    job = entry.get('active_paper_id','')
    saved = dict(entry)
    if job == 'temporary-pilot' and entry.get('state') == 'busy':
        folder = Path(control['folder'])/'temporary-pilot'
        rec = read(folder/'attempt.json')
        saved.update(raw_path=str(folder/'response.txt'), raw_sha256=rec.get('raw_sha256'),
                     conversation_url=rec.get('url'))
    else:
        match = re.fullmatch(r'formula-display-([1-9][0-9]*)',job)
        if not match or entry.get('state') not in ('ready','busy'):
            return None
        n = int(match[1])
        if db.execute('select state from batches where id=?',(n,)).fetchone()!=('done',):
            return None
        folder = output/'batches'/f'{n:06d}'
        frozen_pages(db,folder,n)
        if entry['state']=='busy':
            rec = read(folder/'attempt.json')
            saved.update(raw_path=str(folder/'response.txt'),raw_sha256=rec['raw_sha256'],conversation_url=rec['url'])
    return saved if saved_formula_response(control,tid,saved) else None


def adopt_completed_homes(config,control,db,browser,pw,checks,pool,output,reserved,observed,active):
    """Record two consecutive empty observations before reconciling a fully archived formula slot."""
    from core.api import control__read_record as read
    from browser.api import shared_pool_store__mark_verified_blank as mark_blank
    from browser.api import shared_pool_store__save_pool as save_pool
    from browser.api import web_page_observer__responsive_lock as responsive_lock
    from browser.api import web_card_pool__shared_submission_status as channel
    from .formula_dispatch import empty_formula_home
    import zipfile
    path = Path(config['catalog_path']).parent/'gpt-window-pool.json'
    checked = {}
    from .entry_retry import release_path
    pending = set()
    for n, in db.execute("select id from batches where state in ('active','held','awaiting_answer','review','publishing')"):
        receipt = read(output/'batches'/f'{n:06d}'/'attempt.json')
        from .unavailable_slots import released
        if receipt.get('state')=='submitted' and released(output/'batches'/f'{n:06d}',f'formula-display-{n}',receipt.get('window_target')):
            continue
        if receipt.get('state') not in ('raw_saved','upload_preparation') or (
                receipt.get('state')=='upload_preparation' and not
                release_path(output/'batches'/f'{n:06d}').is_file()):
            pending.add(receipt.get('window_target'))
    for check in checks:
        tid = check['target_id']
        entry = pool['windows'].get(tid,{})
        if (tid in reserved or tid in pending or not empty_formula_home(check)
                or entry.get('kind')!='formula_only' or entry.get('state') not in ('ready','busy')):
            continue
        load = check.get('page_load') or {}
        if load.get('ready_state')!='complete' or not load.get('started_at') or not check.get('account_authenticated'):
            continue
        key = (tid,entry.get('active_paper_id'),entry.get('raw_sha256'),check['url'],load['started_at'])
        first = observed.get(key,check['checked_at'])
        checked[key] = first
        if check['checked_at']-first<30:
            continue
        try:
            with responsive_lock(pw,timeout=1):
                current=load_pool(path)
                if current['windows'].get(tid)!=entry or not active() or not channel(config)['allowed']:
                    continue
                saved=completed_home(control,db,output,tid,entry)
                if saved is None:
                    continue
                require_slot(config,browser,tid)
                page=enumerate_pages(browser)['pages'][tid]
                live=snapshot_page(tid,page)
                require_slot(config,browser,tid)
                if (not empty_formula_home(live) or live.get('url')!=check['url'] or page.url!=check['url']
                        or not live.get('account_authenticated') or (live.get('page_load') or {}).get('ready_state')!='complete'
                        or (live.get('page_load') or {}).get('started_at')!=load['started_at']
                        or not active() or not channel(config)['allowed']):
                    continue
                job=entry['active_paper_id']
                proof=output/'completed-home-recovery'/f'{job}-{tid}.json'
                write(proof,dict(job=job,target=tid,owner=os.getpid(),first=first,second=check['checked_at'],
                                 final=live['checked_at'],previous=saved,live_url=live['url'],document_start=load['started_at']))
                mark_blank(saved)
                saved['never_submitted']=False
                saved['completed_home_proof']=str(proof)
                current['windows'][tid]=saved
                save_pool(path,current)
        except (OSError,ValueError,RuntimeError,KeyError,TimeoutError,zipfile.BadZipFile) as exc:
            write(output/'completed-home-recovery'/(tid+'-error.json'),dict(at=time.time(),reason=str(exc)[:450]))
    observed.clear()
    observed.update(checked)
