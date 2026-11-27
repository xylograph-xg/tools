"""Attachment snapshots, composer evidence, and native picker selection."""
from pathlib import Path
import hashlib
import os
import time
from .errors import DesktopChatError

MAX_FILES = 10
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024

def validate_files(files):
    if files is None: return []
    if not isinstance(files, (list, tuple)) or len(files) > MAX_FILES:
        raise ValueError('files must be a list/tuple of at most 10 absolute file paths')
    paths = []; names = set(); total = 0
    for value in files:
        if not isinstance(value, (str, Path)):
            raise ValueError('Each attachment must be an absolute file path')
        path = Path(value).expanduser()
        if not path.is_absolute() or '\n' in str(path) or '\r' in str(path):
            raise ValueError('Attachment paths must be absolute without line breaks')
        path = path.resolve(strict=True)
        if not path.is_file(): raise ValueError('Attachment must be a regular file')
        stat = path.stat(); total += stat.st_size
        if not 0 < stat.st_size <= MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
            raise ValueError('Local attachment limit: 1..64 MiB each, at most 128 MiB total')
        if path.name.casefold() in names:
            raise ValueError('Duplicate attachment basenames are ambiguous')
        names.add(path.name.casefold()); paths.append(path)
    return paths

def snapshot_files(paths, folder):
    folder = Path(folder); folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    out = []
    for path in paths:
        before = path.stat(); target = folder / path.name
        digest = hashlib.sha256(); count = 0
        with path.open('rb') as src, target.open('xb') as dst:
            os.chmod(target, 0o600)
            while block := src.read(1024 * 1024):
                count += len(block)
                if count > MAX_FILE_BYTES: raise DesktopChatError('attachment_changed', 'Attachment grew while snapshotting')
                digest.update(block); dst.write(block)
            dst.flush(); os.fsync(dst.fileno())
        after = path.stat()
        if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns) != (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) or count != before.st_size:
            raise DesktopChatError('attachment_changed', 'Source attachment changed while snapshotting')
        out.append({'name':path.name,'source_path':str(path),'snapshot_path':str(target),
                    'size':count,'sha256':digest.hexdigest()})
    return out

def verify_snapshots(files):
    for item in files:
        p = Path(item['snapshot_path'])
        with p.open('rb') as f:
            h = hashlib.sha256()
            while block := f.read(1024 * 1024): h.update(block)
            digest = h.hexdigest()
        if p.stat().st_size != item['size'] or digest != item['sha256']:
            raise DesktopChatError('attachment_changed', 'Prepared attachment fingerprint changed')

def _descendants(nodes, root):
    wanted = {root}; out = []
    for n in nodes:
        if n['id'] == root or n.get('parent') in wanted:
            wanted.add(n['id']); out.append(n)
    return out

def composer_nodes(snapshot):
    nodes = snapshot['nodes']; by_id = {n['id']:n for n in nodes}
    editors = [n for n in nodes if n['role']=='AXTextArea' and (n.get('title')=='询问 ChatGPT' or n.get('description')=='询问 ChatGPT')]
    if len(editors)!=1: raise DesktopChatError('ambiguous_editor','Attachment evidence needs one Chat editor')
    root = editors[0].get('parent')
    if root not in by_id: raise DesktopChatError('attachment_structure','Cannot bind attachment evidence to composer')
    return _descendants(nodes, root)

def attachment_names(snapshot):
    names = []
    for n in composer_nodes(snapshot):
        label = n.get('title') or n.get('description') or ''
        if n['role']=='AXButton' and label.startswith('移除'):
            name = label[2:].strip().strip('“”"')
            if not name: raise DesktopChatError('attachment_structure','Unnamed attachment cannot be verified')
            names.append(name)
    return names

def upload_evidence(snapshot, expected):
    composer = composer_nodes(snapshot)
    text = '\n'.join(' '.join(str(n.get(k,'')) for k in ('title','description','value')) for n in composer)
    # Toasts supplement failure evidence, never establish readiness. Avoid sidebar/history text.
    notices = []
    for n in snapshot['nodes']:
        if n.get('role') in ('AXAlert','AXDialog') or (n.get('role')=='AXGroup' and (n.get('title','').startswith('通知') or n.get('description','').startswith('通知'))):
            notices.extend(_descendants(snapshot['nodes'],n['id']))
    all_text = text + '\n' + '\n'.join(n.get('value','')+n.get('title','')+n.get('description','') for n in notices)
    if any(t in all_text for t in ('上传未成功','上传失败','Upload failed')):
        raise DesktopChatError('attachment_upload_failed','App reports attachment upload failure; message was not sent')
    if any(t in all_text for t in ('已达上传上限','上传次数已用完','upload limit')):
        raise DesktopChatError('attachment_quota','App reports upload quota; no automatic retry or model switch')
    names = attachment_names(snapshot)
    if len(names)!=len(set(names)) or set(names)-set(expected):
        raise DesktopChatError('attachment_mismatch','Foreign or duplicate composer attachment; existing files are protected')
    progress = [n for n in composer if n['role']=='AXProgressIndicator' or any(t in n.get('title','')+n.get('description','') for t in ('正在上传','Uploading'))]
    sends = [n for n in composer if n['role']=='AXButton' and (n.get('title')=='发送' or n.get('description')=='发送')]
    return {'names':names,'uploading':bool(progress),'ready':set(names)==set(expected) and not progress and len(sends)==1 and sends[0].get('enabled') is True}

