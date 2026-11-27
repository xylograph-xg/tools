"""Release only explicitly listed, archived temporary turns after an unsuccessful original GET."""
import os
import re
from pathlib import Path

from browser.api import shared_pool_store__load_pool as load_pool, shared_pool_store__save_pool as save_pool
from core.api import control__read_record as read, services__atomic_json as write
from .formula_only import digest

REASON = '原临时会话无法找回，已归档并释放原槽；仅待复核，不重发'


def authorized(folder, job, tid):
    allowed=read(Path(__file__).with_name('unavailable-slot-authorization.json')).get(job)
    if not allowed or allowed['target']!=tid:
        return None
    journal=folder/'slot-recovery'
    for p,key in ((folder/'attempt.json','receipt_sha256'),(journal/'page.json','archive_sha256'),
                  (journal/'original-get.json','get_sha256')):
        if not p.is_file() or digest(p)!=allowed[key]:
            return None
    rec=read(folder/'attempt.json')
    proof=read(journal/'page.json')
    visit=read(journal/'original-get.json')
    if (rec.get('state')!='submitted' or rec.get('window_target')!=tid or rec.get('at')!=allowed['sent_at']
            or rec.get('url')!=allowed['url'] or rec.get('zip_sha256')!=allowed['zip_sha256']
            or proof.get('receipt')!=rec or visit.get('target')!=tid or visit.get('job')!=job or visit.get('url')!=rec['url']):
        return None
    return allowed


def released(folder, job, tid):
    record=read(folder/'slot-recovery/released.json')
    if (not record or record.get('job')!=job or record.get('target')!=tid
            or not record.get('authorization') or record['authorization']!=authorized(folder,job,tid)
            or record.get('requeue_allowed') is not False):
        return False
    final=record.get('final') or {}
    first=record.get('first') or {}
    return (final.get('target_id')==tid and first.get('identity',{}).get('url')==final.get('url')
            and (final.get('checked_at') or 0)-(first.get('at') or 0)>=30
            and all((folder/'slot-recovery'/name).is_file() and digest(folder/'slot-recovery'/name)==record.get(key)
                    for name,key in [('returned-home.html','html_sha256'),('returned-home.png','png_sha256')]))


def released_blank(control, tid, entry):
    job=entry.get('archived_unavailable_job') or ''
    m=re.fullmatch(r'formula-(batch|display)-([1-9][0-9]*)',job)
    if not m:
        return False
    folder=Path(control['folder'])/('automatic' if m[1]=='batch' else 'display-equations')/'batches'/f'{int(m[2]):06d}'
    return released(folder,job,tid)


def release_home(folder, job, tid, db, n, page, entry, pool_path, guard):
    from .formula_dispatch import empty_formula_home
    from .formula_pilot import replace_text
    journal=folder/'slot-recovery'
    allowed=authorized(folder,job,tid)
    if not allowed:
        return False
    def home():
        v=guard()
        if not (empty_formula_home(v) and v.get('account_authenticated') and v.get('target_id')==tid and
                v.get('url')==page.url and (v.get('page_load') or {}).get('ready_state')=='complete'
                and v['page_load'].get('started_at')):
            raise ValueError('原槽首页未完成空白复核')
        return v
    v=home()
    key=dict(url=v['url'],document_start=v['page_load']['started_at'],target=tid,job=job)
    first=read(journal/'release-first-home.json')
    if first.get('identity')!=key:
        write(journal/'release-first-home.json',dict(identity=key,at=v['checked_at']))
        return False
    if v['checked_at']-first['at']<30:
        return False
    proof=read(journal/'page.json')
    if digest(journal/'page.html')!=proof['html_sha256'] or digest(journal/'page.png')!=proof['png_sha256'] or digest(folder/'batch.zip')!=allowed['zip_sha256']:
        raise ValueError('原槽归档或冻结材料指纹变化')
    if not (journal/'released.json').exists():
        replace_text(journal/'returned-home.html',page.content())
        png=page.screenshot(timeout=5000)
        tmp=journal/'returned-home.tmp'
        tmp.write_bytes(png)
        tmp.replace(journal/'returned-home.png')
        last=home()
        if last['page_load']['started_at']!=key['document_start']:
            raise ValueError('空白首页文档已变化')
        write(journal/'released.json',dict(job=job,target=tid,authorization=allowed,owner=os.getpid(),
              pool_before=entry,first=first,final=last,html_sha256=digest(journal/'returned-home.html'),
              png_sha256=digest(journal/'returned-home.png'),requeue_allowed=False))
    record=read(journal/'released.json')
    if (not released(folder,job,tid) or record.get('pool_before')!=entry or
            digest(journal/'returned-home.html')!=record['html_sha256'] or digest(journal/'returned-home.png')!=record['png_sha256']):
        raise ValueError('原槽释放记录不一致')
    current=load_pool(pool_path)
    home()
    if current['windows'].get(tid)!=entry:
        raise ValueError('原槽已重新分配')
    with db:
        if db.execute("update batches set state='review',reason=? where id=? and state in ('held','review')",(REASON,n)).rowcount!=1:
            raise ValueError('原批次状态已改变')
    blank=dict(entry,state='ready_blank',never_submitted=False,archived_unavailable_job=job)
    for field in ('kind','active_paper_id','raw_path','raw_sha256','conversation_url'):
        blank.pop(field,None)
    current['windows'][tid]=blank
    save_pool(pool_path,current)
    return True
