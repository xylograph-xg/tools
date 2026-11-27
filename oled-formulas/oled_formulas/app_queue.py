"""Route unsent OLED display batches to the desktop app under the existing owner lock."""
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import closing
from threading import Lock
import hashlib
import json
import os
import re
from pathlib import Path
import sqlite3
import subprocess
import time
import zipfile

from codex_web_client.api import Client
from core.api import control__read_record as read, seed_focus__allowed as allowed, services__atomic_json as write
from . import display_equations
from .formula_only import digest, fresh
from .formula_pilot import replace_text, save_formulas
from .formula_queue import publish
from .pro_menu import ProMenu

ROUTE = 'codex_web_gpt'
PARALLEL = 5


def archived_unsent(db, output, batch, control, traces):
    from .formula_dispatch import historical_slot_receipt
    folder = output/'batches'/f'{batch:06d}'
    job = f'formula-display-{batch}'
    if any((folder/n).exists() for n in ('attempt.json','response.txt','records.jsonl','app-job.json')):
        return False
    marker = read(folder/'entry-retry'/'original.json')
    prior = db.execute('select admitted_at from entry_retries where batch=?',(batch,)).fetchone()
    packet = read(folder/'packet.json')
    status = read(folder/'status.json')
    events = traces.events.get(job,[])
    if prior:
        old = marker.get('attempt') or {}
        release = folder/'unsent-slot-release.json'
        return (marker.get('phase')=='admitted' and marker.get('queued_at')==prior[0]
                and old==read(folder/'entry-retry'/'attempt.json') and marker.get('packet')==packet
                and marker.get('status')==status and marker.get('release')==read(release)
                and len(events)==2 and events==marker.get('upload_events')
                and historical_slot_receipt(control,output,batch,'held',old.get('window_target'),old,release))
    # This exact terminal path occurs before a tab is selected or an attempt is written.
    return (set(p.name for p in folder.iterdir())=={'packet.json','batch.zip','status.json','account-check.json'}
            and not events and status.get('state')=='blocked'
            and status.get('reason')=='没有通过原所有者守卫的空闲页'
            and (status.get('last') or {}).get('state')=='checking_account'
            and status.get('pid') and status['pid']==status['last'].get('pid')
            and packet.get('batch')==batch and packet.get('sha256')==digest(folder/'batch.zip'))


def admit(db, output, *, control=None, traces=None):
    # An existing legacy batch directory can carry pre-click, pending, or archived
    # transfers. Such batches require archived non-submission proof.
    queued = db.execute("select id from batches where state='queued'").fetchall()
    if not queued:
        return
    folders = {int(p.name) for p in (output/'batches').iterdir() if p.name.isdigit()}
    complete_trace = traces is not None and traces.refresh()
    with db:
        for (batch,) in queued:
            recovered = batch in folders and complete_trace and archived_unsent(db,output,batch,control,traces)
            if recovered or batch not in folders:
                db.execute("""update batches set state='app_queued' where id=? and state='queued'
                    and not exists(select 1 from pending_collections where batch=?)
                    and (? or not exists(select 1 from entry_retries where batch=?))
                    and not exists(select 1 from outputs where batch=?)""", (batch,batch,bool(recovered),batch,batch))


def material(config, root, folder, batch, db, *, answer_format=None):
    sha = display_equations.build_packet(db,config,root,folder,batch)
    staged = folder/'app-input'
    staged.mkdir(exist_ok=True)
    with zipfile.ZipFile(folder/'batch.zip') as z:
        rows = json.loads(z.read('manifest.json'))
        if not 1 <= len(rows) <= 8:
            raise ValueError('整页图数量不符合当前批次合同')
        images = []
        pages = []
        for n,r in enumerate(rows,1):
            data = z.read(r['image'])
            if hashlib.sha256(data).hexdigest()!=r['sha256']:
                raise ValueError('原页 JPEG 指纹不匹配')
            path = staged/f'page-{n:02}.jpg'
            if not path.exists() or digest(path)!=r['sha256']:
                tmp = path.with_suffix('.tmp')
                tmp.write_bytes(data)
                tmp.replace(path)
            images.append(path)
            pages.append(dict(image=path.name,paper_id=r['paper_id'],pdf_page=r['pdf_page'],crop_id=r['crop_id'],
                              lines=json.loads(z.read(r['layout']))))
    write(staged/'layouts.json',pages)
    prompt = (display_equations.PROMPT.replace('解压 ZIP，','').replace('layout.json','layouts.json')
              .replace('从同一 ZIP 重新读取该 JPEG','查看本次同序附上的 JPEG') + str(batch)
              + '。附件按 page-01.jpg 起顺序对应下列页面。用本地只读命令读取当前目录的 layouts.json 获取逐行坐标。'
              + '只使用本任务页图和文字层。页面对应表：'
              + json.dumps([{k:v for k,v in page.items() if k!='lines'} for page in pages],ensure_ascii=False))
    if answer_format == 'fenced-jsonl-v1':
        prompt += '。把全部 JSONL 放在一个以三个反引号包围的 jsonl 代码块内。键名原样保留下划线。'
    elif answer_format is not None:
        raise ValueError('未知的冻结回答格式')
    return sha, rows, images, prompt


