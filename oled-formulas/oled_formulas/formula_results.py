"""Validate scalar code and describe the frozen page coverage of each article."""
from pathlib import Path
import hashlib
import ast
import inspect
import math
import re
import zipfile
import json

from core.api import control__read_record as read
from .formula_only import digest

# These functions return a real scalar for scalar inputs in their domains.
MATH_FUNCTIONS = frozenset("""acos acosh asin asinh atan atan2 atanh cbrt ceil comb copysign
cos cosh degrees erf erfc exp exp2 expm1 fabs factorial floor fmod gamma gcd hypot
lcm ldexp lgamma log log10 log1p log2 perm pow radians remainder sin sinh sqrt tan tanh trunc""".split())
MATH_CONSTANTS = {'pi', 'e', 'tau'}
OPERATORS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv, ast.UAdd, ast.USub)


def scalar_node(node):
    if isinstance(node, ast.Constant):
        return type(node.value) in (int, float)
    if isinstance(node, ast.Name):
        return not node.id.startswith('_') and node.id != 'math'
    if isinstance(node, ast.BinOp):
        return isinstance(node.op, OPERATORS) and scalar_node(node.left) and scalar_node(node.right)
    if isinstance(node, ast.UnaryOp):
        return isinstance(node.op, OPERATORS) and scalar_node(node.operand)
    if isinstance(node, ast.Attribute):
        return isinstance(node.value, ast.Name) and node.value.id == 'math' and node.attr in MATH_CONSTANTS
    if isinstance(node, ast.Call) and not node.keywords:
        func = node.func
        allowed = (isinstance(func, ast.Name) and func.id == 'abs' and len(node.args) == 1
                   or isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
                   and func.value.id == 'math' and func.attr in MATH_FUNCTIONS and hasattr(math, func.attr))
        if not allowed or not all(scalar_node(arg) for arg in node.args):
            return False
        if isinstance(func, ast.Name):
            return True
        if func.attr == 'log':
            return len(node.args) in (1,2)
        if func.attr == 'hypot':
            return True
        try:
            inspect.signature(getattr(math,func.attr)).bind(*node.args)
        except (TypeError,ValueError):
            return False
        return True
    return False


def check_python(item):
    expr = item.get('python_rhs')
    if not expr:
        item['python_status'] = 'needs_review' if item.get('rejected_python_rhs') else 'unavailable'
        return
    try:
        ok = isinstance(expr, str) and scalar_node(ast.parse(expr.strip(), mode='eval').body)
    except (SyntaxError, ValueError, RecursionError):
        ok = False
    if ok:
        item['python_status'] = 'scalar_syntax_checked'
    else:
        item.update(rejected_python_rhs=expr, python_rhs='', python_status='needs_review',
                    python_review_reason='表达式未通过标量 Python 语法、名称或函数检查')


def bound_warning(folder, batch):
    from .formula_pilot import image_warning
    note = read(folder/'observed-image-warning.json')
    receipt = read(folder/'attempt.json')
    return bool(receipt.get('state') in ('submitted','raw_saved') and receipt.get('temporary') is True
                and isinstance(note.get('checked_at'),(float,int)) and 0<(receipt.get('at') or 0)<=note['checked_at']
                and note.get('job_id')==receipt.get('job_id')==f'formula-display-{batch}'
                and all(note.get(k) and note[k]==receipt.get(r) for k,r in
                        [('target','window_target'),('url','url'),('zip_sha256','zip_sha256')])
                and image_warning(note.get('image_health')))


def apply_audit_holds(article, source, items):
    registry = json.loads(Path(__file__).with_name('audit-review-items.json').read_bytes())
    for issue in registry['items']:
        if issue['source_sha256']!=article['source_sha256'] or issue['raw_sha256']!=source['raw_sha256'] or issue['batch']!=source['batch']:
            continue
        for item in items:
            if (item.get('kind')=='equation' and item['paper_id']==issue['paper_id'] and item['pdf_page']==issue['pdf_page']
                    and item.get('equation_label')==issue['equation_label']
                    and hashlib.sha256(item['latex'].encode()).hexdigest()==issue['latex_sha256']):
                item.update(visual_review_required=True,external_review_reason=issue['reason'],external_review_report=registry['report'])


def python_mapping_issues(item):
    if not item.get('python_rhs'):
        return []
    latex = item.get('latex') or ''
    sides = latex.split('=')
    issues = []
    if len(sides)!=2:
        issues.append('ambiguous_equation')
    lhs = item.get('python_lhs')
    if not isinstance(lhs,str) or not lhs.strip() or len(sides)==2 and lhs.strip()!=sides[0].strip():
        issues.append('unconfirmed_target')
    if re.search(r'\bmath\.(?:sin|cos|tan)\b',item['python_rhs']) and (
            item.get('angle_unit') not in ('radian','radians','degree','degrees') or not item.get('angle_unit_evidence')):
        issues.append('unconfirmed_angle_unit')
    return issues


def review_python(item):
    """Expose only scalar code with a supported assignment and usable page evidence."""
    check_python(item)
    issues = python_mapping_issues(item)
    item['python_mapping_issues'] = issues
    if item.get('python_rhs') and (issues or item.get('page_conflict') or item.get('visual_review_required')
                                   or item.get('transcription_status') == 'needs_review'):
        item.update(unverified_python_rhs=item['python_rhs'], python_rhs='', python_status='mapping_needs_review')


