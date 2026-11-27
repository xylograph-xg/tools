"""Persistent backoff for new OLED uploads, independent of collecting existing turns."""
import time

from core.api import control__read_record as read, services__atomic_json as write

BACKOFF = 15 * 60
ENTRY_FAILURE = '附件入口暂未就绪，未发送'


def failure(folder, batch):
    status = read(folder/'status.json')
    attempt = read(folder/'attempt.json')
    reason = status.get('reason') or ''
    if (status.get('state') != 'blocked' or not (reason == ENTRY_FAILURE or reason.startswith('附件额度限制：'))
            or attempt.get('state') != 'upload_preparation' or attempt.get('at') or attempt.get('url')
            or attempt.get('job_id') != f'formula-display-{batch}' or not attempt.get('window_target')
            or (status.get('last') or {}).get('target') != attempt['window_target']):
        return None
    return dict(batch=batch,target=attempt['window_target'],at=status['time'],reason=reason)


def record_failure(state, event):
    events = [e for e in state.get('events',[]) if abs(event['at']-e['at']) <= 300 and e['batch']!=event['batch']]
    events.append(event)
    state = dict(state, events=events)
    if (event['reason'].startswith('附件额度限制：') or len({e['target'] for e in events}) >= 2
            or state.get('mode') in ('cooldown','trial')):
        state.update(mode='cooldown',next_check=max(e['at'] for e in events)+BACKOFF)
    return state


def load_gate(output,db):
    path = output/'attachment-backoff.json'
    if path.exists():
        return read(path)
    # Recover a burst predating this safeguard without treating an old incident as current.
    now=time.time()
    events=[]
    for batch, in db.execute("select id from batches where state='held'"):
        event=failure(output/'batches'/f'{batch:06d}',batch)
        if event and 0 <= now-event['at'] <= 3600:
            events.append(event)
    state={}
    if events:
        latest_send=max((read(p).get('at') or 0 for p in (output/'batches').glob('*/attempt.json')),default=0)
        for event in sorted(events,key=lambda e:e['at']):
            if event['at']>=latest_send:
                state=record_failure(state,event)
        if state.get('mode')=='cooldown':
            state.update(next_check=max(state['next_check'],now+BACKOFF),recovered_at=now)
        if state:
            write(path,state)
    return state


def trial_success(receipt, trial):
    return (receipt.get('state') in ('submitted','raw_saved') and receipt.get('temporary') is True
            and receipt.get('job_id')==f"formula-display-{trial['batch']}" and receipt.get('window_target')==trial['target']
            and bool(receipt.get('zip_sha256')) and (receipt.get('at') or 0)>=trial['at'])




def held_intent(db, receipt, trial):
    return (receipt.get('state')=='send_intent' and receipt.get('temporary') is True
            and receipt.get('job_id')==f"formula-display-{trial['batch']}"
            and receipt.get('window_target')==trial['target'] and bool(receipt.get('zip_sha256'))
            and (receipt.get('at') or 0)>=trial['at']
            and db.execute('select state from batches where id=?',(trial['batch'],)).fetchone() in (('held',),('review',)))


def probe_menu(page, guard):
    from browser.api import web_card_transport__attachment_entry as attachment_entry
    guard()
    initial = attachment_entry(page)
    if initial['reason'] not in ('document_input','no_document_input'):
        return initial
    button = page.locator('button[aria-label="添加文件等内容"],button[aria-label="Add files and more"]')
    if button.count()!=1 or not button.is_visible() or not button.is_enabled():
        return dict(ready=False,reason='menu_unavailable')
    opened = button.get_attribute('aria-expanded')!='true'
    try:
        if opened:
            guard()
            button.evaluate('(el)=>el.click()')
            page.wait_for_timeout(500)
        guard()
        if button.get_attribute('aria-expanded')!='true':
            return dict(ready=False,reason='menu_unconfirmed')
        entry = attachment_entry(page)
        if not entry['ready']:
            return entry
        import re
        options = page.get_by_role('menuitem',name=re.compile(
            r'上传.{0,8}文件|添加.{0,8}文件|从计算机上传|upload (?:from computer|files)|(?:add|attach) (?:photos (?:and|&) )?files',re.I))
        visible = [option for option in options.all() if option.is_visible()]
        if not visible:
            # Some native composers expose a document input with a button or
            # label instead of a menuitem. Inspect the opened popover for a
            # disabled upload action before admitting one normal upload trial.
            fallback = button.evaluate(r"""trigger => {
                const popup = document.getElementById(trigger.getAttribute('aria-controls'));
                const roots = popup ? [popup] : [...document.querySelectorAll(
                    '[role="menu"],[role="listbox"],[role="dialog"],[data-radix-popper-content-wrapper],[popover]:popover-open')];
                const upload = /上传.{0,8}文件|添加.{0,8}文件|从计算机上传|upload (?:from computer|files)|(?:add|attach) (?:photos (?:and|&) )?files/i;
                const actions = roots.flatMap(root => [...root.querySelectorAll(
                    'button,label,[role="button"],[role="menuitemradio"],[role="option"],[aria-disabled],[data-disabled]')])
                    .filter(el => el.getClientRects().length && upload.test(
                        [el.getAttribute('aria-label'),el.innerText].filter(Boolean).join(' ')));
                const disabled = actions.some(el => el.closest(':disabled,[aria-disabled="true"],[data-disabled]:not([data-disabled="false"]),[inert]') ||
                    /disabled|opacity-50|text-token-text-tertiary|pointer-events-none/i.test(el.className || ''));
                return {disabled, visible_upload_actions:actions.length};
            }""")
            if fallback['disabled']:
                return dict(ready=False,reason='disabled')
            guard()
            final = attachment_entry(page)
            if not final['ready']:
                return final
            return dict(ready=True,reason='verified_document_input',visible_upload_actions=fallback['visible_upload_actions'])
        if len(visible)>1:
            return dict(ready=False,reason='ambiguous_upload_menu_options')
        if not visible[0].is_enabled() or visible[0].get_attribute('data-disabled') is not None:
            return dict(ready=False,reason='disabled',notice=visible[0].inner_text()[:120])
        return dict(ready=True,reason='menu_and_document_input',option=visible[0].inner_text()[:120])
    finally:
        if opened:
            guard()
            if button.get_attribute('aria-expanded')=='true':
                button.evaluate('(el)=>el.click()')
