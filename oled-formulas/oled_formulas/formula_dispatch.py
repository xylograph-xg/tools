"""Dispatch OLED batches on distinct registered tabs of the single resident connection."""
import asyncio
import os
import re
import sqlite3
import time
from pathlib import Path

from core.api import control__read_record as read, services__atomic_json as write
from browser.api import account_readiness__recheck as account_readiness_recheck
from browser.api import browser_inventory__enumerate_pages as enumerate_pages
from .formula_pilot import image_warning, save_observation
from . import attachment_gate, entry_retry
from browser.api import owner_work_lane__OwnerWorkLane as OwnerWorkLane
from browser.api import shared_page_health__snapshot_pages as _snapshot_pages
from browser.api import shared_pool_store__load_pool as load_pool
from browser.api import shared_window_owner__require_slot as require_slot
from browser.api import web_card_pool__shared_submission_status as shared_submission_status

PARALLEL = 5


def observe(config, browser, output):
    base = Path(config['catalog_path']).parent
    reg = read(base/'shared-gpt-window.json')
    inventory = enumerate_pages(browser)
    if inventory.get('complete') is False:
        raise RuntimeError('专窗盘点未完成：' + '，'.join(inventory.get('errors', []))[:300])
    pages = inventory['pages']
    owned = {}
    for slot in reg.get('slots', []):
        tid = slot.get('target_id')
        if tid in pages:
            try:
                require_slot(config,browser,tid)
            except (ValueError,RuntimeError,TimeoutError):
                continue
            owned[tid] = pages[tid]
    checks = list(_snapshot_pages(owned).values())
    confirmed = []
    for check in checks:
        try:
            require_slot(config,browser,check['target_id'])
        except (ValueError,RuntimeError,TimeoutError):
            continue
        confirmed.append(check)
        check.update(window_observed=True,window_id=reg['window_id'],window_checked_at=time.time())
    pool = load_pool(base/'gpt-window-pool.json')
    for page in confirmed:
        tid = page['target_id']
        job = pool['windows'].get(tid,{}).get('active_paper_id') or ''
        match = re.fullmatch(r'formula-display-([1-9][0-9]*)',job)
        if not match or not page.get('inspection_complete') or not image_warning(page.get('image_health')):
            continue
        folder = output/'batches'/f'{int(match[1]):06d}'
        receipt = read(folder/'attempt.json')
        from .formula_results import bound_warning
        if (receipt.get('state') in ('submitted','raw_saved') and receipt.get('temporary') is True
                and receipt.get('zip_sha256') and not bound_warning(folder,int(match[1])) and receipt.get('window_target')==tid and
                receipt.get('url') and receipt['url']==page['url'] and receipt.get('job_id')==job):
            write(folder/'observed-image-warning.json',dict(target=tid,job_id=job,url=page['url'],
                  zip_sha256=receipt['zip_sha256'],checked_at=page['checked_at'],image_health=page['image_health']))
            page['new_saved_image_warning'] = receipt['state']=='raw_saved'
    save_observation(output,reg['window_id'],pool,confirmed)
    channel = read(base/'web-channel-control.json').get('chatgpt',{})
    if not channel.get('manual_verification_required'):
        from browser.api import shared_page_repair__manual_block as _manual_block
        for page in confirmed:
            if page.get('inspection_complete') and (page.get('login') or page.get('verification')):
                _manual_block(base,page['target_id'])
                break
    account_readiness_recheck(base,confirmed,formula_window=True)
    if shared_submission_status(config)['allowed']:
        from browser.api import web_card_transport__Router as Router
        from browser.api import web_card_pool__record_channel_failure as record_channel_failure
        for page in confirmed:
            if page.get('quota') and page.get('inspection_complete'):
                tid = page['target_id']
                record_channel_failure(Router(base,policy=config['web_cards']),RuntimeError('网页额度受限'),
                                       owned[tid],lambda:require_slot(config,browser,tid))
                break
    return confirmed


