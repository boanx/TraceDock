"""GitHub release updates, verified with the pinned TraceDock signing key."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request

API = 'https://api.github.com/repos/boanx/TraceDock/releases/latest'
PREFIX = 'https://github.com/boanx/TraceDock/releases/download/'
SIGNER = '21059835+boanx@users.noreply.github.com'
KEY = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMgrU6O7C05fqU1xlcTIIkLnq4XZSjDSe8IhXM7PdlJK'


def version(text):
    match = re.fullmatch(r'v?(\d+)\.(\d+)(?:\.(\d+))?', text)
    if not match:raise ValueError('Geçersiz sürüm numarası.')
    return tuple(int(value or 0) for value in match.groups())


def request(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'TraceDock-Updater'}), timeout=8)


def latest(current):
    with request(API) as response:info=json.loads(response.read(2*1024*1024))
    if info.get('draft') or info.get('prerelease') or version(info['tag_name'])<=version(current):return None
    assets={item['name']:item for item in info['assets']}
    for name in ('TraceDock.exe','TraceDock.exe.sig'):
        item=assets[name]
        if item['browser_download_url']!=PREFIX+info['tag_name']+'/'+name:raise ValueError('Beklenmeyen indirme adresi.')
        if not 0<int(item['size'])<=512*1024*1024:raise ValueError('Geçersiz dosya boyutu.')
    return {'version':info['tag_name'],'assets':assets}


def verify(exe, signature, directory):
    program=Path(os.environ.get('WINDIR',r'C:\Windows'))/'System32/OpenSSH/ssh-keygen.exe'
    if not program.is_file():raise ValueError('İmza doğrulaması için Windows OpenSSH gerekli. Güncellemeyi GitHub üzerinden elle indirebilirsiniz.')
    signers=directory/'allowed_signers'
    signers.write_text(SIGNER+' '+KEY+'\n',encoding='utf-8')
    with exe.open('rb') as source:
        result=subprocess.run([str(program),'-Y','verify','-f',str(signers),'-I',SIGNER,'-n','file','-s',str(signature)],stdin=source,capture_output=True,timeout=45,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode:raise ValueError('Güncellemenin kriptografik imzası doğrulanamadı.')


def download(info, progress, check):
    directory=Path(tempfile.mkdtemp(prefix='TraceDock-update-'))
    try:
        for index,name in enumerate(('TraceDock.exe','TraceDock.exe.sig')):
            item=info['assets'][name];total=int(item['size']);written=0
            with request(item['browser_download_url']) as response, (directory/name).open('wb') as output:
                while True:
                    check();block=response.read(1024*1024)
                    if not block:break
                    written+=len(block)
                    if written>total:raise ValueError('İndirme boyutu beklenenden büyük.')
                    output.write(block);progress((index+written/total)/2,name)
            if written!=total:raise ValueError('İndirme tamamlanamadı.')
        check();verify(directory/'TraceDock.exe',directory/'TraceDock.exe.sig',directory);check()
        return directory
    except BaseException:
        shutil.rmtree(directory)
        raise


def clean_environment():
    env={key:value for key,value in os.environ.items() if not key.startswith(('_PYI','_MEI'))}
    env['PYINSTALLER_RESET_ENVIRONMENT']='1'
    return env


def launch(directory, target, pid):
    target=Path(target).resolve()
    backup=target.with_name(target.name+'.update-backup')
    if backup.exists():raise ValueError('Önceki güncelleme yedeği mevcut: '+str(backup))
    with tempfile.TemporaryFile(dir=target.parent):pass
    helper=directory/'TraceDock-updater.exe'
    shutil.copy2(target,helper)
    return subprocess.Popen([str(helper),'--install-update',str(target),str(int(pid))],env=clean_environment(),close_fds=True)


def install(target, pid):
    """Run only from the detached copy of the current signed application."""
    import ctypes
    import sys
    directory=Path(sys.executable).resolve().parent
    target=Path(target).resolve();backup=target.with_name(target.name+'.update-backup')
    incoming=directory/'TraceDock.exe'
    try:
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.restype=ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
        kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        handle=kernel.OpenProcess(0x100000,False,int(pid))
        if handle:
            try:
                if kernel.WaitForSingleObject(handle,120000)!=0:raise ValueError('TraceDock kapanmadı; güncelleme iptal edildi.')
            finally:kernel.CloseHandle(handle)
        verify(incoming,directory/'TraceDock.exe.sig',directory)
        if backup.exists():raise ValueError('Önceki güncelleme yedeği mevcut.')
        for attempt in range(60):
            try:os.replace(target,backup);break
            except PermissionError:
                if attempt==59:raise
                time.sleep(.5)
        try:
            shutil.copy2(incoming,target)
            subprocess.Popen([str(target)],env=clean_environment(),cwd=str(target.parent),close_fds=True)
        except BaseException:
            os.replace(backup,target)
            raise
        backup.unlink()
        for path in (incoming,directory/'TraceDock.exe.sig',directory/'allowed_signers'):
            path.unlink(missing_ok=True)
    except Exception as exc:
        ctypes.windll.user32.MessageBoxW(None,str(exc),'TraceDock güncelleme hatası',0x10)
        return 1
    return 0