INSPECTOR_BUSY = 'App 正在处理回合，等待核对内置账户'


class AccountCheck:
    """Share recent authentication evidence only within the same live App session."""
    def __init__(self):
        self.lock = Lock()
        self.identity = None
        self.generation = 0
        self.confirmed_at = None

    def invalidate(self):
        self.generation += 1
        self.confirmed_at = None

    def verify(self, client):
        health = client.health()
        home = Path.home()/'.codex-chatgpt-web'
        app_config = home/'config.json'
        descriptor = read(Path(read(app_config).get('browserHostDescriptorPath') or home/'runtime/launcher-browser.json'))
        # The launcher rewrites surfaceTargets and createdAt as turns finish.
        # Bind only the authenticated launcher instance, account partition and control channel.
        channel = descriptor.get('control') or {}
        launcher = (descriptor.get('pid'),descriptor.get('partition'),descriptor.get('profile'),
                    channel.get('endpoint'),channel.get('token'))
        if not all(launcher):
            self.invalidate()
            return 'App 启动器会话身份未确认'
        stamp = (health.get('pid'),digest(app_config),hashlib.sha256(json.dumps(launcher).encode()).digest())
        if self.identity != stamp:
            self.invalidate()
            self.identity = stamp
        if not health.get('ready') or type(stamp[0]) is not int:
            self.invalidate()
            return 'App 服务未就绪'
        reason = gate()
        if reason is None:
            self.confirmed_at = time.monotonic()
        elif reason == INSPECTOR_BUSY:
            if (self.confirmed_at is not None and time.monotonic()-self.confirmed_at<=60
                    and 0 < (health.get('active_browser_turns') or 0) < PARALLEL):
                return None
        else:
            self.invalidate()
        return reason

    def completed(self, token, receipt):
        with self.lock:
            if token != self.generation:
                return
            if receipt.get('state')=='executed' and receipt.get('commands',0)>0:
                self.confirmed_at = time.monotonic()
            elif receipt.get('state')=='review':
                self.invalidate()


def gate():
    home = Path.home()/'.codex-chatgpt-web'
    app = read(home/'config.json')
    if (app.get('browserHost') != 'launcher' or app.get('browserInteractionMode') != 'automatic'
            or app.get('useTemporaryChats') is not True or app.get('mode') != 'full'):
        return '请在 Codex Web GPT 启用内置浏览器、自动交互、Full 模式及临时聊天'
    # browser check asks the launcher's own session inspector for authenticated
    # new-chat evidence. The generic bridge health endpoint cannot establish it.
    command = app.get('runtimeCommand')
    if not isinstance(command,list) or len(command)!=2:
        return 'Codex Web GPT 运行配置缺失'
    runtime, cli = map(Path,command)
    release = cli.parent.parent
    if (release.parent!=home/'versions' or cli!=release/'app/cli.js' or runtime!=release/'runtime/bun'
            or not cli.is_file() or not runtime.is_file()):
        return 'Codex Web GPT 运行目录待核对'
    try:
        check = subprocess.run([str(runtime),str(cli),'browser','check'],capture_output=True,text=True,timeout=30)
    except (OSError,subprocess.TimeoutExpired):
        return 'App 内置浏览器账户检查未完成'
    if check.returncode and re.fullmatch(
            r'codex-chatgpt-web: Launcher ChatGPT session could not be verified: ChatGPT browser is running Codex turn [a-f0-9-]+',
            (getattr(check,'stderr','') or '').strip(), re.I):
        return INSPECTOR_BUSY
    if check.returncode or 'authenticated ChatGPT surface embedded in the launcher' not in check.stdout:
        return 'App 内置浏览器未确认登录，请在 Codex Web GPT 内检查账户'


