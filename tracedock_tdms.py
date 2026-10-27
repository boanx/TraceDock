"""Sequential TDMS import with bounded memory and application-owned staging."""
from pathlib import Path
import math
import tempfile
import time
import numpy as np
from nptdms import TdmsFile


def stage_tdms(path,progress=None,check_cancel=None):
    """Copy once, then decode all channels in one local pass; caller owns the cache."""
    check=check_cancel or (lambda:None)
    report=progress or (lambda fraction,message:None)
    cache=tempfile.TemporaryDirectory(prefix='tracedock-tdms-')
    local=Path(cache.name)/'source.tdms'
    mapped={}
    try:
        check();source=Path(path);before=source.stat();copied=0
        report(0.,'TDMS geçici alana alınıyor')
        with source.open('rb') as reader,local.open('wb') as writer:
            while True:
                check();block=reader.read(8*1024*1024)
                if not block:break
                writer.write(block);copied+=len(block)
                report(.45*min(1.,copied/max(1,before.st_size)),f'{copied/2**20:.1f} / {before.st_size/2**20:.1f} MiB alındı')
        check();after=source.stat()
        if copied!=before.st_size or (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise ValueError('TDMS kopyalanırken kaynak dosya değişti. Kayıt tamamlandıktan sonra yeniden açın.')
        channels=[];counts={};total=0;completed=0;last_report=0.
        with TdmsFile.open(local) as tdms:
            for group in tdms.groups():
                for ch in group.channels():
                    check();dtype=np.dtype(ch.dtype)
                    if dtype.kind not in 'iufb':raise ValueError(f'{group.name}/{ch.name} sayısal olmayan veri içeriyor.')
                    props=ch.properties;rate=''
                    try:
                        increment=float(props.get('wf_increment',0));hz=1/increment if increment>0 else 0
                        if math.isfinite(hz) and hz>0:rate=format(hz,'.17g')
                    except (ValueError,TypeError,ZeroDivisionError):pass
                    key=(group.name,ch.name);target=Path(cache.name)/f'channel-{len(channels)}.npy'
                    if len(ch):mapped[key]=np.lib.format.open_memmap(target,mode='w+',dtype=dtype,shape=(len(ch),))
                    else:np.save(target,np.empty(0,dtype=dtype),allow_pickle=False)
                    counts[key]=0;total+=len(ch)
                    channels.append({'name':f'{group.name}/{ch.name}','cache_path':str(target),'unit':str(props.get('unit_string',props.get('unit',''))),'id':str(props.get('NI_ChannelNumber',ch.name)),'default_rate':rate})
            if not channels:raise ValueError('TDMS dosyasında kanal bulunamadı.')
            report(.45,'TDMS kanalları yerel dosyadan birlikte okunuyor')
            for chunk in tdms.data_chunks():
                check()
                for group in chunk.groups():
                    for ch in group.channels():
                        check();size=len(ch)
                        if not size:continue
                        key=(group.name,ch.name);start=ch.offset;stop=start+size
                        if key not in mapped or start!=counts[key] or stop>len(mapped[key]):
                            raise ValueError('TDMS kanal örnek sırası veya uzunluğu tutarsız: '+group.name+'/'+ch.name)
                        mapped[key][start:stop]=ch[:];counts[key]=stop;completed+=size
                now=time.monotonic()
                if now-last_report>=.1:
                    report(.45+.5*completed/max(1,total),f'{completed:,} / {total:,} kanal örneği okundu');last_report=now
        for key,values in mapped.items():
            check()
            if counts[key]!=len(values):raise ValueError('TDMS kanalında eksik örnek: '+key[0]+'/'+key[1])
            values.flush()
        for values in mapped.values():values._mmap.close()
        mapped.clear();local.unlink();check();report(1.,f'{len(channels)} kanal hazır')
        return channels,cache
    except BaseException:
        for values in mapped.values():values._mmap.close()
        mapped.clear();cache.cleanup();raise
