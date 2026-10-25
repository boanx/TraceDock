"""Import-safe numerical workers shared by the desktop process and frozen child processes."""
import os
for _name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ.setdefault(_name,'1')
import csv,io,re,math,ctypes,codecs
from datetime import datetime
import numpy as np

METADATA={'tracedock','id','unit','rangemax','rangemin','threefactorial','twofactorial','prefixgain','prefixoffset','offset','slope','zerovalue','samplerate','multiplier','commonrate'}
TIME_NAMES={'datetime','timestamp','time','elapsed','elapsedtime','elapsedseconds','testtime','zaman','sure','süre','seconds','second','sec','t','times','timems','timemsec','timemilliseconds','milliseconds','ms'}
DATE_PATTERN=re.compile(r'^(\d{1,4})[-/.](\d{1,2})[-/.](\d{1,4})[ T]+(\d{1,2}):(\d{1,2}):(\d{1,2})(?:[.,](\d+))?(.*)$')

def normalize(value):return re.sub(r'[^a-z0-9ıüşöçğ]','',value.strip().casefold())

def parse_time(raw):
    raw=raw.strip().replace(',','.')
    try:return float(raw),False
    except ValueError:pass
    try:return datetime.fromisoformat(raw).timestamp(),True
    except ValueError:pass
    match=DATE_PATTERN.match(raw)
    if match:
        a,b,c,h,m,s,frac,zone=match.groups();year,month,day=(int(a),int(b),int(c)) if len(a)==4 else (int(c),int(b),int(a))
        micro=int(((frac or '')+'000000')[:6]);stamp=datetime(year,month,day,int(h),int(m),int(s),micro)
        if zone:
            return datetime.fromisoformat(stamp.isoformat()+zone.strip()).timestamp(),True
        return stamp.timestamp(),True
    parts=raw.split(':')
    if len(parts)==3:return int(parts[0])*3600+int(parts[1])*60+float(parts[2]),False
    raise ValueError(f'Tarih/saat okunamadı: {raw[:80]}')

def number(raw):
    try:return float(raw.strip().replace('\u00a0','').replace(' ','').replace(',','.'))
    except ValueError:return float('nan')

def memory_available():
    if os.name=='nt':
        class Memory(ctypes.Structure):
            _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','total_page','available_page','total_virtual','available_virtual','extended')]
        info=Memory();info.length=ctypes.sizeof(info)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(info)):return int(info.total),int(info.available)
    try:
        page=os.sysconf('SC_PAGE_SIZE');return page*os.sysconf('SC_PHYS_PAGES'),page*os.sysconf('SC_AVPHYS_PAGES')
    except (AttributeError,ValueError,OSError):return 8*2**30,4*2**30