def choose_file(backend, path, pid):
    """Caller holds the global UI lock across this exact window-owned file panel."""
    backend.call("activate",allow_foreground=True,expected_pid=pid)
    backend.press({'role':'AXButton','label':'添加文件等内容'},expected_pid=pid,allow_foreground=True)
    deadline = time.monotonic()+8
    while True:
        s=backend.snapshot()
        buttons=[n for n in s['nodes'] if n['role']=='AXButton' and n.get('title')=='添加照片和文件 从计算机上传']
        if len(buttons)==1: break
        if time.monotonic()>deadline: raise DesktopChatError('file_picker_unavailable','Upload menu did not appear')
        time.sleep(.1)
    backend.call('click',query={'role':'AXButton','label':'添加照片和文件 从计算机上传'},allow_foreground=True,expected_pid=pid)
    deadline = time.monotonic()+8
    while True:
        s=backend.snapshot()
        if sum(n['role']=='AXSheet' and n.get('description')=='打开' for n in s['nodes'])==1: break
        if time.monotonic()>deadline: raise DesktopChatError('file_picker_unavailable','Original window Open sheet did not appear')
        time.sleep(.1)
    backend.call('key',query={'role':'AXSheet','description':'打开'},keycode=5,modifiers=['command','shift'],allow_foreground=True,expected_pid=pid)
    deadline = time.monotonic()+8
    while True:
        s=backend.snapshot(); by_id={n['id']:n for n in s['nodes']}; fields=[]
        for n in s['nodes']:
            parent=by_id.get(n.get('parent'),{}); grandparent=by_id.get(parent.get('parent'),{})
            if n['role']=='AXTextField' and parent.get('role')=='AXSheet' and grandparent.get('role')=='AXSheet' and grandparent.get('description')=='打开': fields.append(n)
        if len(fields)==1: break
        if time.monotonic()>deadline: raise DesktopChatError('file_picker_unavailable','Go To path field is not unique')
        time.sleep(.1)
    backend.call('set_path',query={'role':'AXTextField','value':fields[0].get('value','')},path=str(path),allow_foreground=True,expected_pid=pid)
    backend.call('key',query={'role':'AXTextField','value':str(path)},expected_value=str(path),keycode=36,allow_foreground=True,expected_pid=pid)
    deadline = time.monotonic()+8
    while True:
        s=backend.snapshot()
        sheets=[n for n in s['nodes'] if n['role']=='AXSheet']
        if len(sheets)==1 and sheets[0].get('description')=='打开':
            panel=_descendants(s['nodes'],sheets[0]['id'])
            previews=[n for n in panel if n['role']=='AXStaticText' and n.get('value')==Path(path).name]
            buttons=[n for n in panel if n['role']=='AXButton' and n.get('title')=='打开' and n.get('enabled')]
            if previews and len(buttons)==1: break
        if time.monotonic()>deadline: raise DesktopChatError('file_selection_unknown','Exact file preview/Open button not confirmed; retain original panel')
        time.sleep(.1)
    backend.press({'role':'AXButton','title':'打开'},expected_pid=pid,allow_foreground=True)

def image_file_names(files):
    """Only previously verified immutable image bytes permit anonymous image receipts."""
    out=[]
    for item in files:
        if not item.get('upload_ready'): continue
        with Path(item['snapshot_path']).open('rb') as f: header=f.read(16)
        if header.startswith(b'\x89PNG\r\n\x1a\n') or header.startswith(b'\xff\xd8\xff') or header.startswith((b'GIF87a',b'GIF89a')) or (header.startswith(b'RIFF') and header[8:12]==b'WEBP'):
            out.append(item['name'])
    return out

def formal_attachment_evidence(snapshot, wire, expected, image_names=()):
    if not expected: return True
    nodes=snapshot['nodes']; by_id={n['id']:n for n in nodes}
    anchors=[n for n in nodes if n['role']=='AXStaticText' and n.get('value')==wire]
    if len(anchors)!=1: return False
    parent=anchors[0].get('parent')
    for _ in range(12):
        if parent not in by_id: break
        group=_descendants(nodes,parent)
        if any(n['role']=='AXTextArea' for n in group): break
        headings=[n for n in group if n['role']=='AXHeading' and ('你说' in (n.get('title','')+n.get('description','')) or 'You said' in n.get('title',''))]
        if len(headings)>1: break
        # Do not use assistant text or a later turn to prove a user attachment.
        assistant=next((i for i,n in enumerate(group) if n['role']=='AXHeading' and ('ChatGPT 说' in n.get('title','') or 'ChatGPT said' in n.get('title',''))),len(group))
        user=group[:assistant]
        names=set()
        for n in user:
            if n['role']=='AXImage': names.update((n.get('title',''),n.get('description','')))
            elif n['role']=='AXStaticText' and n.get('value')!=wire: names.add(n.get('value',''))
        if set(expected)<=names: return True
        # App formally renders images as anonymous 'user attachment' buttons. Bind count
        # to this exact turn AND the immutable upload-ready file/atomic-send evidence.
        anonymous=sum(n['role']=='AXButton' and (n.get('title')=='用户附件' or n.get('description')=='用户附件') for n in user)
        missing=set(expected)-names
        if missing and missing<=set(image_names) and anonymous==len(missing): return True
        parent=by_id[parent].get('parent')
    return False

def channel_issue(snapshot):
    # Exact native banner prefixes; never infer a reset time from local cooldowns.
    for n in snapshot['nodes']:
        text=n.get('value','')
        if n['role']=='AXStaticText' and text.startswith(('你目前已用完附件额度。','已达上传上限','已达到上传上限')):
            return {'code':'attachment_quota','message':text,'window_id':snapshot['window_id'],'pid':snapshot['pid']}
    return None
