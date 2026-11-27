"""Local, content-addressed ZIP preparation. Never opens an app or sends data."""
from pathlib import Path
import hashlib
import json
import os
import tempfile
import zipfile
import stat
from .attachments import validate_files, MAX_TOTAL_BYTES, MAX_FILE_BYTES
from .errors import DesktopChatError

MANIFEST = '_upload_manifest.json'

def default_bundle_dir():
    configured=os.environ.get('CODEX_CHAT_ZIP_DIR')
    if configured:return Path(configured).expanduser().resolve()
    return Path.home() / 'process' / 'app-upload-zips'


def _hash_file(path):
    h=hashlib.sha256(); count=0
    with path.open('rb') as f:
        while block:=f.read(1024*1024):
            count+=len(block)
            if count>MAX_FILE_BYTES:raise DesktopChatError("attachment_changed","Source grew beyond local limit")
            h.update(block)
    return h.hexdigest()

def verify_bundle(path):
    """Reject corrupt, encrypted, unsafe or oversized archives before any upload."""
    path=Path(path).resolve(strict=True)
    if not 0<path.stat().st_size<=MAX_FILE_BYTES:
        raise DesktopChatError('bundle_too_large','ZIP exceeds local 64MiB upload limit')
    try:
        with zipfile.ZipFile(path) as z:
            infos=z.infolist();names=[i.filename for i in infos]
            if not infos or len(names)!=len(set(names)) or len(infos)>100:
                raise ValueError('Empty, duplicate or excessive ZIP entries')
            total=0
            items=None
            for i in infos:
                parts=Path(i.filename).parts
                kind=stat.S_IFMT(i.external_attr >> 16)
                if kind not in (0, stat.S_IFREG):raise ValueError('Non-regular ZIP entry')
                if i.flag_bits&1 or i.filename.startswith('/') or '..' in parts or '\\' in i.filename or i.is_dir():
                    raise ValueError('Unsafe/encrypted ZIP entry')
                total+=i.file_size
                if i.file_size>MAX_FILE_BYTES or total>MAX_TOTAL_BYTES+1024*1024:raise ValueError('Expanded ZIP exceeds local limits')
            if z.testzip() is not None:raise ValueError('ZIP checksum failure')
            if MANIFEST in names:
                if z.getinfo(MANIFEST).file_size>1024*1024:raise ValueError('Oversized manifest')
                manifest=json.loads(z.read(MANIFEST))
                items=manifest['files']
                if sorted(names)!=sorted([MANIFEST]+[i['name'] for i in items]):raise ValueError('Manifest entry mismatch')
                for item in items:
                    content=z.read(item['name'])
                    if len(content)!=item['size'] or hashlib.sha256(content).hexdigest()!=item['sha256']:raise ValueError('ZIP input fingerprint mismatch')
        return {'zip_path':str(path),'zip_sha256':_hash_file(path),'size':path.stat().st_size,'entries':names,'manifest_files':items}
    except (zipfile.BadZipFile,ValueError,KeyError,TypeError,RuntimeError) as e:
        raise DesktopChatError('bundle_invalid','ZIP cannot be verified: '+str(e)) from e

def _publish(tmp, target):
    # Publish without overwriting a concurrent winner or existing evidence.
    try:os.link(tmp, target)
    except FileExistsError:pass
    directory=os.open(target.parent,os.O_RDONLY)
    try:os.fsync(directory)
    finally:os.close(directory)

def prepare_upload_bundle(files, *, bundle_dir=None):
    paths=validate_files(files)
    if not paths:raise ValueError('At least one attachment is required to prepare a ZIP')
    if len(paths)==1 and paths[0].suffix.lower()=='.zip':
        verified=verify_bundle(paths[0])
        folder=Path(bundle_dir or default_bundle_dir()).expanduser().resolve();folder.mkdir(mode=0o700,parents=True,exist_ok=True)
        if paths[0].parent==folder:return {**verified,'reused':True,'prepacked':True}
        target=folder/(verified['zip_sha256']+'.zip')
        if target.exists():
            cached=verify_bundle(target)
            if cached['zip_sha256']!=verified['zip_sha256']:raise DesktopChatError('bundle_identity_mismatch','Cached ZIP differs from source archive')
            return {**cached,'reused':True,'prepacked':True}
        fd,tmp=tempfile.mkstemp(prefix='.packing-',suffix='.zip',dir=folder)
        try:
            with os.fdopen(fd,'wb') as out, paths[0].open('rb') as src:
                data=src.read(MAX_FILE_BYTES+1)
                if hashlib.sha256(data).hexdigest()!=verified['zip_sha256']:raise DesktopChatError('attachment_changed','ZIP changed before staging')
                out.write(data);out.flush();os.fsync(out.fileno())
            _publish(tmp,target)
        finally:Path(tmp).unlink(missing_ok=True)
        cached=verify_bundle(target)
        if cached['zip_sha256']!=verified['zip_sha256']:raise DesktopChatError('bundle_identity_mismatch','Published ZIP differs from source archive')
        return {**cached,'reused':False,'prepacked':True}
    if any(p.name==MANIFEST for p in paths):raise ValueError('Reserved upload manifest filename')
    items=[{'name':p.name,'size':p.stat().st_size,'sha256':_hash_file(p)} for p in sorted(paths,key=lambda p:p.name)]
    key=hashlib.sha256(json.dumps(items,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    folder=Path(bundle_dir or default_bundle_dir()).expanduser().resolve();folder.mkdir(mode=0o700,parents=True,exist_ok=True)
    target=folder/(key+'.zip')
    if target.exists():
        cached=verify_bundle(target)
        if cached['manifest_files']!=items:raise DesktopChatError('bundle_identity_mismatch','Cached ZIP differs from current source files')
        return {**cached,'reused':True,'prepacked':False}
    fd,tmp=tempfile.mkstemp(prefix='.packing-',suffix='.zip',dir=folder);os.close(fd)
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for path,item in zip(sorted(paths,key=lambda p:p.name),items):
                with path.open("rb") as f:content=f.read(MAX_FILE_BYTES+1)
                if len(content)!=item['size'] or hashlib.sha256(content).hexdigest()!=item['sha256']:
                    raise DesktopChatError('attachment_changed','Source changed while packing; ZIP not published')
                info=zipfile.ZipInfo(item['name'],date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o600<<16
                z.writestr(info,content)
            info=zipfile.ZipInfo(MANIFEST,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,json.dumps({'schema_version':1,'files':items},ensure_ascii=False,sort_keys=True).encode())
        result=verify_bundle(tmp)
        with open(tmp,'rb') as f:os.fsync(f.fileno())
        # Content addressing prevents duplicate packages for identical input sets.
        _publish(tmp,target)
        result=verify_bundle(target)
        if result['manifest_files']!=items:raise DesktopChatError('bundle_identity_mismatch','Published ZIP differs from current source files')
        return {**result,'reused':False,'prepacked':False}
    finally:Path(tmp).unlink(missing_ok=True)
