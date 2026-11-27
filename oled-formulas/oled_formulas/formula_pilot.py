"""Parse and persist frozen formula answers from the App or saved receipts."""
import json
import os
import re
from pathlib import Path
from core.api import services__atomic_json as write, control__read_record as read

def replace_text(path, value):
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(dir=path.parent, delete=False, mode='w', encoding='utf-8') as tmp:
        pending = Path(tmp.name)
        try:
            tmp.write(value)
            tmp.flush()
            os.fsync(tmp.fileno())
            pending.replace(path)
        finally:
            pending.unlink(missing_ok=True)


def image_warning(health):
    return bool(health and (health.get('image_notice') or health.get('broken_images')))


def response_objects(raw):
    text = raw.strip()
    # Only discard a recognized presentation line before parsing complete records.
    text = re.sub(r'^(?:以下是(?:整理)?结果[：:]|Here are the results:)\s*\n', '', text, count=1, flags=re.I)
    if text.startswith('```'):
        lines = text.splitlines()
        if lines[-1].strip() != '```' or lines[0].strip().lower() not in ('```', '```json', '```jsonl'):
            raise ValueError('网页回答的代码块不完整')
        text = '\n'.join(lines[1:-1])
    # Rich-text code blocks sometimes expose the language badge as plain text.
    text = re.sub(r'^jsonl?\s*(?=\{)', '', text, count=1, flags=re.IGNORECASE)
    decoder = json.JSONDecoder()
    records = []
    cursor = 0
    while cursor < len(text):
        if text[cursor].isspace():
            cursor += 1
            continue
        item, cursor = decoder.raw_decode(text, cursor)
        if not isinstance(item, dict):
            raise ValueError('公式记录必须是完整对象')
        records.append(item)
    return records


def save_formulas(control, folder, rec, note):
    import zipfile
    from .formula_only import digest
    packet = folder/('batch.zip' if control.get('batch') else 'two-papers.zip')
    if digest(packet) != rec['zip_sha256']:
        raise ValueError('测试包已变化')
    with zipfile.ZipFile(packet) as bundle:
        rows = json.loads(bundle.read('manifest.json'))
    raw = (folder/'response.txt').read_text(encoding='utf-8')
    try:
        out = response_objects(raw)
    except json.JSONDecodeError as exc:
        if (rec.get('transport') != 'codex_web_gpt' or exc.msg != 'Invalid \\escape'
                or r'"paper\_id"' not in raw):
            raise
        # The App may Markdown-escape identifiers in plain-text negative rows.
        # Preserve the literal backslash in free text. Only decode structural
        # identifiers for this exact schema; math and ambiguous rows stay held.
        rows_with_escapes = response_objects(re.sub(r'(?<!\\)\\_', lambda _: r'\\_', raw))
        keys = {r'paper\_id':'paper_id',r'pdf\_page':'pdf_page',r'crop\_id':'crop_id',
                'kind':'kind','reason':'reason'}
        if not rows_with_escapes or any(set(row)!=keys.keys() or row['kind']!=r'non\_equation'
                                         for row in rows_with_escapes):
            raise
        out = [dict({name:row[key] for key,name in keys.items()},kind='non_equation') for row in rows_with_escapes]
    keys=lambda item:(item['paper_id'],item['pdf_page'],item['crop_id'])
    if control.get('batch'):
        allowed = {'equation','non_equation','uncertain','unreadable'}
        if any(item.get('kind') not in allowed or item['kind']=='equation' and
               (not item.get('latex') or not (item.get('python_rhs') or item.get('reason'))) for item in out):
            raise ValueError('原回答已保存，公式或状态待核对')
    elif len(out)!=len(rows) or any(not x.get('latex') or not x.get('python_rhs') for x in out):
        raise ValueError('原回答已保存，测试结果待核对')
    if set(map(keys,out))!=set(map(keys,rows)):
        raise ValueError('原回答已保存，结构或图片归属待核对')
    from . import display_equations
    if control.get('extraction') == display_equations.POLICY:
        display_equations.mark_page_conflicts(out)
        display_equations.crop_results(folder,rows,out)
        from .formula_results import check_python
        for item in out:
            if item['kind']=='equation':
                check_python(item)
            elif (item['kind']=='non_equation' and '在 reason 写出本页可见内容' in rec.get('prompt','')
                  and not str(item.get('reason') or '').strip()):
                item.update(kind='uncertain',reason='原回答判定本页无行间公式，但没有给出页面依据')
        recorded = read(folder/'observed-image-warning.json')
        bound_warning = (recorded.get('job_id') == rec.get('job_id') and
                         recorded.get('target') == rec.get('window_target') and
                         recorded.get('url') == rec.get('url') and recorded.get('zip_sha256') == rec.get('zip_sha256')
                         and image_warning(recorded.get('image_health')))
        if rec.get('stopped_source'):
            for item in out:
                item.update(visual_review_required=True,stopped_source=True,visual_review_reason='中断回答已核对覆盖，需复核原页')
        if bound_warning or image_warning(rec.get('image_health')) or image_warning(rec.get('observed_image_warning')):
            for item in out:
                item.update(visual_review_required=True,visual_review_reason='原临时聊天显示图片异常，需对照原页')
    sources = {row['paper_id']: row['source_sha256'] for row in rows}
    by_paper = {}
    for item in out:
        paper_id = item['paper_id']
        article = read(Path(control['folder'])/'articles'/(paper_id+'.json'))
        if article.get('source_sha256') != sources[paper_id]:
            raise ValueError('原文索引与测试包版本不一致')
        item['source_path'] = article['source_path']
        by_paper.setdefault(paper_id, []).append(item)
    if control.get('batch'):
        replace_text(folder/'records.jsonl',''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in out))
        out = [x for x in out if x['kind']=='equation']
        if control.get('extraction') == display_equations.POLICY:
            from .formula_results import review_python
            out = [x for x in out if not x.get('page_conflict')]
            for item in out:
                review_python(item)
        by_paper.clear()
    for paper_id, formulas in by_paper.items():
        write(folder/'by-paper'/(paper_id+'.json'), dict(paper_id=paper_id, source_sha256=sources[paper_id],
              source_path=formulas[0]['source_path'], formulas=formulas))
    pending = folder/'formulas.jsonl.tmp'
    pending.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in out),encoding='utf-8')
    pending.replace(folder/'formulas.jsonl')
    note('collected',count=len(out),model=rec['model'],temporary=True)
