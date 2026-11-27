"""Recover the original formula turn or a proven unsent draft on its registered slot."""
import hashlib
import json
import os
import re
import sqlite3
import time
import zipfile
from contextlib import closing
from pathlib import Path

from browser.api import browser_inventory__enumerate_pages as enumerate_pages
from browser.api import shared_page_health__snapshot_page as snapshot_page
from browser.api import shared_pool_store__load_pool as load_pool
from browser.api import shared_window_owner__require_slot as require_slot
from browser.api import web_card_pool__shared_submission_status as channel
from browser.api import web_card_transport__formal_gpt_url as formal_url
from browser.api import web_page_observer__responsive_lock as responsive_lock
from core.api import control__read_record as read, services__atomic_json as write
from .formula_only import digest
from .formula_pilot import replace_text, response_objects

HOME = {'https://chatgpt.com/', 'https://chatgpt.com/?temporary-chat=true'}


def quiet(view):
    return (view.get('inspection_complete') and view.get('account_authenticated') and view.get('composer_available')
            and view.get('uploading') is False and view.get('streaming') is False and not any(
                view.get(k) for k in ('login','verification','quota','account_ui_blocked')))


def draft_matches(value, prompt):
    # ProseMirror textContent can join adjacent paragraph nodes without a newline.
    # Preserve every letter, punctuation mark and horizontal space.
    def text(value):
        return value.replace('\r','').replace('\n','').replace('\u00a0',' ').strip()
    return bool(prompt and text(value)==text(prompt))


def own_draft(view, receipt):
    draft = (view.get('draft') or '').strip()
    return (quiet(view) and view['url'] in HOME and not any(view.get(k) for k in
            ('user_texts','answer_texts','answer_element_count'))
            and set(view.get('errors') or []) <= {'上传未成功','Upload failed'}
            and (not draft or draft_matches(draft,receipt['prompt']))
            and view.get('attachment_names')==[receipt['zip_sha256']+'.zip'])


def upload_pair(events, receipt, status):
    if len(events)!=2 or not status.get('pid'):
        return False
    start,end=events
    expected=dict(lane='formula_only',job_id=receipt['job_id'],target_id=receipt['window_target'],
                  owner_pid=status['pid'],zip_sha256=receipt['zip_sha256'],zip_name=receipt['zip_sha256']+'.zip')
    return (all(e.get(k)==v for e in events for k,v in expected.items())
            and start.get('event')=='upload_started' and end.get('event')=='upload_finished'
            and start.get('upload_attempt_id') and start['upload_attempt_id']==end.get('upload_attempt_id')
            and end.get('result') in ('ok','failed') and (end.get('attachment') or {}).get('confirmed_new') is True
            and (end.get('attachment') or {}).get('expected')==expected['zip_name'])


def stopped_text(folder, receipt, view):
    archived=read(folder/'stopped-answer.json')
    if (archived.get('receipt')!=receipt or len(archived.get('text',[]))!=1 or
            not view.get('terminal_stopped') or view.get('answer_texts')!=archived['text']):
        return None
    raw=archived['text'][0]
    with zipfile.ZipFile(folder/'batch.zip') as z:
        manifest=json.loads(z.read('manifest.json'))
    records=response_objects(raw)
    keys=lambda rows:{(r['paper_id'],r['pdf_page'],r['crop_id']) for r in rows}
    if (keys(records)!=keys(manifest) or any(r.get('kind') not in ('equation','uncertain','unreadable','non_equation')
            or r['kind']=='equation' and not (r.get('latex') and (r.get('python_rhs') or r.get('reason'))) for r in records)):
        return None
    return raw


def archive_page(folder, page, view, receipt, entry):
    journal=folder/'slot-recovery'
    journal.mkdir(exist_ok=True)
    if not (journal/'page.json').exists():
        replace_text(journal/'page.html',page.content())
        image=page.screenshot(timeout=5000)
        tmp=journal/'page.tmp'
        tmp.write_bytes(image)
        tmp.replace(journal/'page.png')
        write(journal/'page.json',dict(view=view,receipt=receipt,pool=entry,owner=os.getpid(),
              html_sha256=digest(journal/'page.html'),png_sha256=digest(journal/'page.png')))
    proof=read(journal/'page.json')
    if (proof.get('receipt')!=receipt or proof.get('pool')!=entry
            or proof.get('html_sha256')!=digest(journal/'page.html') or proof.get('png_sha256')!=digest(journal/'page.png')):
        raise ValueError('原页归档与当前回执不一致')
    return journal