def sources_ok(config, root, rows):
    for paper,sha in {(r['paper_id'],r['source_sha256']) for r in rows}:
        a = read(root/'articles'/(paper+'.json'))
        if (a.get('source_sha256')!=sha or not allowed(config,paper) or not fresh(config,dict(
                id=paper,source_hash=sha,source_path=a['source_path']),for_upload=True)):
            raise ValueError('发送前原文或 OLED 准入发生变化：'+paper)


def set_state(db, batch, state, reason=None):
    with db:
        db.execute('update batches set state=?,reason=? where id=?',(state,reason,batch))


def prepare_job(client, db, config, root, folder, batch):
    prior = read(folder/'app-job.json')
    answer_format = prior.get('answer_format') if prior else 'fenced-jsonl-v1'
    sha, rows, images, prompt = material(config,root,folder,batch,db,answer_format=answer_format)
    sources_ok(config,root,rows)
    key = f'oled-{batch}-{sha}'
    if prior and (prior.get('key'),prior.get('sha256'),prior.get('prompt'))!=(key,sha,prompt):
        raise ValueError('已有 App 请求与冻结材料不一致')
    if not prior:
        write(folder/'app-job.json',dict(key=key,sha256=sha,prompt=prompt,answer_format=answer_format))
    client.submit(key,prompt,workdir=folder/'app-input',require_command=True,images=images,guarded=True)
    set_state(db,batch,'app_prepared')