def available(checks, pool, reserved, cooldown, now):
    """The selected tab is only a candidate; the pilot checks it again before every mutation."""
    candidates = []
    for page in checks:
        tid = page['target_id']
        if tid in reserved or cooldown.get(tid,0)>now:
            continue
        entry = pool['windows'].get(tid,{})
        if (not page.get('inspection_complete') or not page.get('account_ready')
                or (page.get('draft') or '').strip() or not 0<=now-page['checked_at']<=60 or any(page.get(k) for k in
                    ('attachments','streaming','uploading','login','verification','quota'))):
            continue
        blank = entry.get('state') in ('ready_blank','opening')
        archived = (entry.get('state')=='ready' and entry.get('kind')=='formula_only'
                    and entry.get('conversation_url') and page.get('url')==entry['conversation_url'])
        if blank or archived:
            candidates.append((not blank,tid))
    return [tid for _,tid in sorted(candidates)]


def idle_effort_candidate(check, entry, *, held=False):
    control = check.get('effort_control') or {}
    return ((entry.get('state') in ('ready','ready_blank') or (held and entry.get('state')=='busy')) and
            (entry.get('kind')=='formula_only' or entry.get('state')=='ready_blank') and
            check.get('inspection_complete') and check.get('account_ready') and
            check.get('url') in ('https://chatgpt.com/','https://chatgpt.com/?temporary-chat=true') and
            control.get('effort') and control['effort']!='high' and not control.get('disabled') and
            not (check.get('draft') or '').strip() and not any(check.get(k) for k in
                ('user_texts','answer_element_count','attachments','uploading','streaming','login','verification','quota','errors')))


def held_before_send(db, output, entry, tid):
    job = entry.get('active_paper_id') or ''
    match = re.fullmatch(r'formula-display-([1-9][0-9]*)',job)
    if entry.get('kind')!='formula_only' or not match:
        return False
    batch = int(match[1])
    if db.execute('select state from batches where id=?',(batch,)).fetchone()!=('held',):
        return False
    folder = output/'batches'/f'{batch:06d}'
    attempt = read(folder/'attempt.json')
    status = read(folder/'status.json')
    packet = read(folder/'packet.json')
    return (attempt.get('state')=='upload_preparation' and not attempt.get('at') and not attempt.get('url')
            and attempt.get('temporary') is True and attempt.get('job_id')==job and attempt.get('window_target')==tid
            and packet.get('batch')==batch and packet.get('sha256') and packet['sha256']==attempt.get('zip_sha256')
            and status.get('state')=='blocked' and (status.get('last') or {}).get('target')==tid)


def empty_formula_home(check):
    return (check.get('inspection_complete') and check.get('account_ready') and check.get('composer_available')
            and check.get('url') in ('https://chatgpt.com/', 'https://chatgpt.com/?temporary-chat=true')
            and not (check.get('draft') or '').strip()
            and not any(check.get(key) for key in ('attachments','uploading','streaming','user_texts','answer_texts',
                        'answer_element_count','errors','quota','login','verification','account_ui_blocked')))


def historical_slot_receipt(control,output,batch,state,tid,receipt,original_release=None):
    """A prior assignment ceases to reserve this tab only after verifiable local archiving."""
    from .formula_only import digest
    from .formula_pilot import saved_formula_response
    folder=output/'batches'/f'{batch:06d}'
    job=f'formula-display-{batch}'
    packet=read(folder/'packet.json')
    if (state not in ('held','review') or receipt.get('window_target')!=tid or receipt.get('job_id')!=job
            or receipt.get('temporary') is not True or packet.get('batch')!=batch or not packet.get('sha256')
            or packet['sha256']!=receipt.get('zip_sha256') or not (folder/'batch.zip').is_file()
            or digest(folder/'batch.zip')!=packet['sha256']):
        return False
    if receipt.get('state')=='submitted' and state=='review':
        from .unavailable_slots import released
        return released(folder,job,tid)
    if receipt.get('state')=='raw_saved':
        saved=dict(active_paper_id=job,kind='formula_only',conversation_url=receipt.get('url'),
                   raw_sha256=receipt.get('raw_sha256'),raw_path=str(folder/'response.txt'))
        return saved_formula_response(control,tid,saved)
    if state!='held' or receipt.get('state')!='upload_preparation' or any(
            key in receipt for key in ('at','url','click_settings')):
        return False
    record=read(original_release or entry_retry.release_path(folder))
    evidence=record.get('evidence') or {}
    before=evidence.get('pool_before') or {}
    page=record.get('page') or {}
    status=read(folder/'status.json')
    return (evidence.get('job')==job and evidence.get('target')==tid and evidence.get('attempt')==receipt
            and evidence.get('packet')==packet and evidence.get('status')==status and status.get('state')=='blocked'
            and (status.get('last') or {}).get('target')==tid and before.get('kind')=='formula_only'
            and before.get('active_paper_id')==job and before.get('state')=='busy' and record.get('owner')
            and page.get('target_id')==tid and empty_formula_home(page))


