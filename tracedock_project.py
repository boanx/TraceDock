"""Portable .tdoc containers: JSON plus numeric NPY arrays, never pickle."""
import json
import math
import os
from pathlib import Path
import tempfile
import zipfile
import numpy as np
from tracedock_workers import memory_available


def freeze(value):
    return tuple(freeze(item) for item in value) if isinstance(value,list) else value


def save_project(path,manifest,arrays,progress=None,check=None):
    check=check or (lambda:None);report=progress or (lambda f,m:None)
    total=max(1,sum(v.nbytes for v in arrays.values()));written=0;temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=str(Path(path).parent),prefix='.tracedock-project-',suffix='.tmp',delete=False) as f:temporary=f.name
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
            for name,values in arrays.items():
                check()
                with archive.open(name,'w',force_zip64=True) as output:
                    class Writer:
                        def write(self,block):
                            nonlocal written
                            check();size=output.write(block);written+=size;report(min(.99,written/total),'Proje verileri kaydediliyor');return size
                        def flush(self):pass
                    np.save(Writer(),values,allow_pickle=False)
            archive.writestr('project.json',json.dumps(manifest,ensure_ascii=False,allow_nan=False,separators=(',',':')))
        check();os.replace(temporary,path);temporary=None;report(1.,'Proje kaydedildi')
    finally:
        if temporary:
            try:os.unlink(temporary)
            except OSError:pass


def load_project(path,progress=None,check=None):
    check=check or (lambda:None);report=progress or (lambda f,m:None)
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        if len(names)!=len(set(names)):raise ValueError('Proje arşivinde yinelenen kayıt var.')
        info=archive.getinfo('project.json')
        if info.file_size>32*1024*1024:raise ValueError('Proje üst bilgisi çok büyük.')
        def invalid(value):raise ValueError('Geçersiz proje sayısı: '+value)
        manifest=json.loads(archive.read(info).decode('utf-8'),parse_constant=invalid)
        if not isinstance(manifest,dict) or manifest.get('format')!='TraceDock-project' or manifest.get('schema')!=1:raise ValueError('Desteklenmeyen TDOC proje biçimi.')
        expected=manifest.get('arrays')
        if not isinstance(expected,list) or len(expected)!=len(set(expected)) or any(not isinstance(n,str) or not n.startswith('arrays/') or not n.endswith('.npy') for n in expected):raise ValueError('Geçersiz proje veri listesi.')
        total=sum(archive.getinfo(n).file_size for n in expected)
        if total>memory_available()[1]*.85:raise ValueError('Proje için kullanılabilir RAM yetersiz. Diğer büyük projeleri kapatıp tekrar deneyin.')
        arrays={};done=0
        for name in expected:
            check();info=archive.getinfo(name)
            with archive.open(info) as source:
                version=np.lib.format.read_magic(source)
                if version==(1,0):shape,order,dtype=np.lib.format.read_array_header_1_0(source)
                elif version==(2,0):shape,order,dtype=np.lib.format.read_array_header_2_0(source)
                else:raise ValueError('Desteklenmeyen proje dizisi sürümü.')
                if len(shape)!=1 or dtype.kind not in 'iufb' or shape[0]<0:raise ValueError('Proje verisi tek boyutlu sayısal dizi olmalı.')
                size=math.prod(shape)*dtype.itemsize
                if size!=info.file_size-source.tell():raise ValueError('Proje dizi boyutu tutarsız.')
                values=np.empty(shape,dtype=dtype);buffer=memoryview(values).cast('B')
                for start in range(0,size,8*1024*1024):
                    check();end=min(size,start+8*1024*1024);block=source.read(end-start)
                    if len(block)!=end-start:raise ValueError('Proje verisi eksik.')
                    buffer[start:end]=block;done+=len(block);report(min(.99,done/max(1,total)),'Proje verileri okunuyor')
                source.read(1);arrays[name]=values
        check();return manifest,arrays
