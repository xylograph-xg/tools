"""One-shot corpus organization on the existing locked web owner."""
import hashlib
import json
import os
import time
from pathlib import Path

from core.api import control__read_record as read_record, services__atomic_json as atomic_json
from core.api import literature_catalog__source_records as sources, paths__WorkspacePath as WorkspacePath
CONTROLS=('web-card-control.json','card-review-control.json','card-correction-control.json','web-tab-watch-control.json')

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def app_route(request):
    from .display_equations import POLICY
    return (request.get('mode') == 'temporary_queue' and request.get('transport') == 'codex_web_gpt'
            and request.get('extraction') == POLICY)


def enabled(config):
    base=Path(config['catalog_path']).parent
    request=read_record(base/'formula-only-control.json')
    return request.get('enabled') is True and _pauses_match(base, request)

def _pauses_match(base, request):
    for name in CONTROLS:
        if read_record(base/name).get('paused_by_user') is not True or digest(base/name)!=request.get('pause_hashes',{}).get(name):
            return False
    return True

def check_answer(raw,job,evidence):
    text=raw.strip()
    if text.startswith('```') and text.endswith('```'):
        text=text.partition('\n')[2][:-3].strip()
    value=json.loads(text)
    if not isinstance(value,dict) or value.get('job')!=job['id'] or not isinstance(value.get('items'),list):raise ValueError('网页回执批次不一致')
    expected=set(json.loads(job['keys_json']))
    pages={e['id']:e['page'] for e in evidence}
    seen=set()
    for item in value['items']:
        if not isinstance(item,dict):raise ValueError('裁图条目必须为对象')
        k=item['id']
        if k not in expected or k in seen or type(item.get('page')) is not int or item['page']!=pages[k]:
            raise ValueError('裁图标识或页码不一致')
        if item.get('type') not in ('equation','duplicate','non_equation','uncertain','unreadable'):raise ValueError('类型缺失')
        if item['type']=='equation' and (not isinstance(item.get('latex'),str) or not item['latex'].strip()):raise ValueError('缺公式')
        seen.add(k)
    if seen!=expected:raise ValueError('未覆盖全部图片')
    return value

def fresh(config,article, *, for_upload=False):
    found=sources(config['catalog_path'],[article['id']])
    if len(found)!=1:return False
    r=found[0]
    if for_upload:
        from .scope import ordinary_words_only
        if ordinary_words_only(r):
            raise ValueError('标题摘要仅命中普通词或缺乏佐证的小写缩写，OLED 范围待核对：'+article['id'])
    return (r['acquisition']=='available' and r['asset_hash']==article['source_hash']
            and not any(r['metadata'].get(k) for k in ('identity_review_required','version_review_required','out_of_scope'))
            and WorkspacePath(r['asset_path']).resolve()==Path(article['source_path']).resolve()
            and digest(article['source_path'])==article['source_hash'])

def publish(db,job,article,receipt,raw):
    path=Path(article['path']);doc=json.loads(path.read_text(encoding='utf-8'))
    value=check_answer(raw,job,doc['evidence'])
    doc['web_results'][str(job['part'])]=dict(conversation=receipt['url'],model=receipt['settings'],raw_sha256=receipt['raw_sha256'],items=value['items'])
    doc['status']='web_organized' if len(doc['web_results'])==doc['input_parts'] else 'web_partial'
    atomic_json(path,doc)
    db.execute("update jobs set state='organized' where id=?",(job['id'],));db.commit()

def run(config):
    choice=read_record(Path(config['catalog_path']).parent/'formula-only-control.json')
    if app_route(choice):
        from . import formula_queue
        base = Path(config['catalog_path']).parent
        try:
            result = formula_queue.run(config,choice)
        except Exception as exc:
            import traceback
            atomic_json(base/'formula-owner-exit.json',dict(state='owner_error',time=time.time(),pid=os.getpid(),
                        error_type=type(exc).__name__,reason=str(exc)[:700],traceback=traceback.format_exc()[-5000:]))
            raise
        if read_record(base/'formula-only-control.json') != choice or not enabled(config):
            atomic_json(base/'formula-owner-exit.json',dict(state='control_changed',time=time.time(),pid=os.getpid(),
                        owner_revision=choice.get('owner_revision')))
        return result
    raise ValueError('公式队列仅支持已登记的 App 整页模式')

def control_pilot(config, start):
    from core.api import control__mutate_record as mutate
    import subprocess

    base = Path(config['catalog_path']).parent
    path = base / 'formula-only-control.json'

    def validate(request):
        if not start:
            return
        if not app_route(request):
            raise ValueError('公式队列仅支持已登记的 App 整页模式')
        if not _pauses_match(base, request):
            raise ValueError('原网页任务暂停记录已变化，请核对后启动')
        if not (Path(request['folder'])/'jobs.sqlite3').is_file():
            raise ValueError('公式材料库无法读取')

    mutate(path, {'enabled': start}, event='formula_pilot_control', validate=validate)
    if start:
        service = f'gui/{os.getuid()}/local.paper.web-cards'
        result = subprocess.run(['/bin/launchctl', 'kickstart', service], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError('未能启动公式测试：' + result.stderr.strip())