def release_unsent_slots(config,control,db,browser,pw,checks,pool,output,active):
    """Release a clean slot after a frozen pre-click failure, leaving the held batch intact."""
    from browser.api import shared_page_health__snapshot_page as snapshot_page
    from browser.api import shared_pool_store__save_pool as save_pool
    from browser.api import shared_window_owner__require_reusable as require_reusable
    from browser.api import web_page_observer__responsive_lock as responsive_lock
    from .formula_only import digest
    from .formula_pilot import saved_formula_response
    pool_path = Path(config['catalog_path']).parent/'gpt-window-pool.json'
    for check in checks:
        tid = check['target_id']
        entry = pool['windows'].get(tid,{})
        if entry.get('state')!='busy' or not empty_formula_home(check) or not held_before_send(db,output,entry,tid):
            continue
        job = entry['active_paper_id']
        batch = int(job.split('-')[-1])
        folder = output/'batches'/f'{batch:06d}'
        try:
            with responsive_lock(pw,timeout=1):
                current = load_pool(pool_path)
                if current['windows'].get(tid)!=entry or not held_before_send(db,output,entry,tid):
                    continue
                previous = entry.get('previous_saved_response') or {}
                receipt = read(folder/'attempt.json')
                if ('click_settings' in receipt or not saved_formula_response(control,tid,previous)
                        or receipt['zip_sha256']!=digest(folder/'batch.zip')
                        or not receipt.get('prompt','').endswith(receipt['zip_sha256'])):
                    continue
                others = db.execute("select id,state from batches where id!=? and state in ('active','held','awaiting_answer','review','publishing')",(batch,))
                conflict=False
                for other,state in others:
                    prior=read(output/'batches'/f'{other:06d}'/'attempt.json')
                    if prior.get('window_target')==tid and not historical_slot_receipt(control,output,other,state,tid,prior):
                        conflict=True
                        break
                if conflict:
                    continue
                require_slot(config,browser,tid)
                page = enumerate_pages(browser)['pages'][tid]
                live = snapshot_page(tid,page)
                if not empty_formula_home(live) or live['url']!=check['url']:
                    continue
                blank = dict(entry,state='ready_blank')
                del blank['kind'], blank['active_paper_id']
                require_reusable(page,blank,allow_temporary_home=True)
                require_slot(config,browser,tid)
                final = snapshot_page(tid,page)
                require_slot(config,browser,tid)
                if (not active() or not shared_submission_status(config)['allowed'] or not empty_formula_home(final)
                        or final['url']!=live['url'] or page.url!=live['url'] or read(folder/'attempt.json')!=receipt):
                    continue
                archive = entry_retry.release_path(folder)
                evidence = dict(job=job,target=tid,attempt=receipt,pool_before=entry,
                                status=read(folder/'status.json'),packet=read(folder/'packet.json'))
                if archive.exists():
                    if read(archive).get('evidence')!=evidence:
                        continue
                else:
                    write(archive,dict(evidence=evidence,page=final,checked_at=time.time(),owner=os.getpid()))
                blank['unsent_slot_release'] = str(archive)
                current['windows'][tid] = blank
                save_pool(pool_path,current)
        except (OSError,ValueError,KeyError,RuntimeError,TimeoutError) as exc:
            write(folder/'slot-release-check.json',dict(time=time.time(),reason=str(exc)[:400],target=tid))