def dispatch_job(client, config, root, output, batch, active, slot, guard):
    folder = output/'batches'/f'{batch:06d}'
    job = read(folder/'app-job.json')
    key = job['key']
    receipt = client.get(key)
    if receipt['state'] not in ('queued','sending'):
        return receipt

    token = None
    def before_send(task_id):
        nonlocal token
        with guard.lock:
            if task_id!=key or not active():
                return '任务已暂停'
            block = guard.verify(client)
            if block:
                return block
            if not (folder/'packet.json').is_file():
                raise ValueError('冻结材料清单缺失')
            with closing(sqlite3.connect((output/'queue.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
                sha,rows,_,prompt = material(config,root,folder,batch,db,answer_format=job.get('answer_format'))
            if sha!=job['sha256'] or prompt!=job['prompt'] or key!=f'oled-{batch}-{sha}':
                raise ValueError('冻结材料或提示变化')
            sources_ok(config,root,rows)
            token = guard.generation
            return None if active() else '任务已暂停'

    receipt = client.run_once(key=key,before_send=before_send,pro_first=True,parallel_slot=slot,
                              allow_pro=slot in guard.pro_slots)
    if token is not None and receipt.get('id')==key:
        guard.completed(token,receipt)
    return client.get(key) if receipt['state']=='idle' else receipt


def collect_job(db, control, root, output, batch, receipt):
    folder = output/'batches'/f'{batch:06d}'
    job = read(folder/'app-job.json')
    key = job['key']
    if receipt.get('id')!=key or receipt['state']!='executed':
        set_state(db,batch,'review','App 回执待核对：'+str(receipt.get('reason') or receipt['state']))
        return
    rec = dict(state='raw_saved',transport=ROUTE,job_id=f'formula-display-{batch}',app_job=key,
               zip_sha256=job['sha256'],model={('chatgpt-web/gpt-6-pro','max'):'GPT-6 Pro',
               ('chatgpt-web/gpt-6.2-sol','xhigh'):'GPT-6.2 Sol Extra High',
               ('chatgpt-web/gpt-6.2-sol','high'):'GPT-6.2 Sol High'}[
                   (receipt.get('model','chatgpt-web/gpt-6.2-sol'),receipt.get('effort','high'))],prompt=job['prompt'],
               temporary=True,raw_sha256=hashlib.sha256(receipt['answer'].encode()).hexdigest())
    old = read(folder/'attempt.json')
    if old and old!=rec:raise ValueError('批次已有其他回执')
    replace_text(folder/'response.txt',receipt['answer'])
    write(folder/'attempt.json',rec)
    save_formulas(dict(control,batch=batch),folder,rec,lambda *a,**kw:None)
    records = [json.loads(line) for line in (folder/'records.jsonl').read_text().splitlines()]
    if any(item.get('kind')=='unreadable' for item in records):
        set_state(db,batch,'review','App 回答中有不可读图页，原回答已保存')
    else:
        publish(db,root,output,batch,folder)


def run(config, control, db, output, active):
    from .formula_dispatch import index_paper_order
    from .formula_queue import recover_publications
    root = Path(control['folder'])
    base = Path(config['catalog_path']).parent
    state_dir = Path.home()/'.local/state/codex-web-client-oled'/hashlib.sha256(str(output.resolve()).encode()).hexdigest()[:16]
    client = Client(state_dir,timeout=900)
    from .entry_retry import EntryTraces
    admit(db,output,control=control,traces=EntryTraces(base/'upload-attempt-events.jsonl'))
    index_paper_order(db)
    running = {}
    guard = AccountCheck()
    menu = ProMenu(base / ('oled-pro-menu-' + state_dir.name + '.json'),
                   Path.home()/'.codex-chatgpt-web/diagnostics/browser-turns')
    recover_at = retry_at = 0
    last_status = None
    reason = None

    def status(stage):
        nonlocal last_status
        counts = dict(db.execute('select state,count(*) from batches group by state'))
        batches = sorted(running)
        values = dict(state=stage,batches=batches,batch=next(iter(batches),None),parallel_limit=PARALLEL,
                      reason=reason,counts=counts,pro_menu=menu.state)
        if values!=last_status:
            write(output/'app-status.json',dict(route=ROUTE,pid=os.getpid(),time=time.time(),**values))
            last_status = values

    errors = (ValueError,KeyError,TypeError,zipfile.BadZipFile)
    with ThreadPoolExecutor(max_workers=PARALLEL,thread_name_prefix='oled-app') as pool:
        while active():
            now = time.monotonic()
            wall_time = time.time()
            if running:
                menu.observe(wall_time)
            guard.pro_slots = tuple(menu.state['pro_slots'])
            for batch,(slot,future) in list(running.items()):
                if not future.done():
                    continue
                del running[batch]
                try:
                    receipt = future.result()
                    if (receipt.get('effort') == 'max' and receipt.get('state') == 'review'
                            or receipt.get('reason') == 'model_quota_before_send' and
                            client.get(receipt['id']).get('effort') == 'max'):
                        menu.retire_slot(slot, receipt.get('id'))
                        guard.pro_slots = tuple(menu.state['pro_slots'])
                    if receipt['state'] in ('unavailable','busy','cooldown'):
                        reason = receipt.get('reason',receipt['state'])
                        retry_at = now+5
                    else:
                        collect_job(db,control,root,output,batch,receipt)
                except errors as exc:
                    if db.execute('select state from batches where id=?',(batch,)).fetchone()!=('publishing',):
                        set_state(db,batch,'review',str(exc)[:500])
                except (OSError,sqlite3.Error) as exc:
                    reason,retry_at = str(exc)[:250],now+5
            if now>=recover_at:
                recover_at = now+300
                recover_publications(db,root,output,active)
            if now>=retry_at and len(running)<PARALLEL:
                reason = None
                candidates = db.execute("""select b.id,b.state from batches b join formula_paper_order p on p.batch=b.id
                    where b.state in ('app_queued','app_prepared')
                    order by case b.state when 'app_prepared' then 0 else 1 end,p.first_batch,b.id limit ?""",
                    (PARALLEL,)).fetchall()
                if not candidates and not running:
                    status('finished')
                    return
                for batch,previous in candidates:
                    if batch in running or not active() or len(running)>=PARALLEL:
                        continue
                    folder = output/'batches'/f'{batch:06d}'
                    try:
                        if previous=='app_queued':
                            prepare_job(client,db,config,root,folder,batch)
                        used = {slot for slot,_ in running.values()}
                        slot = next(s for s in range(PARALLEL) if s not in used)
                        future = pool.submit(dispatch_job,client,config,root,output,batch,active,slot,guard)
                        running[batch] = slot,future
                        status('dispatching')
                    except errors as exc:
                        set_state(db,batch,'held' if previous=='app_queued' else 'review',str(exc)[:500])
                    except (OSError,sqlite3.Error) as exc:
                        reason,retry_at = str(exc)[:250],time.monotonic()+5
                        break
            status('dispatching' if running else 'waiting_app')
            if running:
                wait([future for _,future in running.values()],timeout=2,return_when=FIRST_COMPLETED)
            elif retry_at>now:
                time.sleep(min(2,retry_at-now))