def verified_latex(article, formulas, review, evidence):
    # Only a separate local scientific review can authorize training. Bind
    # the decision to the exact PDF, saved answer, crop and transcription.
    if (review.get('schema')!='oled-scientific-review-v1' or not review.get('reviewer')
            or review.get('topic_verified') is not True or not review.get('topic_evidence')
            or not article.get('source_sha256') or review.get('source_sha256')!=article['source_sha256']):
        return []
    approved = []
    sources = {row['batch']:row['raw_sha256'] for row in evidence}
    for item in formulas:
        if (item.get('visual_review_required') or item.get('transcription_status') not in ('unverified','latex_visually_checked')
                or item.get('python_status')=='needs_review' or not item.get('crop_path') or not item.get('latex')):
            continue
        binding = dict(paper_id=item['paper_id'],batch=item['source_batch'],pdf_page=item['pdf_page'],
                       latex_sha256=hashlib.sha256(item['latex'].encode()).hexdigest(),raw_sha256=sources[item['source_batch']])
        checks = [r for r in review.get('items',[]) if isinstance(r,dict) and all(r.get(k)==v for k,v in binding.items())]
        if len(checks)!=1:
            continue
        check=checks[0]
        if not all(check.get(k) is True for k in ('display_verified','latex_verified','scientific_verified')) or not check.get('page_evidence'):
            continue
        path=Path(item['crop_path'])
        if path.is_file() and check.get('crop_sha256')==digest(path):
            approved.append(dict(paper_id=item['paper_id'],source_batch=item['source_batch'],pdf_page=item['pdf_page'],
                                 crop_path=str(path),latex=item['latex'],reviewer=review['reviewer']))
    return approved


def training_view(article, formulas, review=None, evidence=()):
    # All current receipts document extraction or narrow transcription checks only.
    # Never promote a model-supplied verification field into a scientific approval.
    title = article.get('title') or ''
    subject = bool(re.search(r'\borganic\s+(?:light[\s‐‑–-]*emitting|electroluminescent)\s+(?:diodes?|devices?|displays?)\b',title,re.I)
                   or re.search(r'\bOLEDs?\b',title) and re.search(
                       r'optical|efficien|emiss|lumin|diodes?|device|carrier|exciton|organic|emitter|transport|electr',title,re.I))
    # Expose only the unverified LaTeX and its evidence in the review view.
    fields = ('source_batch','pdf_page','crop_id','crop_path','equation_label','latex')
    candidates = [{k:item.get(k) for k in fields} for item in formulas if subject and item.get('latex') and item.get('crop_path')
                  and item.get('transcription_status') in ('unverified','latex_visually_checked')
                  and not item.get('visual_review_required') and item.get('python_status')!='needs_review']
    approved = verified_latex(article,formulas,review or {},evidence)
    return dict(training_formulas=approved,training_candidates=candidates,topic_status='title_supported' if subject else 'needs_topic_review',
                training_status='has_verified_latex' if approved else 'awaiting_scientific_review')


def frozen_pages(db, folder, batch):
    packet = read(folder/'packet.json')
    bundle = folder/'batch.zip'
    receipt = read(folder/'attempt.json')
    if (packet.get('batch') != batch or packet.get('policy') != 'display-pages-v1'
            or packet.get('sha256') != digest(bundle)):
        raise ValueError('冻结包身份或内容变化')
    with zipfile.ZipFile(bundle) as archive:
        rows = json.loads(archive.read('manifest.json'))
    scheduled = set(db.execute('select paper,crop from crops where batch=?', (batch,)))
    keys = {(r['paper_id'], r['crop_id']) for r in rows}
    if not keys or keys != scheduled or len(keys) != len(rows) or any(
            r['crop_id'] != f"P{r['pdf_page']:04d}" for r in rows):
        raise ValueError('冻结包与实际排队页不一致')
    if (receipt.get('state') != 'raw_saved' or receipt.get('job_id') != f'formula-display-{batch}'
            or receipt.get('zip_sha256') != packet['sha256']
            or receipt.get('raw_sha256') != digest(folder/'response.txt')):
        raise ValueError('已保存回答与冻结包不一致')
    return rows, dict(batch=batch, raw_sha256=receipt['raw_sha256'], zip_sha256=packet['sha256'])


def coverage(db, paper, records):
    planned = db.execute('select c.crop,c.batch,b.state from crops c join batches b on b.id=c.batch where c.paper=?', (paper,)).fetchall()
    keys = [key for key, _, _ in planned]
    if not keys or any(not re.fullmatch(r'P[0-9]{4,}', key) for key in keys):
        raise ValueError('行间公式页计划缺失或无效')
    expected = {int(key[1:]) for key in keys}
    checked = {r['pdf_page'] for r in records}
    if not checked <= expected:
        raise ValueError('产出页超出冻结计划')
    conflict = {r['pdf_page'] for r in records if r.get('page_conflict')}
    uncertain = {r['pdf_page'] for r in records if r['kind'] in ('uncertain','unreadable') or r.get('visual_review_required')
                 or r.get('transcription_status') == 'needs_review'}
    return dict(conflict_pages=sorted(conflict), visual_review_pages=sorted(conflict | uncertain),
                expected_pages=sorted(expected), pages_checked=sorted(checked),
                missing_pages=sorted(expected-checked), complete=checked == expected,
                failed_batches_at_export=sorted({batch for _,batch,state in planned if state in ('held','review')}
                                               | {r['source_batch'] for r in records if r.get('page_conflict')}))