def prepare_idle_effort(config, control, db, browser, checks, pool, reserved, retry_after, output, active):
    from .formula_pilot import saved_formula_blank
    from .formula_only import digest
    from browser.api import gpt_model_policy__set_composer_high as set_composer_high
    from browser.api import shared_page_health__snapshot_page as snapshot_page
    for check in checks:
        tid = check['target_id']
        entry = pool['windows'].get(tid,{})
        if tid in reserved or retry_after.get(tid,0)>time.monotonic():
            continue
        held = entry.get('state')=='busy' and held_before_send(db,output,entry,tid)
        if not idle_effort_candidate(check,entry,held=held):
            continue
        retry_after[tid] = time.monotonic()+120
        try:
            if entry['state']=='ready':
                job = entry.get('active_paper_id') or ''
                match = re.fullmatch(r'formula-display-([1-9][0-9]*)',job)
                if not match:
                    continue
                folder = output/'batches'/f'{int(match[1]):06d}'
                raw = folder/'response.txt'
                record = read(folder/'attempt.json')
                if (record.get('state')!='raw_saved' or record.get('window_target')!=tid or
                        record.get('job_id')!=job or record.get('url')!=entry.get('conversation_url') or
                        str(raw)!=entry.get('raw_path') or not raw.is_file() or
                        not record.get('raw_sha256')==entry.get('raw_sha256')==digest(raw)):
                    continue
            elif not held and not entry.get('never_submitted') and not saved_formula_blank(dict(control,batch=True),tid,entry):
                continue
            require_slot(config,browser,tid)
            page = enumerate_pages(browser)['pages'][tid]
            live = snapshot_page(tid,page)
            if not active():
                return
            if live.get('url')!=check['url'] or not idle_effort_candidate(live,entry,held=held):
                continue
            require_slot(config,browser,tid)
            page._web_gpt_background = True
            def guard():
                if not active() or page.url!=live['url']:
                    raise ValueError('公式任务已暂停或页面地址变化')
                require_slot(config,browser,tid)
            set_composer_high(page,guard)
            guard()
            result = snapshot_page(tid,page)
            if (not result.get('inspection_complete') or result.get('url')!=live['url'] or
                    (result.get('effort_control') or {}).get('effort')!='high'):
                raise ValueError('关闭菜单后输入框未显示 High')
            receipt = dict(state='verified',previous=live['effort_control'],current=result['effort_control'])
        except Exception as exc:
            receipt = dict(state='pending',reason=str(exc)[:400])
        write(output/'idle-model-checks'/(tid+'.json'),dict(target=tid,time=time.time(),**receipt))
        return


def resume_visible_answers(db, output, checks):
    for batch, in db.execute("select id from batches where state='review' and reason=?",('原会话连续半小时无回答节点，等待原页出现正文',)).fetchall():
        receipt=read(output/'batches'/f'{batch:06d}'/'attempt.json')
        if receipt.get('state')!='submitted':
            continue
        page=next((c for c in checks if c['target_id']==receipt.get('window_target')), {})
        if (page.get('inspection_complete') and page.get('url')==receipt.get('url') and
                (page.get('streaming') or any(page.get('answer_texts',[]))) and
                not any(page.get(k) for k in ('login','verification','quota'))):
            with db:
                db.execute("update batches set state='awaiting_answer',reason=null where id=?",(batch,))
                db.execute('insert or replace into pending_collections values(?,?)',(batch,time.time()))


def index_paper_order(db):
    """Keep frozen batches together and visit the earliest planned paper group first."""
    db.execute('create temp table if not exists formula_paper_order(batch integer primary key, first_batch integer)')
    db.execute('delete from temp.formula_paper_order')
    db.execute("""with firsts as (select paper,min(batch) first_batch from crops group by paper)
        insert into temp.formula_paper_order
        select c.batch,min(f.first_batch) from crops c join firsts f using(paper) group by c.batch""")
    db.commit()