def resource_plan(size=0):
    total,available=memory_available();cpus=max(1,os.cpu_count() or 1)
    budget=int(available*.85);reserve=min(size*2,budget//2);workers=max(1,min(cpus,(budget-reserve)//(96*2**20)))
    chunk=max(256*1024,min(4*2**20,max(1,size)//max(1,workers*4)))
    return {'cpus':cpus,'workers':int(workers),'total_ram':total,'available_ram':available,'memory_budget':budget,'chunk_bytes':chunk}

def _encoding(path):
    with open(path,'rb') as f:sample=f.read(65536)
    if sample.startswith((b'\xff\xfe',b'\xfe\xff')):return 'utf-16'
    if sample.startswith(b'\xef\xbb\xbf'):return 'utf-8-sig'
    if sample and sample.count(b'\x00')>len(sample)//10:
        return 'utf-16-le' if sample[1:32:2].count(b'\x00')>sample[:32:2].count(b'\x00') else 'utf-16-be'
    try:codecs.getincrementaldecoder('utf-8')().decode(sample,final=False);return 'utf-8-sig'
    except UnicodeDecodeError:return 'cp1254'

def inspect_text(path,kind='csv'):
    with open(path,'rb') as f:signature=f.read(4)
    if signature in (b'TDSm',b'TDSh'):raise ValueError('Bu dosya NI TDMS biçiminde. “TDMS ekle” seçeneğini kullanın.')
    encoding=_encoding(path)
    with open(path,encoding=encoding,newline='') as f:sample=f.read(65536)
    if '\x00' in sample:raise ValueError('Dosya metin/CSV biçiminde değil. Exlab TDMBIN dosyaları için “Exlab dosyası ekle” seçeneğini kullanın.')
    candidates=[]
    for delimiter in (',',';','\t','|'):
        try:rows=list(csv.reader(io.StringIO(sample,newline=''),delimiter=delimiter))[:80]
        except csv.Error:continue
        timed=max((len(r) for r in rows if len(r)>1 and any(normalize(v) in TIME_NAMES for v in r)),default=0)
        widths=[len(r) for r in rows if len(r)>1];width=max(set(widths),key=widths.count) if widths else 1
        candidates.append((timed*1000+width+10*widths.count(width),delimiter,rows))
    _,delimiter,rows=max(candidates,key=lambda item:item[0]);header_index=None;header=None;has_header=True
    for i,row in enumerate(rows):
        if len(row)>1 and normalize(row[0]) not in METADATA and any(normalize(v) in TIME_NAMES for v in row):header_index=i;header=row;break
    if header_index is None:
        if kind=='strain':raise ValueError('Exlab metin tablosunun DateTime başlığı bulunamadı. CSV ekle ile genel bir tablo olarak da açabilirsiniz.')
        for i,row in enumerate(rows):
            if not row or not any(v.strip() for v in row):continue
            if len(row)==1 and (':' in row[0] or normalize(row[0]).startswith(('version','channelamount'))):continue
            header_index=i;numeric=sum(math.isfinite(number(v)) for v in row)
            has_header=numeric<len(row)/2
            header=row if has_header else [f'Kanal {j+1}' for j in range(len(row))];break
    if header is None:raise ValueError('CSV başlığı veya sayısal tablo bulunamadı.')
    header=[v.strip() or f'Kanal {i+1}' for i,v in enumerate(header)];seen={}
    for i,name in enumerate(header):seen[name]=seen.get(name,0)+1;header[i]=name if seen[name]==1 else f'{name} ({seen[name]})'
    time_index=next((i for i,v in enumerate(header) if normalize(v) in TIME_NAMES),None) if has_header else None
    export_times={normalize(value):i for i,value in enumerate(header)}
    paired_export='time' in export_times and 'times' in export_times
    if paired_export:time_index=export_times['times']
    value_indices=[i for i in range(len(header)) if i!=time_index and not (paired_export and i==export_times['time'])]
    if not value_indices:raise ValueError('Zaman sütunu dışında ölçüm kanalı bulunamadı.')
    # TextIO.tell at a complete logical record gives an encoding-safe offset.
    with open(path,encoding=encoding,newline='') as f:
        logical=0
        while True:
            start=f.tell();line=f.readline()
            if not line:raise ValueError('Veri başlığı bulunamadı.')
            quotes=line.count('"')%2
            while quotes:
                extra=f.readline()
                if not extra:break
                line+=extra;quotes^=extra.count('"')%2
            if logical==header_index:offset=f.tell() if has_header else start;break
            logical+=1
    scale=.001 if time_index is not None and normalize(header[time_index]) in {'timems','timemsec','timemilliseconds','milliseconds','ms'} else 1.0
    return {'encoding':encoding,'delimiter':delimiter,'header':header,'time_index':time_index,'value_indices':value_indices,'data_offset':offset,'time_scale':scale,'kind':kind}

def parse_records(text,layout):
    records=[];times=[];metadata={};dates=False;invalid_times=0;width=len(layout['header']);time_index=layout['time_index'];columns=layout['value_indices']
    for row in csv.reader(io.StringIO(text,newline=''),delimiter=layout['delimiter']):
        if not row or not any(v.strip() for v in row):continue
        first=row[0].strip();key=normalize(first) if first and first[0].isalpha() else ''
        if key in METADATA:metadata[key]=[row[i] if i<len(row) else '' for i in columns];continue
        if key.startswith(('version','channelamount')) or (key in TIME_NAMES and len(row)<2):continue
        if row==layout['header']:continue
        if len(row)<width:row+=['']*(width-len(row))
        data=[row[i] for i in columns]
        stamp=None
        if time_index is not None:
            try:stamp,date=parse_time(row[time_index]);dates|=date;stamp*=layout['time_scale']
            except (ValueError,OverflowError,OSError):pass
        if stamp is None and not any(math.isfinite(number(v)) or v.strip().casefold() in {'nan','na','null','inf','-inf','+inf'} for v in data):continue
        if time_index is not None:
            if stamp is None:invalid_times+=1;stamp=float('nan')
            times.append(stamp)
        records.append(data)
    if not records:return None,None,metadata,dates,invalid_times
    text=' '.join(v.strip().replace('\u00a0','').replace(' ','').replace(',','.') or 'nan' for row in records for v in row)
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',DeprecationWarning);values=np.fromstring(text,sep=' ',dtype=float)
        if len(values)!=len(records)*len(columns):raise ValueError()
    except (ValueError,DeprecationWarning):values=np.fromiter((number(v) for row in records for v in row),dtype=float,count=len(records)*len(columns))
    return np.asarray(times,dtype=float) if time_index is not None else None,values.reshape(len(records),len(columns)),metadata,dates,invalid_times

def parse_file_block(path,start,end,layout):
    with open(path,'rb') as f:f.seek(start);raw=f.read(end-start)
    return (*parse_records(raw.decode(layout['encoding']),layout),os.getpid())

def format_export_block(chunks,shared,decimal,elapsed,uniform=False):
    def fmt(v):
        if not np.isfinite(v):return ''
        value=format(float(v),'.17g' if uniform else '.10g');return value.replace('.',',') if decimal==',' else value
    def clock(v):
        if not elapsed:return fmt(v)
        sign='-' if v<0 else '';total,frac=divmod(int(round(abs(float(v))*10000)),10000);hours,rem=divmod(total,3600);minutes,seconds=divmod(rem,60)
        return f'{sign}{hours:02d}:{minutes:02d}:{seconds:02d}.{frac:04d}'
    length=max((len(x) for x,y in chunks),default=0);output=io.StringIO(newline='');writer=csv.writer(output,delimiter=';' if decimal==',' else ',')
    for row in range(length):
        if shared:
            stamp=chunks[0][0][row];time_values=[clock(stamp),fmt(stamp)] if uniform and elapsed else [clock(stamp)]
            writer.writerow(time_values+[fmt(y[row]) for x,y in chunks])
        else:writer.writerow([v for x,y in chunks for v in ([clock(x[row]),fmt(y[row])] if row<len(x) else ['',''])])
    return output.getvalue()