def recover(config, control, db, browser, pw, checks, pool, output, reserved, active, timers, traces):
    from .formula_dispatch import held_before_send, historical_slot_receipt, empty_formula_home
    from .formula_pilot import saved_formula_response, exact_user_turn
    base=Path(config['catalog_path']).parent
    for observed in checks:
        tid=observed['target_id']
        entry=pool['windows'].get(tid,{})
        job=entry.get('active_paper_id') or ''
        m=re.fullmatch(r'formula-(batch|display)-([1-9][0-9]*)',job)
        if tid in reserved or entry.get('state')!='busy' or entry.get('kind')!='formula_only' or not m or not quiet(observed):
            continue
        n=int(m[2]); legacy=m[1]=='batch'
        root=output.parent/'automatic' if legacy else output
        folder=root/'batches'/f'{n:06d}'
        if legacy and not (root/'queue.sqlite3').is_file():
            continue
        with closing(sqlite3.connect((root/'queue.sqlite3').as_uri()+'?mode=ro',uri=True)) as status_db:
            batch=status_db.execute('select state,reason from batches where id=?',(n,)).fetchone()
        if not batch or batch[0] not in ('review','held'):
            continue
        receipt=read(folder/'attempt.json')
        status=read(folder/'status.json')
        kind=status.get('state')
        journal=folder/'slot-recovery'
        intended=read(journal/'original-get.json')
        identity=(tid,job,observed['url'],(observed.get('page_load') or {}).get('started_at'),receipt.get('state'))
        now=time.monotonic()
        if identity not in timers:
            timers[identity]=now+30
            continue
        if now<timers[identity]:
            continue
        timers[identity]=now+60
        def decision(reason,**extra):
            result=dict(reason=reason,job=job,target=tid,**extra)
            previous=read(journal/'outcome.json')
            if any(previous.get(k)!=v for k,v in result.items()):
                write(journal/'outcome.json',dict(result,checked_at=time.time()))
        try:
            packet=read(folder/'packet.json')
            if (receipt.get('window_target')!=tid or receipt.get('temporary') is not True or
                    receipt.get('job_id',job if legacy else None)!=job or packet.get('batch')!=n or
                    not packet.get('sha256') or receipt.get('zip_sha256')!=packet['sha256'] or
                    not receipt.get('prompt','').endswith(packet['sha256']) or digest(folder/'batch.zip')!=packet['sha256']):
                decision('原批次身份不一致');continue
            with responsive_lock(pw,timeout=1):
                page=enumerate_pages(browser)['pages'][tid]
                def guard():
                    require_slot(config,browser,tid)
                    if (not active() or not channel(config)['allowed'] or
                            load_pool(base/'gpt-window-pool.json')['windows'].get(tid)!=entry or
                            read(folder/'attempt.json')!=receipt):
                        raise ValueError('页面或回执归属变化')
                    v=snapshot_page(tid,page)
                    if not quiet(v) or v['url']!=observed['url'] or v.get('page_load',{}).get('started_at')!=identity[3]:
                        raise ValueError('页面状态变化')
                    return v
                v=guard()
                if receipt['state']=='upload_preparation' and not legacy:
                    if (not held_before_send(db,output,entry,tid) or any(k in receipt for k in ('click_settings','at','url'))
                            or not saved_formula_response(control,tid,entry.get('previous_saved_response') or {})):
                        decision('原未发送归属不足');continue
                    if any(prior.get('window_target')==tid and not historical_slot_receipt(control,output,num,state,tid,prior)
                           for num,state in db.execute("select id,state from batches where id!=? and state in ('active','held','awaiting_answer','review','publishing')",(n,))
                           for prior in [read(output/'batches'/f'{num:06d}'/'attempt.json')]):
                        decision('同一槽位还有未解除的批次归属');continue
                    if not own_draft(v,receipt):
                        decision('残留内容未完全匹配',attachment_names=v.get('attachment_names'),has_draft=bool((v.get('draft') or '').strip()),
                                 draft_length=len(v.get('draft') or ''),expected_length=len(receipt['prompt']),
                                 draft_matches=draft_matches(v.get('draft') or '',receipt['prompt']),errors=v.get('errors'))
                        continue
                    if not traces.refresh() or not upload_pair(traces.events.get(job,[]),receipt,status):
                        decision('上传事件无法绑定残留附件');continue
                    journal=archive_page(folder,page,v,receipt,entry)
                    if not own_draft(guard(),receipt):
                        continue
                    # Remove exactly the archived content-addressed chip. Never act on another attachment or editor.
                    remove=page.get_by_role('button',name=re.compile(r'^(?:移除|Remove)\s+'+re.escape(packet['sha256']+'.zip')+'$',re.I))
                    if remove.count()!=1:
                        decision('未找到唯一的原附件移除控件');continue
                    draft=(v.get('draft') or '').strip()
                    if draft:
                        from web_gpt.core import wait_prompt_box
                        box=wait_prompt_box(page,timeout=1500)
                        if not own_draft(guard(),receipt):
                            continue
                        # A live compare-and-clear uses the exact archived draft bytes.
                        ok=box.evaluate("""(el,prompt)=>{if ((el.value??el.textContent??'').trim()!==prompt.trim()) return false;
                            if ('value' in el) el.value='';else el.replaceChildren();
                            el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'deleteContentBackward'}));return true}""",v['draft'])
                        if not ok:
                            continue
                    final=guard()
                    if own_draft(final,receipt) and not (final.get('draft') or '').strip():
                        remove.evaluate('(el)=>el.click()')
                        decision('已移除归档的原附件，等待空白复核')
                    continue
                if receipt.get('state')!='submitted' or not formal_url(receipt.get('url','')) or not receipt.get('at'):
                    continue
                url=receipt['url']
                if sum(i.get('url')==url for i in checks)>int(v['url']==url):
                    decision('原会话地址不唯一');continue
                if v.get('attachments') or (v.get('draft') or '').strip() or v.get('errors'):
                    decision('原页仍有内容或网站错误',errors=v.get('errors'));continue
                original=v['url']==url
                if original and not exact_user_turn(page,receipt['prompt']).get('exact'):
                    decision('当前原页提示无法核实');continue
                if kind=='stopped_answer_review' and original and not legacy:
                    raw=stopped_text(folder,receipt,v)
                    if not raw:
                        decision('中断正文不完整或覆盖不足');continue
                    journal=archive_page(folder,page,v,receipt,entry)
                    if stopped_text(folder,receipt,guard())!=raw or not exact_user_turn(page,receipt['prompt']).get('exact'):
                        continue
                    if (folder/'response.txt').exists() and (folder/'response.txt').read_text()!=raw:
                        decision('已有回答文件冲突');continue
                    replace_text(folder/'response.txt',raw)
                    with db:
                        db.execute("update batches set state='active',reason=null where id=? and state='review'",(n,))
                    write(folder/'attempt.json',dict(receipt,state='raw_saved',stopped_source=True,raw_sha256=digest(folder/'response.txt')))
                    decision('已核对中断原文全部页，交回本地解析');continue
                if intended and not original:
                    from .unavailable_slots import release_home
                    if empty_formula_home(v):
                        if legacy:
                            with closing(sqlite3.connect(root/'queue.sqlite3')) as previous:
                                freed=release_home(folder,job,tid,previous,n,page,entry,base/'gpt-window-pool.json',guard)
                        else:
                            freed=release_home(folder,job,tid,db,n,page,entry,base/'gpt-window-pool.json',guard)
                        if freed:
                            decision('原槽已释放，原批次留档待复核');continue
                    decision('原会话打开后仍不可收取',current_url=v['url']);continue
                if intended and original and v.get('answer_texts') and legacy:
                    with closing(sqlite3.connect(root/'queue.sqlite3')) as old, old:
                        old.execute("update batches set state='active',reason=null where id=? and state='review'",(n,))
                    decision('原历史会话已返回正文，接回旧队列收取');continue
                if intended and original and v.get('answer_texts') and not legacy:
                    if kind not in ('terminal_without_text','blocked','empty_wait_review'):
                        continue
                    with db:
                        db.execute("update batches set state='awaiting_answer',reason=null where id=?",(n,))
                        db.execute('insert or replace into pending_collections values(?,?)',(n,time.time()))
                    decision('原页出现回答，接回原请求收取');continue
                if intended:
                    decision('已复查原地址，仍无可收取正文');continue
                if not (empty_formula_home(v) or original and kind=='empty_wait_review' and
                        not v.get('answer_element_count') and not v.get('answer_texts')):
                    continue
                journal=archive_page(folder,page,v,receipt,entry)
                latest=guard()
                if not (empty_formula_home(latest) or original and not latest.get('answer_element_count') and
                        not latest.get('attachments') and not (latest.get('draft') or '').strip()
                        and exact_user_turn(page,receipt['prompt']).get('exact')):
                    continue
                write(journal/'original-get.json',dict(target=tid,job=job,at=time.time(),url=url,
                      zip_sha256=packet['sha256'],owner=os.getpid()))
                page.goto(url,wait_until='domcontentloaded',timeout=12000)
                decision('已只读打开原会话',current_url=page.url)
        except Exception as exc:
            decision('恢复检查受阻',error=str(exc)[:350])