def dispatch(config, control, db, output, pw, browser, active, process, legacy):
    base = Path(config['catalog_path']).parent
    workers = {}
    stages = {}
    cooldown = {}
    effort_retry = {}
    stalled_loads = {}
    completed_homes = {}
    recovery_timers = {}
    checks = []
    next_check = next_legacy = 0
    observation_error = None
    observe_seconds = None
    index_paper_order(db)
    state_path = output/'status.json'
    traces = entry_retry.EntryTraces(base/'upload-attempt-events.jsonl')
    gate_path = output/'attachment-backoff.json'
    gate = attachment_gate.load_gate(output,db)

    def store_gate(value):
        nonlocal gate
        write(gate_path,value)
        gate=value


    last_status = None
    last_write = 0

    def progress(state, **fields):
        nonlocal last_status, last_write
        batch = fields.get('batch')
        now = time.time()
        if batch in workers:
            stages[batch] = dict(state=state,time=now,target=workers[batch][0],batch=batch)
        counts = dict(db.execute('select state,count(*) from batches group by state'))
        status = dict(state=state,pid=os.getpid(),counts=counts,workers=list(stages.values()),
                      parallel_limit=PARALLEL,observation_error=observation_error,observe_seconds=observe_seconds,**fields)
        if status != last_status or now - last_write >= 5:
            write(state_path,dict(status,time=now))
            last_status, last_write = status, now

    def launch(batch, target):
        def execute():
            lane.stop()
            try:
                outcome = process(batch,target,progress)
                if outcome=='probe_unavailable':
                    result=read(output/'batches'/f'{batch:06d}'/'trial-probe.json')
                    store_gate(dict(gate,mode='cooldown',next_check=time.time()+attachment_gate.BACKOFF,
                                    last_probe=result))
                if outcome=='no_slot':
                    cooldown[target] = time.time()+120
                if outcome=='blocked' and active():
                    folder = output/'batches'/f'{batch:06d}'
                    reason = read(folder/'status.json').get('reason') or '原回执待核对'
                    # Any attempted transfer remains bound to its original batch and tab.
                    with db:
                        db.execute("update batches set state='held',reason=? where id=?",(reason,batch))
                    incident=attachment_gate.failure(folder,batch)
                    if incident:
                        store_gate(attachment_gate.record_failure(gate,incident))
                    cooldown[target] = time.time()+120
            except Exception as exc:
                with db:
                    db.execute("update batches set state='held',reason=? where id=?",(str(exc)[:900],batch))
                cooldown[target] = time.time()+120
            finally:
                stages.pop(batch,None)
        lane = OwnerWorkLane(pw,execute)
        workers[batch] = (target,lane)
        progress('preparing',batch=batch,target=target)
        lane.start()

    try:
        while active():
            for batch,(_,lane) in list(workers.items()):
                if lane.completed:
                    del workers[batch]
            now = time.time()
            if now>=next_legacy:
                next_legacy = now+300
                try:
                    legacy()
                except (ValueError,RuntimeError,OSError,sqlite3.Error) as exc:
                    write(output/'legacy-collection-error.json',dict(time=time.time(),reason=str(exc)[:500]))
            inspected = now>=next_check
            if inspected:
                next_check = now+10
                started = time.monotonic()
                try:
                    checks = observe(config,browser,output)
                    resume_visible_answers(db,output,checks)
                    if any(c.get('new_saved_image_warning') for c in checks):
                        from .formula_queue import refresh_image_reviews
                        refresh_image_reviews(db,Path(control['folder']),output,active)
                    observation_error = None
                    if workers:
                        progress('dispatching')
                except (ValueError, RuntimeError, OSError, KeyError, sqlite3.Error, BrowserError) as exc:
                    checks = []
                    observation_error = str(exc)[:400]
                    if not browser.is_connected():
                        raise
                finally:
                    observe_seconds = round(time.monotonic() - started,3)
            reserved = {target for target,_ in workers.values()}
            pool = load_pool(base/'gpt-window-pool.json')
            candidates = available(checks,pool,reserved,cooldown,time.time())
            channel = shared_submission_status(config)
            start = read(base/'browser-start-request.json')
            slots = read(base/'shared-gpt-window.json')
            bootstrap = (not slots.get('slots') or not all(s.get('target_id') for s in slots['slots'])
                         or slots.get('startup_request_id')!=start.get('id'))
            allow_new = channel['allowed'] and not read(base/'web-channel-control.json').get('chatgpt',{}).get('manual_verification_required')
            # The user requested a composer preference change, independent of sending.
            # During a known account recheck, touch only proven authenticated blank homes.
            channel_hold = read(base/'web-channel-control.json').get('chatgpt',{})
            local_setting_only = (channel_hold.get('manual_verification_required') is True and
                                  channel_hold.get('reason')=='共享页检查发现登录或访问验证' and
                                  len(checks)==20 and all(c.get('inspection_complete') and not
                                  any(c.get(k) for k in ('login','verification','quota')) for c in checks))
            if inspected and allow_new and not bootstrap:
                from .formula_reload import adopt_completed_homes, reconcile_saved_slots
                adopt_completed_homes(config,control,db,browser,pw,checks,pool,output,reserved,completed_homes,active)
                reconcile_saved_slots(config,control,db,browser,pw,checks,pool,output,reserved,active)
            elif inspected:
                completed_homes.clear()
            if inspected and allow_new and not bootstrap:
                from .slot_recovery import recover
                recover(config,control,db,browser,pw,checks,pool,output,reserved,active,recovery_timers,traces)
                available_checks = [c for c in checks if c['target_id'] not in reserved]
                release_unsent_slots(config,control,db,browser,pw,available_checks,pool,output,active)
            if inspected:
                if local_setting_only and not bootstrap and not workers:
                    from .formula_reload import recover_load
                    recover_load(config,control,db,browser,checks,pool,output,stalled_loads,active)
                else:
                    stalled_loads.clear()
            if inspected and (allow_new or local_setting_only) and not bootstrap and PARALLEL>len(workers):
                prepare_idle_effort(config,control,db,browser,checks,pool,reserved,effort_retry,output,active)
            trial=gate.get('trial') or {}
            if gate.get('mode')=='trial':
                folder=output/'batches'/f"{trial['batch']:06d}"
                receipt=read(folder/'attempt.json')
                if attachment_gate.trial_success(receipt,trial):
                    store_gate(dict(mode='ready',last_success=trial,at=now))
                elif trial['batch'] not in workers and attachment_gate.held_intent(db,receipt,trial):
                    store_gate(dict(gate,mode='cooldown',next_check=now+attachment_gate.BACKOFF,
                                    last_unconfirmed_trial=trial))
                elif trial['batch'] not in workers and receipt.get('state') not in ('send_intent','submitted','raw_saved'):
                    store_gate(dict(gate,mode='cooldown',next_check=now+attachment_gate.BACKOFF))
            if inspected and allow_new and gate.get('mode')=='ready':
                try:
                    entry_retry.recover_preflight(db,output,traces,active)
                    entry_retry.resume_one(db,output,control,gate,active,now,traces)
                except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
                    write(output/'entry-retry-error.json',dict(time=now,reason=str(exc)[:500]))
            trial_target=None
            if (gate.get('mode')=='cooldown' and allow_new and not bootstrap and inspected
                    and now>=gate['next_check'] and len(workers)<PARALLEL):
                index=gate.get('checks',0)
                homes = [c for c in checks if c['target_id'] in candidates and empty_formula_home(c)
                         and c['url']=='https://chatgpt.com/?temporary-chat=true']
                probe = dict(at=now,ready=False,reason='no_clean_temporary_home')
                if homes:
                    home = sorted(homes,key=lambda c:c['target_id'])[index % len(homes)]
                    target = home['target_id']
                    probe.update(target=target,eligible=True,url=home['url'],document_start=(home.get('page_load') or {}).get('started_at'))
                    try:
                        from browser.api import shared_page_health__snapshot_page as snapshot_page
                        page=enumerate_pages(browser)['pages'][target]
                        def guard_probe():
                            require_slot(config,browser,target)
                            current = snapshot_page(target,page)
                            if (not active() or not shared_submission_status(config)['allowed'] or
                                    not empty_formula_home(current) or page.url!=home['url'] or
                                    (current.get('page_load') or {}).get('started_at')!=(home.get('page_load') or {}).get('started_at')):
                                raise ValueError('临时首页已变化')
                        entry = attachment_gate.probe_menu(page,guard_probe)
                        probe.update(entry)
                        if entry['ready']:
                            trial_target=target
                    except Exception as exc:
                        probe.update(ready=False,reason='inspection_error',error=str(exc)[:250])
                elif candidates:
                    # Normal slot acquisition can prepare an archived or ordinary
                    # home. The pilot inspects the final blank temporary composer
                    # before it creates any upload intent.
                    trial_target=candidates[index % len(candidates)]
                    probe.update(target=trial_target,eligible=True,reason='awaiting_temporary_home')
                store_gate(dict(gate,next_check=now+attachment_gate.BACKOFF,last_check=now,checks=index+1,last_probe=probe))
            work = db.execute("""select b.id,b.state from batches b left join pending_collections p on p.batch=b.id
                left join temp.formula_paper_order o on o.batch=b.id
                where b.state='active' or (b.state='awaiting_answer' and p.next_check<=?)
                or b.state='queued' order by case b.state when 'active' then 0 when 'awaiting_answer' then 1 else 2 end,
                coalesce(p.next_check,0),case when b.state='queued' then coalesce(o.first_batch,b.id) else b.id end,b.id limit 32""",(now,)).fetchall()
            for batch,state in work:
                if len(workers)>=PARALLEL or not active():
                    break
                if batch in workers:
                    continue
                receipt = read(output/'batches'/f'{batch:06d}'/'attempt.json')
                if receipt:
                    target = receipt.get('window_target')
                    if not target:
                        with db:
                            db.execute("update batches set state='held',reason=? where id=?",('原回执缺少页面归属',batch))
                        continue
                    if target in reserved:
                        continue
                elif gate.get('mode') in ('cooldown','trial') and not trial_target:
                    continue
                elif bootstrap and allow_new and not workers:
                    # Only the original startup path may initialize the window.
                    result = process(batch,None,progress)
                    if result=='blocked':return
                    next_check = 0
                    break
                elif candidates and allow_new and not bootstrap:
                    if trial_target:
                        if trial_target not in candidates:
                            continue
                        target=trial_target
                        store_gate(dict(gate,mode='trial',trial=dict(batch=batch,target=target,at=time.time())))
                        trial_target=None
                    else:
                        target=candidates.pop(0)
                else:
                    continue
                if target in candidates:
                    candidates.remove(target)
                reserved.add(target)
                launch(batch,target)
            if not workers:
                if not work and not db.execute("select 1 from batches where state='awaiting_answer' limit 1").fetchone():
                    unresolved = db.execute("select count(*) from batches where state!='done'").fetchone()[0]
                    progress('needs_review' if unresolved else 'finished')
                    return
                if observation_error:
                    progress('checking_account',reason=observation_error)
                elif not allow_new:
                    progress('waiting_channel',reason=channel.get('reason') or '等待账户复核')
                elif gate.get('mode') in ('cooldown','trial'):
                    progress('waiting_attachment',reason='等待附件入口检查' if gate.get('mode')=='cooldown' else '等待单批试探的提交回执',next_check=gate.get('next_check'),
                             eligible_slots=len(candidates),attachment_probe=gate.get('last_probe'),attachment_mode=gate.get('mode'))
                elif db.execute("select 1 from batches where state='awaiting_answer' limit 1").fetchone():
                    progress('awaiting_answer')
                else:
                    progress('waiting_slot',reason='等待已核实可用于新批次的原槽位')
            pw._sync(asyncio.sleep(1))
    finally:
        for _,lane in workers.values():
            lane.drain()
