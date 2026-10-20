import multiprocessing
if __name__=='__main__':multiprocessing.freeze_support()
import csv, json, math, os, sys, traceback, uuid, threading, queue, time, tempfile, warnings
from array import array
from collections import deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from tracedock_workers import resource_plan, inspect_text, parse_file_block, parse_records, format_export_block, number
from numpy.lib.mixins import NDArrayOperatorsMixin
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
from tracedock_theme import GlassButton, GlassMessages as messagebox, GlassInputs as simpledialog, apply_native_glass, rounded_rect
import numpy as np
from nptdms import TdmsFile
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter

Y_AXIS_LABELS={'L1':'Sol 1','L2':'Sol 2','R1':'Sağ 1','R2':'Sağ 2'}
Y_AXIS_COLORS={'L1':'#007f85','L2':'#3f7eb6','R1':'#7261c4','R2':'#c77a1a'}
APP_NAME='TraceDock'
__author__='Ahmet Yusuf Ozyurt'
CONFIG_PATH=Path(os.getenv('APPDATA',str(Path.home()))) / 'TraceDock' / 'config.json'
LEGACY_CONFIG_PATH=Path(os.getenv('APPDATA',str(Path.home()))) / 'StrainLab' / 'config.json'
PALETTE=['#007f85','#7261c4','#c77a1a','#c44b78','#3f7eb6','#65933b','#b36135','#8c59a7','#247c66','#b54852','#6876ae','#467e91','#a16f21','#7c5c9d','#617f39']

class Cancelled(Exception):pass

def check_cancel(cancel):
    if cancel is not None and cancel.is_set():raise Cancelled()

class NumericView(NDArrayOperatorsMixin):
    def __array_ufunc__(self,ufunc,method,*inputs,**kwargs):
        return getattr(ufunc,method)(*[np.asarray(v) if isinstance(v,NumericView) else v for v in inputs],**kwargs)
    @property
    def shape(self):return (len(self),)
    @property
    def size(self):return len(self)
    @property
    def dtype(self):return np.dtype('float64')
    def copy(self):return np.asarray(self).copy()

class SampleTimeAxis(NumericView):
    """A regular clock described by a few scalars, without an N-sample allocation."""
    __slots__=('count','rate','offset','stride','origin')
    def __init__(self,count,rate,offset=0,stride=1,origin=0.0):
        self.count=int(count);self.rate=float(rate);self.offset=offset;self.stride=stride;self.origin=origin
    def __len__(self):return self.count
    def __array__(self,dtype=None,copy=None):
        values=(self.offset+np.arange(self.count,dtype=float)*self.stride)/self.rate+self.origin
        return values.astype(dtype,copy=False) if dtype is not None else values
    def __getitem__(self,key):
        if isinstance(key,slice):
            start,stop,stride=key.indices(self.count)
            return SampleTimeAxis(len(range(start,stop,stride)),self.rate,self.offset+start*self.stride,self.stride*stride,self.origin)
        if np.isscalar(key):
            index=int(key)
            if index<0:index+=self.count
            if not 0<=index<self.count:raise IndexError(index)
            return (self.offset+index*self.stride)/self.rate+self.origin
        indices=np.asarray(key)
        if indices.dtype==bool:indices=np.flatnonzero(indices)
        return (self.offset+indices*self.stride)/self.rate+self.origin
    def searchsorted(self,value,side='left'):
        if not self.count:return 0
        if value<=self[0]:return 0 if side=='left' or value<self[0] else 1
        if value>=self[-1]:return self.count if side=='right' or value>self[-1] else self.count-1
        idx=max(0,min(self.count,int((value-self.origin)*self.rate-self.offset)//self.stride))
        if side=='left':
            while idx<self.count and self[idx]<value:idx+=1
            while idx>0 and self[idx-1]>=value:idx-=1
        else:
            while idx<self.count and self[idx]<=value:idx+=1
            while idx>0 and self[idx-1]>value:idx-=1
        return idx

class JoinedValues(NumericView):
    """A sequence of source views; export materializes only requested chunks."""
    def __init__(self,parts):
        self.parts=[p for p in parts if len(p)];self.ends=np.cumsum([len(p) for p in self.parts],dtype=np.int64)
    def __len__(self):return int(self.ends[-1]) if len(self.ends) else 0
    def __array__(self,dtype=None,copy=None):
        values=np.concatenate([np.asarray(p) for p in self.parts]) if self.parts else np.empty(0)
        return values.astype(dtype,copy=False) if dtype is not None else values
    def __getitem__(self,key):
        if isinstance(key,slice):
            start,stop,step=key.indices(len(self))
            if step!=1:return self[np.arange(start,stop,step)]
            parts=[];begin=0
            for part,end in zip(self.parts,self.ends):
                end=int(end)
                if end>start and begin<stop:parts.append(part[max(0,start-begin):min(len(part),stop-begin)])
                begin=end
                if begin>=stop:break
            return type(self)(parts)
        if np.isscalar(key):
            index=int(key)
            if index<0:index+=len(self)
            if not 0<=index<len(self):raise IndexError(index)
            part=int(np.searchsorted(self.ends,index,side='right'));begin=int(self.ends[part-1]) if part else 0
            return self.parts[part][index-begin]
        indices=np.asarray(key)
        if indices.dtype==bool:indices=np.flatnonzero(indices)
        indices=np.where(indices<0,indices+len(self),indices)
        if np.any((indices<0)|(indices>=len(self))):raise IndexError('sample index')
        result=np.empty(indices.shape,dtype=float);groups=np.searchsorted(self.ends,indices,side='right')
        for group in np.unique(groups):
            mask=groups==group;begin=int(self.ends[group-1]) if group else 0;result[mask]=self.parts[group][indices[mask]-begin]
        return result

class JoinedTimeAxis(JoinedValues):
    def searchsorted(self,value,side='left'):
        lo=0;hi=len(self)
        while lo<hi:
            mid=(lo+hi)//2
            if self[mid]<value or (side=='right' and self[mid]==value):lo=mid+1
            else:hi=mid
        return lo

class ScaledValues(NumericView):
    __slots__=('base','factor')
    def __init__(self,base,factor):self.base=base;self.factor=float(factor)
    def __len__(self):return len(self.base)
    def __array__(self,dtype=None,copy=None):
        values=self.base*self.factor
        return values.astype(dtype,copy=False) if dtype is not None else values
    def __getitem__(self,key):return self.base[key]*self.factor

class ReferenceXAxis(NumericView):
    """Evaluate a chosen X channel only at the points actually needed for display/export."""
    __slots__=('clock','reference_time','reference_values')
    def __init__(self,clock,reference_time,reference_values):self.clock=clock;self.reference_time=reference_time;self.reference_values=reference_values
    def __len__(self):return len(self.clock)
    def __getitem__(self,key):
        query=np.asarray(self.clock[key]);rt=self.reference_time;ry=self.reference_values
        if not len(rt):return np.full(query.shape,np.nan)
        if isinstance(rt,SampleTimeAxis):indices=np.floor(((query-rt.origin)*rt.rate-rt.offset)/rt.stride).astype(np.int64)+1
        else:indices=np.searchsorted(rt,query,side='right')
        left=np.clip(indices-1,0,len(rt)-1);right=np.clip(indices,0,len(rt)-1)
        lx=rt[left];rx=rt[right];ly=ry[left];uy=ry[right];width=rx-lx
        fraction=np.divide(query-lx,width,out=np.zeros(query.shape,dtype=float),where=width!=0)
        values=ly+(uy-ly)*fraction
        # Exact samples must not become NaN merely because the following sample is missing.
        values=np.where(query==lx,ly,values);values=np.where((query<rt[0])|(query>rt[-1]),np.nan,values)
        return float(values) if values.ndim==0 else values
    def __array__(self,dtype=None,copy=None):
        values=self[:]
        return values.astype(dtype,copy=False) if dtype is not None else values

def new_process_pool(plan):
    return ProcessPoolExecutor(max_workers=plan['workers'],mp_context=multiprocessing.get_context('spawn'))

def ordered_parallel(pool,requests,cancel,pending_limit):
    pending=deque();iterator=iter(requests)
    try:
        while True:
            while len(pending)<pending_limit:
                check_cancel(cancel)
                try:function,args=next(iterator)
                except StopIteration:break
                pending.append(pool.submit(function,*args))
            if not pending:return
            future=pending[0]
            while not future.done():check_cancel(cancel);time.sleep(.015)
            pending.popleft();yield future.result()
    finally:
        for future in pending:future.cancel()

def text_block_ranges(path,offset,chunk_bytes,cancel):
    with open(path,'rb') as f:
        f.seek(offset)
        while True:
            check_cancel(cancel);start=f.tell();part=f.read(chunk_bytes)
            if not part:return
            part+=f.readline();quotes=part.count(b'"')%2
            while quotes:
                extra=f.readline()
                if not extra:break
                quotes^=extra.count(b'"')%2
            yield start,f.tell()

def parse_text_file(path,progress=None,cancel=None,kind='csv',pool=None,plan=None):
    layout=inspect_text(path,kind);plan=plan or resource_plan(os.path.getsize(path));size=os.path.getsize(path)
    columns=[array('d') for i in layout['value_indices']];clock=array('d');metadata={};date=False;invalid_times=0;count=0;pids=set()
    def consume(result):
        nonlocal date,invalid_times,count
        times,values,meta,is_date,invalid,pid=result;metadata.update(meta);date|=is_date;invalid_times+=invalid;pids.add(pid)
        if values is None:return
        count+=len(values)
        if times is not None:clock.frombytes(times.tobytes())
        for i,column in enumerate(columns):column.frombytes(values[:,i].tobytes())
    if layout['encoding'].startswith('utf-16'):
        # Decode complete records before splitting UTF-16 so a byte-order/code-unit boundary is never cut.
        with open(path,encoding=layout['encoding'],newline='') as f:
            f.seek(layout['data_offset']);lines=[];length=0;quoted=False
            def requests():
                nonlocal lines,length,quoted
                for line in f:
                    check_cancel(cancel);lines.append(line);length+=len(line);quoted^=bool(line.count('"')%2)
                    if length>=plan['chunk_bytes'] and not quoted:
                        yield ''.join(lines);lines=[];length=0
                if lines:yield ''.join(lines)
            for text in requests():
                consume((*parse_records(text,layout),os.getpid()))
                if progress:progress(min(.98,count*max(1,len(columns))*8/max(1,size)),f'{count:,} satır okundu')
    else:
        ranges=text_block_ranges(path,layout['data_offset'],plan['chunk_bytes'],cancel)
        if pool is None:
            for start,end in ranges:
                consume(parse_file_block(path,start,end,layout))
                if progress:progress(end/max(1,size),f'{count:,} satır okundu')
        else:
            ends=deque()
            def requests():
                for start,end in ranges:ends.append(end);yield parse_file_block,(str(path),start,end,layout)
            for result in ordered_parallel(pool,requests(),cancel,plan['workers']*2):
                consume(result);end=ends.popleft()
                if progress:progress(end/max(1,size),f'{count:,} satır • {plan["workers"]} paralel çalışan')
    if not count:raise ValueError('Ölçüm satırı bulunamadı. Dosyanın zaman ve sütun ayıracı biçimini kontrol edin.')
    names=[layout['header'][i] for i in layout['value_indices']];parsed={name:np.frombuffer(column,dtype=float) for name,column in zip(names,columns)}
    if not any(np.any(np.isfinite(values)) for values in parsed.values()):raise ValueError('Ölçüm sütunlarında sayısal değer bulunamadı.')
    common=None
    for raw in metadata.get('commonrate',[]):
        value=number(raw)
        if math.isfinite(value) and value>0:common=value;break
    warning=''
    if not clock or invalid_times or not np.all(np.isfinite(clock)):
        x=SampleTimeAxis(count,common or 1);date=False
        if invalid_times:warning=f'{invalid_times} zaman damgası çözülemedi. Örnekler korundu; Hz veya süreyi düzenleyin.'
    else:x=np.frombuffer(clock,dtype=float)
    rate=common or ((count-1)/(x[-1]-x[0]) if count>1 and x[-1]>x[0] else 1.0)
    return {'name':Path(path).name,'path':str(path),'source_kind':kind,'xname':layout['header'][layout['time_index']] if layout['time_index'] is not None else 'time','x':x,'x_is_date':date,'channels':parsed,'units':dict(zip(names,metadata.get('unit',['']*len(names)))),'ids':dict(zip(names,metadata.get('id',names))),'grid_rate':rate,'_base_rate':rate,'multipliers':{name:1.0 for name in parsed},'_base_x':x,'_base_channels':dict(parsed),'timing_warning':warning,'reader_workers':len(pids),'reader_pids':sorted(pids)}

def parse_exlab(path,progress=None,cancel=None):return parse_text_file(path,progress,cancel,'csv')
def parse_strain(path,progress=None,cancel=None):return parse_text_file(path,progress,cancel,'strain')

def build_channel_cache(values,cancel=None):
    n=len(values);block_size=256;extrema=[];first=last=minimum=maximum=None
    for start in range(0,n,131072):
        check_cancel(cancel);part=values[start:min(n,start+131072)];finite=np.isfinite(part)
        if np.any(finite):
            a=float(part[np.argmax(finite)]);b=float(part[len(part)-1-np.argmax(finite[::-1])])
            if first is None:first=a
            last=b;low=float(np.min(part,where=finite,initial=np.inf));high=float(np.max(part,where=finite,initial=-np.inf))
            minimum=low if minimum is None else min(minimum,low);maximum=high if maximum is None else max(maximum,high)
        full=len(part)//block_size
        if full:
            matrix=part[:full*block_size].reshape(full,block_size);ok=finite[:full*block_size].reshape(full,block_size)
            offsets=start+np.arange(full,dtype=np.int64)*block_size
            extrema.append(np.column_stack((offsets+np.argmin(np.where(ok,matrix,np.inf),axis=1),offsets+np.argmax(np.where(ok,matrix,-np.inf),axis=1))))
        if len(part)%block_size:
            offset=full*block_size;tail=part[offset:];valid=finite[offset:]
            extrema.append(np.array([[start+offset+np.argmin(np.where(valid,tail,np.inf)),start+offset+np.argmax(np.where(valid,tail,-np.inf))]],dtype=np.int64))
    levels=[]
    if extrema:
        indices=np.concatenate(extrema);size=block_size;levels.append((size,indices))
        while len(indices)>1:
            check_cancel(cancel);flat=indices.ravel();padding=(-len(flat))%8
            if padding:flat=np.pad(flat,(0,padding),mode='edge')
            candidates=flat.reshape(-1,8);data=values[candidates];finite=np.isfinite(data);rows=np.arange(len(candidates))
            indices=np.column_stack((candidates[rows,np.argmin(np.where(finite,data,np.inf),axis=1)],candidates[rows,np.argmax(np.where(finite,data,-np.inf),axis=1)]))
            size*=4;levels.append((size,indices))
    return (first,last,minimum,maximum),levels

def prepare_dataset(d,progress=None,cancel=None):
    d.setdefault('uid',uuid.uuid4().hex)
    if '_base_channels' not in d:d['_base_channels']=dict(d['channels'])
    d.setdefault('_selected',set(list(d['channels'])[:6]));base_x=d.get('_base_x',d.get('x',[]))
    if not isinstance(base_x,SampleTimeAxis):base_x=np.asarray(base_x,dtype=float)
    rate=d.get('_base_rate') or d.get('grid_rate')
    if not rate and len(base_x)>1 and base_x[-1]>base_x[0]:rate=(len(base_x)-1)/(base_x[-1]-base_x[0])
    rate=float(rate) if rate and math.isfinite(float(rate)) and float(rate)>0 else 1.0
    if abs(rate-round(rate))<max(1,rate)*1e-8:rate=float(round(rate))
    regular=bool(len(base_x));origin=float(base_x[0]) if len(base_x) else 0
    tolerance=max(1e-9,abs(origin)*3e-16)
    for start in range(0,0 if isinstance(base_x,SampleTimeAxis) else len(base_x),65536):
        check_cancel(cancel);stop=min(len(base_x),start+65536)
        if not np.allclose(base_x[start:stop]-origin,np.arange(start,stop)/rate,rtol=1e-10,atol=tolerance):regular=False;break
    shared=None if regular else base_x-origin;clocks={};d['channel_rates']={};d['_channel_x']={};d['_base_stats']={};d['_envelopes']={}
    names=list(d['channels'])
    def cache(name):return build_channel_cache(d['_base_channels'][name],cancel)
    parallel=len(names)>1 and sum(v.nbytes for v in d['_base_channels'].values())>=2*2**20
    if parallel:
        plan=resource_plan(sum(v.nbytes for v in d['_base_channels'].values()));workers=min(plan['workers'],len(names))
        with ThreadPoolExecutor(max_workers=workers,thread_name_prefix='TraceDock-channel') as executor:
            futures={executor.submit(cache,name):name for name in names};completed=0
            for future in as_completed(futures):
                check_cancel(cancel);name=futures[future];d['_base_stats'][name],d['_envelopes'][name]=future.result();completed+=1
                if progress:progress(completed/max(1,len(names)),f'{completed}/{len(names)} kanal • {workers} paralel çalışan')
        d['cache_workers']=workers
    else:
        for i,name in enumerate(names):
            check_cancel(cancel);d['_base_stats'][name],d['_envelopes'][name]=cache(name)
            if progress:progress((i+1)/max(1,len(names)),f'{i+1}/{len(names)} kanal hazırlandı')
        d['cache_workers']=1
    for name in names:
        values=d['_base_channels'][name];values.flags.writeable=False;count=len(values);d['channel_rates'][name]=rate
        if count not in clocks:clocks[count]=SampleTimeAxis(count,rate) if regular or count!=len(base_x) else shared
        d['_channel_x'][name]=clocks[count]
        factor=float(d.get('multipliers',{}).get(name,1))*float(d.get('data_multiplier',1));d['channels'][name]=values if factor==1 else ScaledValues(values,factor)
    return d

def set_timing(d,names,field,value):
    value=float(value)
    if not math.isfinite(value) or value<=0:raise ValueError('Pozitif ve sonlu bir sayı girin.')
    if field not in ('rate','duration'):raise ValueError('Bilinmeyen zaman alanı.')
    planned={}
    for name in names:
        count=len(d['channels'][name])
        if not count:continue
        rate=value if field=='rate' else count/value
        if not math.isfinite(rate) or rate<=0 or not math.isfinite(count/rate):raise ValueError('Bu değerle geçerli süre veya frekans hesaplanamıyor.')
        planned[name]=(count,rate)
    clocks={}
    for name,(count,rate) in planned.items():
        d['channel_rates'][name]=rate
        if (count,rate) not in clocks:clocks[count,rate]=SampleTimeAxis(count,rate)
        d['_channel_x'][name]=clocks[count,rate]

def envelope_indices(values,start,stop,levels,budget=4000):
    if stop<=start:return np.empty(0,dtype=np.int64)
    if stop-start<=budget:return np.arange(start,stop,dtype=np.int64)
    size,indices=next(((size,indices) for size,indices in levels if math.ceil((stop-start)/size)*2<=budget),levels[-1])
    left=(start+size-1)//size;right=stop//size;parts=[np.array([start,stop-1],dtype=np.int64),indices[left:right].ravel()]
    for lo,hi in [(start,min(stop,left*size)),(max(start,right*size),stop)]:
        if hi<=lo:continue
        data=values[lo:hi];finite=np.isfinite(data)
        if np.any(finite):parts.append(np.array([lo+np.argmin(np.where(finite,data,np.inf)),lo+np.argmax(np.where(finite,data,-np.inf))]))
    return np.unique(np.concatenate(parts))

def visible_slice(axis,lo,hi):
    if hasattr(axis,'searchsorted'):return slice(max(0,axis.searchsorted(lo)-1),min(len(axis),axis.searchsorted(hi,'right')+1))
    return slice(max(0,int(np.searchsorted(axis,lo))-1),min(len(axis),int(np.searchsorted(axis,hi,'right'))+1))

def range_selection(axis,lo,hi,elapsed=True):
    if elapsed:
        if hasattr(axis,'searchsorted'):return slice(axis.searchsorted(lo),axis.searchsorted(hi,'right'))
        return slice(int(np.searchsorted(axis,lo)),int(np.searchsorted(axis,hi,'right')))
    values=np.asarray(axis);return np.flatnonzero(np.isfinite(values)&(values>=lo)&(values<=hi))

def selection_count(axis,selection):return len(range(*selection.indices(len(axis)))) if isinstance(selection,slice) else len(selection)
def selection_part(axis,selection,start,stop):
    return axis[slice(selection.start+start,min(selection.start+stop,selection.stop))] if isinstance(selection,slice) else axis[selection[start:stop]]

def number_text(value,decimal='.'):
    if not np.isfinite(value):return ''
    value=f'{value:.10g}';return value.replace('.',',') if decimal==',' else value

def write_series_csv(path,series,lo,hi,decimal='.',elapsed=True,progress=None,cancel=None,metadata=None):
    filtered=[(entry,range_selection(entry['x'],lo,hi,elapsed)) for entry in series];counts=[selection_count(entry['x'],sel) for entry,sel in filtered];count=max(counts,default=0)
    if not count:raise ValueError('Seçilen aralıkta örnek bulunamadı.')
    shared=all(n==counts[0] for n in counts)
    if shared:
        first,first_sel=filtered[0]
        for entry,sel in filtered[1:]:
            if entry['x'] is first['x'] and isinstance(sel,slice) and sel==first_sel:continue
            for start in range(0,count,8192):
                check_cancel(cancel)
                if not np.array_equal(selection_part(entry['x'],sel,start,start+8192),selection_part(first['x'],first_sel,start,start+8192)):shared=False;break
            if not shared:break
    temporary=None;pool=None;plan=resource_plan(count*len(series)*16)
    try:
        parallel_threshold=8_000_000 if getattr(sys,'frozen',False) else 1_000_000
        if count*len(series)>=parallel_threshold and plan['workers']>1:pool=new_process_pool(plan)
        with tempfile.NamedTemporaryFile('w',encoding='utf-8-sig',newline='',dir=str(Path(path).parent),prefix='.tracedock-',suffix='.tmp',delete=False) as output:
            temporary=output.name;writer=csv.writer(output,delimiter=';' if decimal==',' else ',')
            writer.writerow((['time' if elapsed else 'X']+[entry['label'] for entry,sel in filtered]) if shared else [text for entry,sel in filtered for text in (entry['label']+' / '+('time' if elapsed else 'X'),entry['label']+' / value')])
            if metadata:writer.writerows(metadata)
            def requests():
                for start in range(0,count,8192):
                    check_cancel(cancel);stop=min(count,start+8192)
                    chunks=[(np.asarray(selection_part(entry['x'],sel,start,stop)),np.asarray(selection_part(entry['y'],sel,start,stop))) for entry,sel in filtered]
                    yield format_export_block,(chunks,shared,decimal,elapsed)
            results=ordered_parallel(pool,requests(),cancel,plan['workers']*2) if pool else (fn(*args) for fn,args in requests())
            written=0
            for text in results:
                check_cancel(cancel);output.write(text);written=min(count,written+8192)
                if progress:progress(written/count,f"{written:,}/{count:,} satır • {plan['workers'] if pool else 1} paralel çalışan")
        check_cancel(cancel);os.replace(temporary,path);temporary=None
    finally:
        if pool:pool.shutdown(wait=True,cancel_futures=True)
        if temporary:
            try:os.unlink(temporary)
            except OSError:pass
    return count


def elapsed_text(seconds):
    sign='-' if seconds<0 else ''
    ticks=int(round(abs(float(seconds))*10000));total,frac=divmod(ticks,10000)
    hours,rem=divmod(total,3600);minutes,secs=divmod(rem,60)
    return f'{sign}{hours:02d}:{minutes:02d}:{secs:02d}.{frac:04d}'


class TraceDock(tk.Tk):
 def __init__(self):
    super().__init__(); self.title('TraceDock'); window_width=min(1500,max(1000,self.winfo_screenwidth()-60));window_height=min(920,max(620,self.winfo_screenheight()-100));self.geometry(f'{window_width}x{window_height}');self.minsize(min(1240,window_width),min(720,window_height)); self.configure(bg='#e8eff5')
    self.timeline_rows=[{'uid':uuid.uuid4().hex,'name':'Satır 1'}];self.timeline_row=self.timeline_rows[0]['uid'];self._timeline_row_number=1;self.timeline=[];self.timeline_selected=None;self._timeline_drag=None;self._timeline_scale=1.;self._timeline_fit=True;self.timeline_match=tk.StringVar(value='Kanal adına göre');self.datasets=[]; self.active=0; self.selected=set();self._tree_anchor=None; self.probes={};self.legend_visible=tk.BooleanVar(value=True);self._graph_button=None;self._channel_axes={};self._track_axes={};self._y_axes={};self._reset_axis_slots=set();self._legend_artist=None;self._legend_targets=[]; self.mouse_data=None; self.span=None; self.span_artist=None; self._span_generation=0; self.drag_mode=None; self.drag_start=None; self.click_start=None; self._guide_artists=[]; self.sort_state={}
    icon_path=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'tracedock.ico'
    if icon_path.exists():
      try:self.iconbitmap(str(icon_path))
      except Exception:pass
    self._style(); self._build(); self.load_default_config(); self.redraw_all()
 def _style(self):
    style=ttk.Style(self);style.theme_use('clam');style.configure('.',background='#f4f8fb',foreground='#203449',fieldbackground='#ffffff',bordercolor='#cbdbe7',lightcolor='#ffffff',darkcolor='#d9e4ed',font=('Segoe UI',9))
    style.configure('Treeview',background='#ffffff',foreground='#203449',fieldbackground='#ffffff',rowheight=28,bordercolor='#d9e4ed',relief='flat');style.configure('Treeview.Heading',background='#eaf2f8',foreground='#405d75',font=('Segoe UI',9,'bold'),padding=(8,7),relief='flat');style.map('Treeview',background=[('selected','#d7efee')],foreground=[('selected','#164e58')]);style.map('Treeview.Heading',background=[('active','#dceef2')])
    style.configure('TCombobox',fieldbackground='#ffffff',background='#eaf2f8',foreground='#203449',selectbackground='#d7efee',selectforeground='#203449',arrowcolor='#60758a',borderwidth=1,padding=5);style.map('TCombobox',fieldbackground=[('readonly','#ffffff')],foreground=[('readonly','#203449')],selectbackground=[('readonly','#ffffff')],selectforeground=[('readonly','#203449')])
    style.configure('TEntry',fieldbackground='#ffffff',foreground='#203449',insertcolor='#203449',padding=5,borderwidth=1);style.map('TEntry',bordercolor=[('focus','#55aeb1')])
    style.configure('TNotebook',background='#f4f8fb',bordercolor='#d9e4ed',tabmargins=(4,3,4,0));style.configure('TNotebook.Tab',background='#eaf2f8',foreground='#60758a',padding=(15,7));style.map('TNotebook.Tab',background=[('selected','#ffffff'),('active','#e1f1f3')],foreground=[('selected','#007f85')])
    for name in ('Vertical.TScrollbar','Horizontal.TScrollbar'):style.configure(name,background='#c3d6e3',troughcolor='#edf3f8',bordercolor='#edf3f8',arrowcolor='#60758a',arrowsize=12,relief='flat');style.map(name,background=[('active','#91b8ca')])
    style.configure('Horizontal.TProgressbar',background='#54adb4',troughcolor='#e4edf4',bordercolor='#e4edf4',lightcolor='#8fd1d0',darkcolor='#54adb4')
    for pattern,value in (('*TCombobox*Listbox.background','#ffffff'),('*TCombobox*Listbox.foreground','#203449'),('*TCombobox*Listbox.selectBackground','#d7efee'),('*TCombobox*Listbox.selectForeground','#203449'),('*Entry.background','#ffffff'),('*Entry.foreground','#203449'),('*Entry.insertBackground','#203449')):self.option_add(pattern,value)
    self.bind_all('<Map>',self._glass_window_mapped,add='+')
 def _glass_window_mapped(self,event):
    if event.widget is self or isinstance(event.widget,tk.Toplevel):self.after_idle(lambda window=event.widget:apply_native_glass(window) if window.winfo_exists() else None)
 def _build(self):
    top=tk.Frame(self,bg='#e8eff5',height=58); top.pack(fill='x',padx=18);self._add_brand_logo(top); tk.Label(top,text='TraceDock',font=('Segoe UI',18,'bold'),fg='#007f85',bg='#e8eff5').pack(side='left',pady=12); self.status=tk.StringVar(value='Çevrimdışı • veriler bilgisayarınızda kalır'); tk.Label(top,textvariable=self.status,fg='#60758a',bg='#e8eff5').pack(side='right')
    self.workarea=tk.PanedWindow(self,orient='vertical',bg='#d9e4ed',sashwidth=6,bd=0);self.workarea.pack(fill='both',expand=True,padx=14,pady=(0,14));body=tk.PanedWindow(self.workarea,orient='horizontal',bg='#d9e4ed',sashwidth=5,bd=0);self.workarea.add(body,minsize=380,stretch='always'); sidebar_host=tk.Frame(body,bg='#f4f8fb',width=520);right=tk.Frame(body,bg='#f4f8fb');body.add(sidebar_host,minsize=350);body.add(right,minsize=620);sidebar_host.configure(highlightthickness=1,highlightbackground='#ffffff');right.configure(highlightthickness=1,highlightbackground='#ffffff');left=self._build_scrollable_sidebar(sidebar_host)
    self._panel_title(left,'VERİ DOSYALARI');self._button(left,'Strain Gauge dosyası ekle',self.add_strain).pack(fill='x',padx=10,pady=(0,5)); bar=tk.Frame(left,bg='#f4f8fb'); bar.pack(fill='x',padx=10); self._button(bar,'CSV ekle',self.add_csv).pack(side='left',fill='x',expand=True); self._button(bar,'TDMS ekle',self.add_tdms).pack(side='left',fill='x',expand=True,padx=(5,0)); self._button(bar,'Kaldır',self.remove_file).pack(side='left',padx=(6,0)); self.filelist=tk.Listbox(left,exportselection=False,bg='#ffffff',fg='#203449',selectbackground='#d7efee',selectforeground='#203449',relief='flat',height=5,highlightthickness=0); self.filelist.pack(fill='x',padx=10,pady=8); self.filelist.bind('<<ListboxSelect>>',self.switch_file);self.filelist.bind('<Double-Button-1>',self.rename_dataset);self.filelist.bind('<Button-3>',self.edit_dataset_multiplier)
    row=tk.Frame(left,bg='#f4f8fb');row.pack(fill='x',padx=10,pady=(3,6));self._button(row,'Ayarları kaydet',self.save_config).pack(side='left',fill='x',expand=True);self._button(row,'Ayarları yükle',self.load_config_dialog).pack(side='left',fill='x',expand=True,padx=(6,0))
    self._panel_title(left,'KANALLAR • DOSYAYA GÖRE'); self.filter=tk.StringVar(); ent=ttk.Entry(left,textvariable=self.filter); ent.pack(fill='x',padx=10,pady=(0,5)); ent.insert(0,''); ent.bind('<KeyRelease>',lambda e:self.render_channels());selectionbar=tk.Frame(left,bg='#f4f8fb');selectionbar.pack(fill='x',padx=10,pady=(0,5));self._button(selectionbar,'Seçilenleri işaretle',lambda:self._set_channel_checks(True)).pack(side='left',fill='x',expand=True);self._button(selectionbar,'İşaretleri kaldır',lambda:self._set_channel_checks(False)).pack(side='left',fill='x',expand=True,padx=(6,0)); self.chlist=tk.Frame(left,bg='#f4f8fb'); self.chlist.pack(fill='both',expand=True,padx=8,pady=(0,8));tk.Label(left,text='Shift+tık: kanal aralığı • Ctrl+tık: çoklu seçim\nBoşluk / kutucuk: toplu aç-kapat • Çift tık: ad / Hz / süre / çarpan',fg='#60758a',bg='#f4f8fb',justify='left',anchor='w').pack(fill='x',padx=10,pady=(0,8))
    toolbar=tk.Frame(right,bg='#f4f8fb');toolbar.pack(fill='x',padx=12,pady=(8,4));bar=tk.Frame(toolbar,bg='#f4f8fb');bar.pack(fill='x');tk.Label(bar,text='X ekseni',fg='#526c82',bg='#f4f8fb').pack(side='left');self.xcombo=ttk.Combobox(bar,state='readonly',width=16,values=[]);self.xcombo.pack(side='left',padx=(5,8));self.xcombo.bind('<<ComboboxSelected>>',lambda e:self.redraw());tk.Label(bar,text='Eğri',fg='#526c82',bg='#f4f8fb').pack(side='left');self.limit=ttk.Combobox(bar,state='readonly',width=6,values=['12','30','100','Tümü']);self.limit.set('Tümü');self.limit.pack(side='left',padx=4);self.limit.bind('<<ComboboxSelected>>',lambda e:self.redraw());tk.Label(bar,text='Ondalık',fg='#526c82',bg='#f4f8fb').pack(side='left',padx=(5,2));self.decimal=ttk.Combobox(bar,state='readonly',width=3,values=('.',','));self.decimal.set('.');self.decimal.pack(side='left');self.decimal.bind('<<ComboboxSelected>>',lambda e:(self.redraw(preserve_view=True) if self.datasets else None));self._button(bar,'Tümünü göster',self.reset_zoom).pack(side='left',padx=(9,2));self._button(bar,'Seçili aralığı temizle',self.clear_span).pack(side='left',padx=2);self._button(bar,'Probe temizle',self.clear_probes).pack(side='left',padx=2)
    bar2=tk.Frame(toolbar,bg='#f4f8fb');bar2.pack(fill='x',pady=(4,0));self._button(bar2,'Grafik CSV',self.export_graph_csv).pack(side='left',padx=(0,4));self._button(bar2,"Seçili aralığı CSV'ye aktar",self.export_span_csv).pack(side='left',padx=4);self._button(bar2,'İstatistik CSV',self.export_stats_csv).pack(side='left',padx=4);self._button(bar2,'Grafik PNG',self.export_graph_png).pack(side='left',padx=4);self.coords=tk.StringVar(value='X = —    Y = —');bar3=tk.Frame(toolbar,bg='#f4f8fb');bar3.pack(fill='x',pady=(3,0));self._button(bar3,'Y eksenleri',self._show_y_axes).pack(side='right',padx=(6,0));ttk.Checkbutton(bar3,text='Lejantı göster',variable=self.legend_visible,command=self._toggle_legend).pack(side='right',padx=(8,0));tk.Label(bar3,text='Sol tık: prob ekle/sil • Sağ tık: prob etiketi • Sol sürükle: aralık • Sağ sürükle: kaydır • Tekerlek / orta tuş: zoom',fg='#60758a',bg='#f4f8fb').pack(side='left',padx=2)
    self.graph_panels=tk.PanedWindow(right,orient='vertical',bg='#d9e4ed',sashwidth=6,bd=0);self.graph_panels.pack(fill='both',expand=True,padx=10,pady=(0,8));plotbox=tk.Frame(self.graph_panels,bg='#f4f8fb');self.graph_panels.add(plotbox,minsize=120,stretch='always');readout=tk.Label(plotbox,textvariable=self.coords,fg='#405d75',bg='#f4f8fb',font=('Segoe UI',8),anchor='w',justify='left',padx=6,pady=2);readout.pack(side='bottom',fill='x');readout.bind('<Configure>',lambda e:readout.configure(wraplength=max(150,e.width-12))); self.fig=Figure(figsize=(9,5),dpi=100,facecolor='#f4f8fb');self.ax=self.fig.add_subplot(111);self.ax.set_facecolor('#ffffff');self.fig.subplots_adjust(left=.09,right=.985,top=.97,bottom=.12);self.canvas=FigureCanvasTkAgg(self.fig,master=plotbox);self.canvas.get_tk_widget().pack(fill='both',expand=True);self.canvas.mpl_connect('motion_notify_event',self.on_motion);self.canvas.mpl_connect('button_press_event',self.on_press);self.canvas.mpl_connect('button_release_event',self.on_release);self.canvas.mpl_connect('scroll_event',self.on_scroll);self.canvas.mpl_connect('resize_event',self._on_graph_resize)
    measurements=tk.Frame(self.graph_panels,bg='#f4f8fb',height=170);measurements.pack_propagate(False);self.graph_panels.add(measurements,minsize=145,height=170,stretch='never');self.tables=ttk.Notebook(measurements);self.tables.pack(fill='both',expand=True,padx=4,pady=4);stats_tab=tk.Frame(self.tables,bg='#f4f8fb');probe_tab=tk.Frame(self.tables,bg='#f4f8fb');self.tables.add(stats_tab,text='Kanal istatistikleri');self.tables.add(probe_tab,text='Problar');cols=('channel','start','end','min','max');self.table=ttk.Treeview(stats_tab,columns=cols,show='headings',height=4);labels=['Kanal','Başlangıç','Bitiş','Minimum','Maksimum'];widths=[280,150,150,150,150]
    for c,l,w in zip(cols,labels,widths):self.table.heading(c,text=l,command=lambda col=c:self.sort_tree(self.table,col));self.table.column(c,width=w,anchor='w' if c=='channel' else 'e')
    self._pack_measurement_table(self.table,stats_tab);pcols=('channel','probe','x','y');self.probe_table=ttk.Treeview(probe_tab,columns=pcols,show='headings',height=4)
    for c,l,w in zip(pcols,['Kanal','Probe','X','Değer Y'],[280,100,260,200]):self.probe_table.heading(c,text=l,command=lambda col=c:self.sort_tree(self.probe_table,col));self.probe_table.column(c,width=w,anchor='w' if c in ('channel','probe') else 'e')
    self._pack_measurement_table(self.probe_table,probe_tab)
    self._build_timeline();self._body=self.workarea;self._job=None;self._closing=False;self._lod_after=None;self._background=None;self._motion_clock=0;self._pending_tdms=[]
    self._job_bar=tk.Frame(self,bg='#f4f8fb');self._job_progress=ttk.Progressbar(self._job_bar,maximum=100);self._job_progress.pack(side='left',fill='x',expand=True,padx=8,pady=4)
    self._job_cancel=self._button(self._job_bar,'İptal',self._cancel_job);self._job_cancel.pack(side='right',padx=8)
    self.canvas.mpl_connect('draw_event',self._on_canvas_draw);self.protocol('WM_DELETE_WINDOW',self._close_app);self._sidebar_bind_widgets(self.sidebar_content)
 def _add_brand_logo(self,parent):
    path=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'tracedock.png'
    if not path.exists():return
    image=tk.PhotoImage(file=str(path));self._brand_logo=image.subsample(max(1,round(image.width()/40)),max(1,round(image.height()/40)));tk.Label(parent,image=self._brand_logo,bg='#e8eff5').pack(side='left',padx=(0,10),pady=6)
 def _build_scrollable_sidebar(self,parent):
    parent.rowconfigure(0,weight=1);parent.columnconfigure(0,weight=1)
    self.sidebar_canvas=tk.Canvas(parent,bg='#f4f8fb',highlightthickness=0,bd=0,width=500,yscrollincrement=24,xscrollincrement=24);self.sidebar_canvas.grid(row=0,column=0,sticky='nsew')
    self.sidebar_vertical=ttk.Scrollbar(parent,orient='vertical',command=self.sidebar_canvas.yview);self.sidebar_horizontal=ttk.Scrollbar(parent,orient='horizontal',command=self.sidebar_canvas.xview)
    self.sidebar_vertical.grid(row=0,column=1,sticky='ns');self.sidebar_horizontal.grid(row=1,column=0,sticky='ew');self.sidebar_canvas.configure(yscrollcommand=self.sidebar_vertical.set,xscrollcommand=self.sidebar_horizontal.set)
    self.sidebar_content=tk.Frame(self.sidebar_canvas,bg='#f4f8fb');self._sidebar_window=self.sidebar_canvas.create_window((0,0),window=self.sidebar_content,anchor='nw')
    self._sidebar_pending=None;self._sidebar_wheel_fraction={'x':0.,'y':0.};self._sidebar_bindtag='TraceDockSidebar'+str(id(self))
    self.bind_class(self._sidebar_bindtag,'<MouseWheel>',self._sidebar_wheel);self.bind_class(self._sidebar_bindtag,'<FocusIn>',self._sidebar_focus)
    self.sidebar_content.bind('<Configure>',self._schedule_sidebar_layout);self.sidebar_canvas.bind('<Configure>',self._schedule_sidebar_layout)
    self._sidebar_bind_widgets(parent);return self.sidebar_content
 def _sidebar_bind_widgets(self,widget):
    tags=widget.bindtags()
    if self._sidebar_bindtag not in tags:widget.bindtags((self._sidebar_bindtag,)+tags)
    for child in widget.winfo_children():self._sidebar_bind_widgets(child)
 def _schedule_sidebar_layout(self,event=None):
    if self._sidebar_pending is None:self._sidebar_pending=self.after_idle(self._layout_sidebar)
 def _layout_sidebar(self):
    self._sidebar_pending=None;c=self.sidebar_canvas;content=self.sidebar_content;width=max(1,c.winfo_width());height=max(1,c.winfo_height());required_width=max(460,content.winfo_reqwidth());required_height=content.winfo_reqheight();new_width=max(width,required_width);new_height=max(height,required_height)
    c.itemconfigure(self._sidebar_window,width=new_width,height=new_height);c.configure(scrollregion=(0,0,new_width,new_height))
    # Keep each scrollbar only when its direction actually overflows.
    for scrollbar,needed in ((self.sidebar_vertical,required_height>height+1),(self.sidebar_horizontal,required_width>width+1)):
      shown=bool(scrollbar.winfo_manager())
      if needed and not shown:scrollbar.grid()
      elif shown and not needed:scrollbar.grid_remove()
    if required_height<=height+1:c.yview_moveto(0)
    if required_width<=width+1:c.xview_moveto(0)
 def _sidebar_wheel(self,event):
    if not event.delta:return
    axis='x' if event.state&1 else 'y';c=self.sidebar_canvas;direction=-1 if event.delta>0 else 1
    # Lists keep their own scrolling; at an edge, continue with the whole panel.
    if axis=='y' and event.widget.winfo_class() in ('Treeview','Listbox'):
      view=event.widget.yview()
      if view and ((direction<0 and view[0]>0) or (direction>0 and view[1]<1)):return
    view=c.xview() if axis=='x' else c.yview()
    if not view or view[1]-view[0]>=.999999:return
    self._sidebar_wheel_fraction[axis]+=-event.delta/120*3;units=math.trunc(self._sidebar_wheel_fraction[axis]);self._sidebar_wheel_fraction[axis]-=units
    if units:
      if axis=='x':c.xview_scroll(units,'units')
      else:c.yview_scroll(units,'units')
    return 'break'
 def _sidebar_focus(self,event):
    if isinstance(event.widget,GlassButton) or event.widget.winfo_class() in ('Entry','TEntry','TCombobox','Button','Treeview','Listbox'):self.after_idle(lambda widget=event.widget:self._sidebar_reveal(widget))
 def _sidebar_reveal(self,widget):
    if not widget.winfo_exists():return
    c=self.sidebar_canvas;content=self.sidebar_content
    for axis,start,length,viewport,view,total in (
      ('y',widget.winfo_rooty()-content.winfo_rooty(),widget.winfo_height(),c.winfo_height(),c.canvasy(0),content.winfo_height()),
      ('x',widget.winfo_rootx()-content.winfo_rootx(),widget.winfo_width(),c.winfo_width(),c.canvasx(0),content.winfo_width())):
      target=None
      if start<view:target=start
      elif start+length>view+viewport:target=min(start,start+length-viewport)
      if target is not None and total>viewport:
        if axis=='y':c.yview_moveto(max(0,target)/total)
        else:c.xview_moveto(max(0,target)/total)
 def _pack_measurement_table(self,tree,parent):
    parent.rowconfigure(0,weight=1);parent.columnconfigure(0,weight=1);tree.grid(row=0,column=0,sticky='nsew',padx=(4,0),pady=(4,0));vertical=ttk.Scrollbar(parent,orient='vertical',command=tree.yview);vertical.grid(row=0,column=1,sticky='ns',pady=(4,0));horizontal=ttk.Scrollbar(parent,orient='horizontal',command=tree.xview);horizontal.grid(row=1,column=0,sticky='ew',padx=(4,0));tree.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set)
 def _toggle_timeline_panel(self):
    self._timeline_collapsed=not self._timeline_collapsed
    if self._timeline_collapsed:
      self.timeline_content.pack_forget();self.workarea.paneconfigure(self.timeline_dock,minsize=36,height=36);self.timeline_dock.configure(height=36);self.timeline_fold_button.configure(text='Genişlet ▾')
    else:
      self.timeline_content.pack(fill='both',expand=True);self.workarea.paneconfigure(self.timeline_dock,minsize=190,height=230);self.timeline_dock.configure(height=230);self.timeline_fold_button.configure(text='Küçült ▴')
 def _build_timeline(self):
    dock=tk.Frame(self.workarea,bg='#f4f8fb',height=230);dock.configure(highlightthickness=1,highlightbackground='#ffffff');dock.pack_propagate(False);self.workarea.add(dock,minsize=190,height=230,stretch='never');self.timeline_dock=dock;self._timeline_collapsed=False
    row=tk.Frame(dock,bg='#f4f8fb');row.pack(fill='x',padx=10,pady=(6,2))
    tk.Label(row,text='ZAMAN ÇİZELGESİ',fg='#007f85',bg='#f4f8fb',font=('Segoe UI',9,'bold')).pack(side='left',padx=(0,12))
    self.timeline_fold_button=self._button(row,'Küçült ▴',self._toggle_timeline_panel);self.timeline_fold_button.configure(pady=2);self.timeline_fold_button.pack(side='right',padx=(8,0))
    self.timeline_total=tk.StringVar(value='Toplam: 00:00:00.0000')
    tk.Label(row,textvariable=self.timeline_total,fg='#203449',bg='#f4f8fb').pack(side='right')
    tk.Label(row,text='Kanal eşleştirme',fg='#60758a',bg='#f4f8fb').pack(side='left',padx=(12,5))
    combo=ttk.Combobox(row,textvariable=self.timeline_match,state='readonly',width=22,values=['Kanal adına göre','Sütun sırasına göre','Ayrı çizgiler']);combo.pack(side='left');combo.bind('<<ComboboxSelected>>',lambda e:self._timeline_changed())
    self.timeline_content=tk.Frame(dock,bg='#f4f8fb');self.timeline_content.pack(fill='both',expand=True)
    row=tk.Frame(self.timeline_content,bg='#f4f8fb');row.pack(fill='x',padx=10,pady=(0,3))
    tk.Label(row,text='Aktif satır',fg='#60758a',bg='#f4f8fb').pack(side='left',padx=(0,6))
    self.timeline_row_combo=ttk.Combobox(row,state='readonly',width=16);self.timeline_row_combo.pack(side='left',padx=(0,5));self.timeline_row_combo.bind('<<ComboboxSelected>>',self._timeline_select_row)
    self._button(row,'Yeni satır',self.timeline_new_row).pack(side='left',padx=(0,4));self._button(row,'Satırı kaldır',self.timeline_remove_row).pack(side='left',padx=(0,8))
    tk.Label(row,text='Aynı satır: uç uca • Farklı satırlar: üst üste • Sürükle: sırala / satır değiştir',fg='#60758a',bg='#f4f8fb').pack(side='left')
    row=tk.Frame(self.timeline_content,bg='#f4f8fb');row.pack(fill='x',padx=10,pady=(0,3))
    for label,command in [('Seçili kanalları ekle',self.timeline_add),('Tümünü sırala',self.timeline_all),('←',lambda:self.timeline_move(-1)),('→',lambda:self.timeline_move(1)),('Paketi kaldır',self.timeline_remove),('Temizle',self.timeline_clear)]:self._button(row,label,command).pack(side='left',padx=(0,4))
    for label,command in [('Sığdır',self.timeline_fit),('−',lambda:self.timeline_zoom(1/1.5)),('+',lambda:self.timeline_zoom(1.5))]:self._button(row,label,command).pack(side='right',padx=2)
    area=tk.Frame(self.timeline_content,bg='#ffffff');area.pack(fill='both',expand=True,padx=10)
    self.timeline_canvas=tk.Canvas(area,bg='#ffffff',height=145,highlightthickness=0);self.timeline_canvas.pack(side='left',fill='both',expand=True)
    vsb=ttk.Scrollbar(area,orient='vertical',command=self._timeline_vscroll);vsb.pack(side='right',fill='y');self.timeline_canvas.configure(yscrollcommand=vsb.set)
    sb=ttk.Scrollbar(self.timeline_content,orient='horizontal',command=self._timeline_scroll);sb.pack(side='bottom',before=area,fill='x',padx=10,pady=(0,4));self.timeline_canvas.configure(xscrollcommand=sb.set)
    c=self.timeline_canvas;c.bind('<Configure>',lambda e:self._render_timeline());c.bind('<Button-1>',self._timeline_press);c.bind('<B1-Motion>',self._timeline_motion);c.bind('<ButtonRelease-1>',self._timeline_release);c.bind('<Double-Button-1>',self._timeline_focus);c.bind('<MouseWheel>',self._timeline_wheel)
 def _timeline_row_info(self,uid):return next((row for row in self.timeline_rows if row['uid']==uid),self.timeline_rows[0])
 def _timeline_sync_rows(self):
    valid={r['uid'] for r in self.timeline_rows}
    if self.timeline_row not in valid:self.timeline_row=self.timeline_rows[0]['uid']
    self.timeline_row_combo['values']=[r['name'] for r in self.timeline_rows];self.timeline_row_combo.current(next(i for i,r in enumerate(self.timeline_rows) if r['uid']==self.timeline_row))
 def _timeline_select_row(self,event=None):
    index=self.timeline_row_combo.current()
    if index<0:return
    self.timeline_row=self.timeline_rows[index]['uid'];self.timeline_selected=None;self._render_timeline();self._timeline_reveal_row()
 def _new_timeline_row(self):
    self._timeline_row_number+=1;row={'uid':uuid.uuid4().hex,'name':f'Satır {self._timeline_row_number}'};self.timeline_rows.append(row);self.timeline_row=row['uid'];self.timeline_selected=None;return row
 def timeline_new_row(self):
    row=self._new_timeline_row();self._timeline_changed();self._timeline_reveal_row();self.status.set(row['name']+' eklendi • Dosya/Kanal sütununa sağ tıklayarak veri ekleyin')
 def timeline_remove_row(self):
    uid=self.timeline_row;contexts={'clip:'+c['uid'] for c in self.timeline if c.get('row_uid',self.timeline_rows[0]['uid'])==uid};self.timeline=[c for c in self.timeline if c.get('row_uid',self.timeline_rows[0]['uid'])!=uid];self.probes={k:v for k,v in self.probes.items() if k[0] not in contexts}
    self.timeline_rows=[r for r in self.timeline_rows if r['uid']!=uid]
    if not self.timeline_rows:
      self._timeline_row_number+=1;self.timeline_rows=[{'uid':uuid.uuid4().hex,'name':f'Satır {self._timeline_row_number}'}]
    self.timeline_row=self.timeline_rows[0]['uid'];self.timeline_selected=None;self._timeline_changed()
 def _timeline_reveal_row(self):
    c=self.timeline_canvas;index=next(i for i,r in enumerate(self.timeline_rows) if r['uid']==self.timeline_row);top=28+index*76;bottom=top+76;height=max(75,c.winfo_height());total=max(height,28+76*len(self.timeline_rows));view=c.canvasy(0)
    if top<view+28:c.yview_moveto(max(0,top-28)/total)
    elif bottom>view+height:c.yview_moveto(max(0,bottom-height)/total)
    self._render_timeline()
 def _timeline_layout(self):
    sources={d['uid']:d for d in self.datasets};result=[]
    # Each row starts at zero and has its own cumulative clock.
    for row in self.timeline_rows:
      start=0.
      for clip in self.timeline:
        if clip.get('row_uid',self.timeline_rows[0]['uid'])!=row['uid']:continue
        d=sources.get(clip['dataset_uid'])
        if d is None:continue
        # Timeline timing follows the editable N/Hz duration, not source timestamps
        # that may contain pauses, jitter or a clock restart within an acquisition.
        duration=max((len(d['channels'][n])/d['channel_rates'][n] for n in self._clip_channels(clip,d)),default=0.)
        result.append((clip,d,start,start+duration));start+=duration
    return result
 def _timeline_duration(self):return max((end for clip,d,start,end in self._timeline_layout()),default=0.)
 def _timeline_active(self):return bool(self.timeline)
 def _clip_channels(self,clip,d):return [name for name in clip.get('channels',d['channels']) if name in d['channels']]
 def _timeline_changed(self):
    live_rows={row['uid'] for row in self.timeline_rows};self._track_axes={key:slot for key,slot in self._track_axes.items() if key[0] in live_rows}
    self.span=None;self.mouse_data=None;self._span_generation+=1;self.redraw_all()
 def timeline_add(self):
    if not self.datasets:self.status.set('Önce bir veri dosyası ekleyin');return
    d=self.datasets[self.active];self._timeline_add_source(d['uid'],tuple(n for n in d['channels'] if n in d['_selected']),self.timeline_row)
 def _timeline_add_source(self,dataset_uid,names,row_uid=None,new_row=False):
    d=next((d for d in self.datasets if d['uid']==dataset_uid),None)
    if d is None:return
    names=[n for n in names if n in d['channels']]
    if not names:self.status.set('Eklemek için en az bir kanal seçin');return
    if new_row:row_uid=self._new_timeline_row()['uid']
    row=next((row for row in self.timeline_rows if row['uid']==(row_uid or self.timeline_row)),None)
    if row is None:return
    clip={'uid':uuid.uuid4().hex,'dataset_uid':dataset_uid,'row_uid':row['uid'],'channels':list(dict.fromkeys(names))};self.timeline.append(clip);self.timeline_selected=clip['uid'];self.timeline_row=row['uid']
    if self._timeline_collapsed:self._toggle_timeline_panel()
    self._timeline_changed();self.after_idle(self._timeline_reveal_row);self.status.set(f"{d['name']} • {len(clip['channels'])} kanal → {row['name']}")
 def timeline_all(self):
    if not self.datasets:return
    clips=[{'uid':uuid.uuid4().hex,'dataset_uid':d['uid'],'row_uid':self.timeline_row,'channels':[n for n in d['channels'] if n in d['_selected']]} for d in self.datasets if d['_selected']]
    if not clips:self.status.set('Eklemek için en az bir kanal işaretleyin');return
    row=self.timeline_row;removed={'clip:'+c['uid'] for c in self.timeline if c.get('row_uid',self.timeline_rows[0]['uid'])==row};self.timeline=[c for c in self.timeline if c.get('row_uid',self.timeline_rows[0]['uid'])!=row]
    self.timeline.extend(clips);self.timeline_selected=clips[0]['uid'];self.probes={k:v for k,v in self.probes.items() if k[0] not in removed};self._timeline_fit=True;self._timeline_changed();self._timeline_reveal_row()
 def timeline_move(self,delta):
    positions=[i for i,c in enumerate(self.timeline) if c.get('row_uid',self.timeline_rows[0]['uid'])==self.timeline_row];index=next((i for i,p in enumerate(positions) if self.timeline[p]['uid']==self.timeline_selected),None)
    if index is None or not 0<=index+delta<len(positions):return
    a,b=positions[index],positions[index+delta];self.timeline[a],self.timeline[b]=self.timeline[b],self.timeline[a];self._timeline_changed()
 def timeline_remove(self):
    uid=self.timeline_selected
    if uid is None:return
    self.timeline=[c for c in self.timeline if c['uid']!=uid];self.probes={k:v for k,v in self.probes.items() if k[0]!='clip:'+uid};self.timeline_selected=None;self._timeline_changed()
 def timeline_clear(self):
    self.timeline=[];self.timeline_selected=None;self.probes={k:v for k,v in self.probes.items() if not k[0].startswith('clip:')};self._timeline_changed()
 def timeline_fit(self):self._timeline_fit=True;self.timeline_canvas.xview_moveto(0);self._render_timeline()
 def _timeline_scroll(self,*args):self.timeline_canvas.xview(*args);self._render_timeline()
 def _timeline_vscroll(self,*args):self.timeline_canvas.yview(*args);self._render_timeline()
 def timeline_zoom(self,factor):
    self._timeline_fit=False;self._timeline_scale=max(1e-9,min(1e8,self._timeline_scale*factor));self._render_timeline()
 def _render_timeline(self):
    self._timeline_sync_rows();c=self.timeline_canvas;c.delete('all');layout=self._timeline_layout();total=max((e for cl,d,s,e in layout),default=0.);width=max(160,c.winfo_width());height=max(75,c.winfo_height());margin=120;row_height=76
    self.timeline_total.set(f'{len(self.timeline_rows)} satır • {len(layout)} paket • Toplam: {elapsed_text(total)}')
    if self._timeline_fit:self._timeline_scale=(width-margin-15)/max(total,1e-9)
    scale=self._timeline_scale;extent=max(width,total*scale+margin+15);content_height=max(height,28+row_height*len(self.timeline_rows));c.configure(scrollregion=(0,0,extent,content_height));self._timeline_rects=[]
    left=c.canvasx(0);right=c.canvasx(width);top=c.canvasy(0);bottom=c.canvasy(height);row_indices={r['uid']:i for i,r in enumerate(self.timeline_rows)}
    for row in self.timeline_rows:
      y=28+row_indices[row['uid']]*row_height
      if y+row_height<top or y>bottom:continue
      c.create_rectangle(left,y,right,y+row_height,fill='#e8f4f5' if row['uid']==self.timeline_row else '#ffffff',outline='#d9e4ed')
      if not any(cl.get('row_uid',self.timeline_rows[0]['uid'])==row['uid'] for cl in self.timeline):c.create_text(max(margin+12,left+margin+12),y+35,text='Boş satır • Sağ tıkla veri ekleyin veya bir paketi buraya sürükleyin',fill='#708798',anchor='w',font=('Segoe UI',9))
    for i,(clip,d,start,end) in enumerate(layout):
      row_uid=clip.get('row_uid',self.timeline_rows[0]['uid']);y=28+row_indices[row_uid]*row_height;x1=margin+start*scale;x2=margin+end*scale;y1=y+5;y2=y+row_height-5;self._timeline_rects.append((clip['uid'],row_uid,x1,x2,y1,y2))
      if x2<left+margin or x1>right or y2<top+28 or y1>bottom:continue
      color=PALETTE[row_indices[row_uid]%len(PALETTE)];selected=clip['uid']==self.timeline_selected
      rounded_rect(c,x1,y1,x2,y2,r=11,fill='#d7efee' if selected else '#eaf2f8',outline='#007f85' if selected else '#cbdbe7',width=2 if selected else 1)
      if x2-x1>30:
        chars=max(1,int((x2-x1-12)/7));names=self._clip_channels(clip,d);title=d['name']+((' / '+names[0]) if len(names)==1 else f' / {len(names)} kanal');title=title if len(title)<=chars else title[:max(1,chars-1)]+'…';c.create_text(x1+6,y+22,text=title,fill=color,anchor='w',font=('Segoe UI',9,'bold'))
        if x2-x1>135:c.create_text(x1+6,y+45,text=f'{elapsed_text(start)} → {elapsed_text(end)}',fill='#405d75',anchor='w',font=('Segoe UI',8))
    # Fixed row labels and ruler stay visible while either scrollbar moves.
    c.create_rectangle(left,top,left+margin-6,bottom,fill='#f4f8fb',outline='')
    for row in self.timeline_rows:
      index=row_indices[row['uid']];y=28+index*row_height
      if y+row_height<top+28 or y>bottom:continue
      rounded_rect(c,left+3,y+3,left+margin-10,y+row_height-3,r=11,fill='#d7efee' if row['uid']==self.timeline_row else '#eaf2f8',outline=PALETTE[index%len(PALETTE)])
      c.create_text(left+12,y+25,text=row['name'],fill='#203449',anchor='w',font=('Segoe UI',9,'bold'));c.create_text(left+12,y+47,text='Aktif satır' if row['uid']==self.timeline_row else 'Seçmek için tıkla',fill='#60758a',anchor='w',font=('Segoe UI',8))
    c.create_rectangle(left,top,right,top+27,fill='#f4f8fb',outline='');c.create_text(left+12,top+13,text='SATIRLAR',fill='#60758a',anchor='w',font=('Segoe UI',8,'bold'))
    if total>0:
      step=max(total/1000000,100/max(scale,1e-12));power=10**math.floor(math.log10(step));step=next(v*power for v in (1,2,5,10) if v*power>=step);first=max(0,math.ceil(left/scale/step))
      for i in range(first,first+int(width/100)+4):
        sec=i*step;x=margin+sec*scale
        if sec>total or x>right+120:break
        if x<left+margin:continue
        c.create_line(x,top+20,x,top+27,fill='#60758a');c.create_text(x+3,top+11,text=elapsed_text(sec),fill='#526c82',anchor='w',font=('Segoe UI',8))
 def _timeline_row_at(self,event):
    if event.y<28:return None
    index=int((self.timeline_canvas.canvasy(event.y)-28)//76)
    return self.timeline_rows[index]['uid'] if 0<=index<len(self.timeline_rows) else None
 def _timeline_hit(self,event):
    if event.x<120 or event.y<28:return None
    x=self.timeline_canvas.canvasx(event.x);y=self.timeline_canvas.canvasy(event.y)
    return next((uid for uid,row,a,b,c,d in self._timeline_rects if a<=x<b and c<=y<d),None)
 def _timeline_press(self,event):
    row=self._timeline_row_at(event)
    if row is not None:self.timeline_row=row
    self.timeline_selected=self._timeline_hit(event);self._timeline_drag=(self.timeline_selected,event.x,event.y);self._render_timeline()
 def _timeline_drop_target(self,event,uid):
    row=self._timeline_row_at(event)
    if row is None:return None
    x=self.timeline_canvas.canvasx(max(120,event.x));peers=[(key,a,b) for key,r,a,b,y1,y2 in self._timeline_rects if r==row and key!=uid];target=sum(x>(a+b)/2 for key,a,b in peers)
    return row,target,peers
 def _timeline_motion(self,event):
    if not self._timeline_drag or self._timeline_drag[0] is None:return
    c=self.timeline_canvas
    if event.x<135:c.xview_scroll(-1,'units')
    elif event.x>c.winfo_width()-20:c.xview_scroll(1,'units')
    if event.y<40:c.yview_scroll(-1,'units')
    elif event.y>c.winfo_height()-15:c.yview_scroll(1,'units')
    self._render_timeline();target=self._timeline_drop_target(event,self._timeline_drag[0])
    if target:
      row,index,peers=target;ri=next(i for i,r in enumerate(self.timeline_rows) if r['uid']==row);y=28+ri*76;x=peers[index][1] if index<len(peers) else peers[-1][2] if peers else 120
      ya=max(y+1,c.canvasy(0)+28);yb=min(y+75,c.canvasy(c.winfo_height()));c.create_rectangle(c.canvasx(0)+120,ya,c.canvasx(c.winfo_width()),yb,outline='#007f85',width=2,tags='drop');c.create_line(max(x,c.canvasx(0)+120),ya,max(x,c.canvasx(0)+120),yb,fill='#203449',width=3,tags='drop')
 def _timeline_release(self,event):
    drag=self._timeline_drag;self._timeline_drag=None;self.timeline_canvas.delete('drop')
    if not drag or drag[0] is None or max(abs(event.x-drag[1]),abs(event.y-drag[2]))<5:return
    uid=drag[0];target=self._timeline_drop_target(event,uid);clip=next((c for c in self.timeline if c['uid']==uid),None)
    if clip is None or target is None:return
    row,index,peers=target;remaining=[c for c in self.timeline if c['uid']!=uid];positions=[i for i,c in enumerate(remaining) if c.get('row_uid',self.timeline_rows[0]['uid'])==row];position=positions[index] if index<len(positions) else positions[-1]+1 if positions else len(remaining)
    clip['row_uid']=row;remaining.insert(position,clip);self.timeline=remaining;self.timeline_row=row;self._timeline_changed()
 def _timeline_focus(self,event):
    uid=self._timeline_hit(event)
    if uid is None:return
    self.timeline_selected=uid
    for clip,d,start,end in self._timeline_layout():
      if clip['uid']==uid:self.ax.set_xlim(start,end);self.canvas.draw_idle();break
    self._render_timeline()
 def _timeline_wheel(self,event):
    if event.state&4:self.timeline_zoom(1.25 if event.delta>0 else .8)
    elif event.state&1:self._timeline_scroll('scroll',-3 if event.delta>0 else 3,'units')
    else:self._timeline_vscroll('scroll',-3 if event.delta>0 else 3,'units')
    return 'break'
 def _export_series(self):
    series=self._plot_series()
    if not self._timeline_active() or self.timeline_match.get()=='Ayrı çizgiler':return series
    tracks={}
    for entry in series:tracks.setdefault(entry['track'],[]).append(entry)
    return [{'label':items[0]['track_label'],'x':JoinedTimeAxis([e['x'] for e in items]),'y':JoinedValues([e['y'] for e in items])} for items in tracks.values()]
 def _panel_title(self,parent,text): tk.Label(parent,text=text,font=('Segoe UI',9,'bold'),fg='#60758a',bg='#f4f8fb',anchor='w').pack(fill='x',padx=10,pady=(12,7))
 def _button(self,parent,text,cmd):return GlassButton(parent,text,cmd)
 def _start_job(self,title,work,on_success,on_error=None):
    if self._job is not None:
      messagebox.showinfo('İşlem sürüyor','Devam eden işlemin bitmesini bekleyin veya İptal düğmesini kullanın.',parent=self);return False
    events=queue.Queue();cancel=threading.Event();self._job={'events':events,'cancel':cancel,'success':on_success,'error':on_error,'title':title}
    self._job_progress['value']=0;self._job_cancel.config(state='normal');self._job_bar.pack(before=self._body,fill='x',padx=14,pady=(0,4));self.status.set(title)
    def worker():
      previous=[0.0]
      def progress(fraction,message=''):
        now=time.perf_counter()
        if now-previous[0]>=.08 or fraction>=1:events.put(('progress',(max(0,min(1,fraction)),message)));previous[0]=now
      try:result=work(progress,cancel);events.put(('done',result))
      except Cancelled:events.put(('cancelled',None))
      except Exception as exc:events.put(('error',str(exc)))
    threading.Thread(target=worker,daemon=False,name='TraceDock-work').start();self.after(30,self._poll_job);return True
 def _poll_job(self):
    if self._closing or self._job is None:return
    job=self._job
    while True:
      try:kind,payload=job['events'].get_nowait()
      except queue.Empty:break
      if kind=='progress':self._job_progress['value']=payload[0]*100;self.status.set(job['title']+' • '+payload[1]);continue
      self._job=None;self._job_bar.pack_forget()
      if kind=='done':job['success'](payload)
      elif kind=='cancelled':self.status.set('İşlem iptal edildi')
      else:
        self.status.set('İşlem tamamlanamadı');messagebox.showerror(job['title'],payload,parent=self)
        if job['error']:job['error'](payload)
      return
    self.after(30,self._poll_job)
 def _cancel_job(self):
    self._pending_tdms=[]
    if self._job:self._job['cancel'].set();self._job_cancel.config(state='disabled');self.status.set('İptal ediliyor…')
 def _close_app(self):
    self._closing=True
    if self._job:self._job['cancel'].set()
    self.destroy()
 def add_csv(self):self._add_text_files('csv')
 def add_strain(self):self._add_text_files('strain')
 def _add_text_files(self,kind):
    if self._job is not None:return
    title='Strain Gauge dosyalarını seçin' if kind=='strain' else 'CSV dosyalarını seçin'
    paths=filedialog.askopenfilenames(title=title,filetypes=[('Strain Gauge / Exlab','*.csv *.txt *.tsv *.asc')] if kind=='strain' else [('CSV','*.csv'),('Tüm dosyalar','*.*')])
    if not paths:return
    def work(progress,cancel):
      datasets=[];errors=[];size=sum(os.path.getsize(path) for path in paths);plan=resource_plan(size);pool=new_process_pool(plan) if size>=32*2**20 and plan['workers']>1 else None
      try:
        for i,path in enumerate(paths):
          check_cancel(cancel)
          try:
            d=parse_text_file(path,lambda f,msg:progress((i+.7*f)/len(paths),Path(path).name+' • '+msg),cancel,kind,pool,plan)
            datasets.append(prepare_dataset(d,lambda f,msg:progress((i+.7+.3*f)/len(paths),Path(path).name+' • '+msg),cancel))
          except Cancelled:raise
          except Exception as exc:errors.append(f'{Path(path).name}: {exc}')
      finally:
        if pool:pool.shutdown(wait=True,cancel_futures=True)
      return datasets,errors
    def complete(result):
      datasets,errors=result
      for d in datasets:self.datasets.append(d)
      if datasets:self.active=len(self.datasets)-1;self.selected=set(datasets[-1]['_selected'])
      self.redraw_all(preserve_view=True);self.status.set(f'{len(datasets)} dosya yüklendi • özgün veriler korundu')
      if errors:messagebox.showerror('Okunamayan dosyalar','\n'.join(errors),parent=self)
      warnings=[d['name']+': '+d['timing_warning'] for d in datasets if d.get('timing_warning')]
      if warnings:messagebox.showinfo('Zaman bilgisi','\n'.join(warnings),parent=self)
    self._start_job('Strain Gauge yükleniyor' if kind=='strain' else 'CSV yükleniyor',work,complete)

 def _refresh_values(self):
    for d in self.datasets:
      for name,values in d['_base_channels'].items():
        factor=float(d.get('multipliers',{}).get(name,1))*float(d.get('data_multiplier',1));current=d['channels'][name]
        if (factor==1 and current is values) or (isinstance(current,ScaledValues) and current.base is values and current.factor==factor):continue
        d['channels'][name]=values if factor==1 else ScaledValues(values,factor)

 def _tdms_settings(self,channels):
    win=tk.Toplevel(self);win.title('TDMS kanal hızları ve çarpanları');win.geometry('860x600');win.transient(self);win.grab_set();win.configure(bg='#f4f8fb')
    tk.Label(win,text='Hız metaverisi otomatik doldurulur. Kanallar en yüksek hıza eşitlenir; her kanalın çarpanını düzenleyin.',fg='#203449',bg='#f4f8fb',font=('Segoe UI',11,'bold')).pack(anchor='w',padx=14,pady=(14,8))
    frame=tk.Frame(win,bg='#f4f8fb');frame.pack(fill='both',expand=True,padx=14,pady=8)
    tree=ttk.Treeview(frame,columns=('channel','rate','factor'),show='headings');tree.heading('channel',text='Grup / kanal');tree.heading('rate',text='Örnekleme hızı (Hz)');tree.heading('factor',text='Çarpan');tree.column('channel',width=500);tree.column('rate',width=170,anchor='center');tree.column('factor',width=130,anchor='center');sb=ttk.Scrollbar(frame,orient='vertical',command=tree.yview);tree.configure(yscrollcommand=sb.set);tree.pack(side='left',fill='both',expand=True);sb.pack(side='right',fill='y')
    for i,ch in enumerate(channels):tree.insert('','end',iid=str(i),values=(ch['name'],ch['default_rate'],'1'))
    editor={'widget':None}
    def edit(event):
      item=tree.identify_row(event.y);column=tree.identify_column(event.x)
      if not item or column not in ('#2','#3'):return
      box=tree.bbox(item,column)
      if not box:return
      x,y,w,h=box;values=list(tree.item(item,'values'));index=int(column[1:])-1;ent=tk.Entry(tree);ent.place(x=x,y=y,width=w,height=h);ent.insert(0,values[index]);ent.select_range(0,tk.END);ent.focus_set();editor['widget']=ent
      def save(_event=None):
        if editor['widget'] is None:return
        values[index]=editor['widget'].get().strip();tree.item(item,values=values);editor['widget'].destroy();editor['widget']=None
      ent.bind('<Return>',save);ent.bind('<FocusOut>',save);ent.bind('<Escape>',lambda _e:(ent.destroy(),editor.update(widget=None)))
    tree.bind('<Double-1>',edit)
    result={'settings':None}
    buttons=tk.Frame(win,bg='#f4f8fb');buttons.pack(fill='x',padx=14,pady=(4,14))
    def accept():
      for i in range(len(channels)):
        if editor['widget'] is not None:editor['widget'].event_generate('<Return>')
        row=tree.item(str(i),'values')
        try:
          rate=int(row[1]);factor=float(row[2].replace(',','.'))
          if rate<=0 or not math.isfinite(factor):raise ValueError
        except (ValueError,IndexError):messagebox.showerror('Ayarları kontrol edin',f"{row[0]} için pozitif tam sayı Hz ve geçerli çarpan girin.",parent=win);return
      result['settings']=[(int(tree.item(str(i),'values')[1]),float(tree.item(str(i),'values')[2].replace(',','.'))) for i in range(len(channels))]
      win.destroy()
    self._button(buttons,'Vazgeç',win.destroy).pack(side='right')
    self._button(buttons,'Senkronize et',accept).pack(side='right',padx=8)
    self.wait_window(win)
    return result['settings']
 def add_tdms(self):
    if self._job is not None:return
    paths=filedialog.askopenfilenames(title='NI TDMS dosyalarını seçin',filetypes=[('NI TDMS','*.tdms'),('Tüm dosyalar','*.*')])
    self._pending_tdms=list(paths);self._next_tdms()
 def _next_tdms(self):
    if not self._pending_tdms:return
    path=self._pending_tdms.pop(0)
    def read(progress,cancel):
      channels=[]
      with TdmsFile.open(path) as tdms:
        source=[(group,ch) for group in tdms.groups() for ch in group.channels()]
        for i,(group,ch) in enumerate(source):
          check_cancel(cancel);props=ch.properties;rate=''
          try:
            increment=float(props.get('wf_increment',0));hz=1/increment if increment>0 else 0
            if hz>0 and abs(hz-round(hz))<1e-7:rate=str(round(hz))
          except (ValueError,TypeError,ZeroDivisionError):pass
          channels.append({'name':f'{group.name}/{ch.name}','values':np.asarray(ch[:]),'unit':str(props.get('unit_string',props.get('unit',''))),'id':str(props.get('NI_ChannelNumber',ch.name)),'default_rate':rate});progress((i+1)/max(1,len(source)),f'{i+1}/{len(source)} kanal okundu')
      if not channels:raise ValueError('TDMS dosyasında kanal bulunamadı.')
      return channels
    def loaded(channels):
      settings=self._tdms_settings(channels)
      if settings is None:self.after_idle(self._next_tdms);return
      destination=filedialog.asksaveasfilename(title='Senkronize TDMS CSV dosyasını kaydet',initialfile=f'{Path(path).stem}_senkronize.csv',initialdir=str(Path(path).parent),defaultextension='.csv',filetypes=[('CSV','*.csv')])
      if not destination:self.after_idle(self._next_tdms);return
      rates=[pair[0] for pair in settings];factors=[pair[1] for pair in settings];common=max(rates);row_count=max((math.ceil(len(ch['values'])*common/rate-1e-10) for ch,rate in zip(channels,rates)),default=0)
      if row_count>5_000_000 and not messagebox.askyesno('Büyük çıktı',f'Ortak hız {common:,} Hz ve yaklaşık {row_count:,} satır olacak. Devam edilsin mi?',parent=self):self.after_idle(self._next_tdms);return
      decimal=self.decimal.get()
      def convert(progress,cancel):
        base={};aligned={};ids={};units={};clock=SampleTimeAxis(row_count,common)
        def align(item):
          ch,rate,factor=item;check_cancel(cancel);data=ch['values']
          if data.dtype.kind not in 'iufb':raise ValueError(f"{ch['name']} sayısal olmayan veri içeriyor.")
          valid=min(row_count,math.ceil(len(data)*common/rate-1e-10));values=np.full(row_count,np.nan)
          for start in range(0,valid,65536):
            check_cancel(cancel);stop=min(valid,start+65536);idx=np.minimum((np.arange(start,stop,dtype=float)*rate/common).astype(np.int64),len(data)-1);values[start:stop]=data[idx]
          return ch['name'],values
        workers=min(len(channels),resource_plan(row_count*len(channels)*8)['workers']);results={}
        with ThreadPoolExecutor(max_workers=max(1,workers),thread_name_prefix='TraceDock-TDMS') as executor:
          futures=[executor.submit(align,item) for item in zip(channels,rates,factors)]
          for i,future in enumerate(as_completed(futures)):
            name,values=future.result();results[name]=values;progress(.25*(i+1)/len(channels),name+' eşlendi')
        for ch,factor in zip(channels,factors):
          name=ch['name'];values=results[name];base[name]=values;aligned[name]=values if factor==1 else ScaledValues(values,factor);ids[name]=ch['id'];units[name]=ch['unit']
        metadata=[['ID']+list(ids.values()),['Unit']+list(units.values()),['SampleRate']+rates,['Multiplier']+[number_text(v,decimal) for v in factors],['CommonRate']+[common]*len(channels)]
        series=[{'label':name,'x':clock,'y':values} for name,values in aligned.items()]
        d={'name':Path(destination).name,'path':str(destination),'xname':'time','x':clock,'_base_x':clock,'x_is_date':False,'channels':aligned,'units':units,'ids':ids,'sample_rates':dict(zip(aligned,rates)),'grid_rate':common,'_base_rate':common,'multipliers':dict(zip(aligned,factors)),'_base_channels':base}
        prepare_dataset(d,lambda f,msg:progress(.25+.2*f,msg),cancel)
        write_series_csv(destination,series,0,float('inf'),decimal,True,lambda f,msg:progress(.45+.55*f,msg),cancel,metadata)
        return d
      def complete(d):
        self.datasets.append(d);self.active=len(self.datasets)-1;self.selected=set(d['_selected']);self.redraw_all(preserve_view=True);self.status.set(f'{Path(path).name} dönüştürüldü • {common:,} Hz • {row_count:,} satır');self.after_idle(self._next_tdms)
      self._start_job('TDMS dönüştürülüyor',convert,complete,lambda msg:self.after_idle(self._next_tdms))
    self._start_job('TDMS okunuyor',read,loaded,lambda msg:self.after_idle(self._next_tdms))

 def _elapsed(self,index,rate):
    ticks=(index*10_000+rate//2)//rate;total,frac=divmod(ticks,10_000);hours,rem=divmod(total,3600);minutes,seconds=divmod(rem,60);return f'{hours:02d}:{minutes:02d}:{seconds:02d}.{frac:04d}'
 def remove_file(self):
    if not self.datasets:return
    removed=self.datasets.pop(self.active);self.active=max(0,min(self.active,len(self.datasets)-1))
    contexts={removed['uid']}|{'clip:'+c['uid'] for c in self.timeline if c['dataset_uid']==removed['uid']};self.timeline=[c for c in self.timeline if c['dataset_uid']!=removed['uid']];self.probes={key:items for key,items in self.probes.items() if key[0] not in contexts};self.span=None
    self._channel_axes={key:slot for key,slot in self._channel_axes.items() if key[0]!=removed['uid']}
    self.selected=set(self.datasets[self.active]['_selected']) if self.datasets else set();self.redraw_all()

 def switch_file(self,event=None):
    sel=self.filelist.curselection()
    if not sel or int(sel[0])==self.active:return
    self._activate_dataset(int(sel[0]))

 def rename_dataset(self,event=None):
    if not self.datasets:return
    new=simpledialog.askstring('Veri adı','Yeni veri adı:',initialvalue=self.datasets[self.active]['name'],parent=self)
    if new and new.strip():self.datasets[self.active]['name']=new.strip();self.redraw_all()
 def render_channels(self):
    if not hasattr(self,'channel_tree'):
      self.channel_tree=ttk.Treeview(self.chlist,columns=('rate','duration','factor','axis'),show='tree headings',selectmode='extended')
      tree=self.channel_tree;tree.tag_configure('dataset',foreground='#007f85',font=('Segoe UI',9,'bold'));tree.heading('#0',text='Dosya / kanal');tree.column('#0',width=205,minwidth=130)
      for col,label,width in [('rate','Hz',82),('duration','Süre (s)',96),('factor','Çarpan',70),('axis','Y ekseni',78)]:tree.heading(col,text=label);tree.column(col,width=width,minwidth=55,anchor='e')
      sb=ttk.Scrollbar(self.chlist,orient='vertical',command=tree.yview);hs=ttk.Scrollbar(self.chlist,orient='horizontal',command=tree.xview)
      tree.configure(yscrollcommand=sb.set,xscrollcommand=hs.set);sb.pack(side='right',fill='y');hs.pack(side='bottom',fill='x');tree.pack(fill='both',expand=True)
      self._check_images={}
      for checked in (False,True,'mixed'):
        icon=tk.PhotoImage(width=14,height=14);icon.put('#b1c7d7',to=(0,0,14,14));icon.put('#ffffff',to=(1,1,13,13))
        if checked=='mixed':icon.put('#007f85',to=(3,6,11,8))
        elif checked:
          for x,y in [(3,6),(4,7),(5,8),(6,7),(7,6),(8,5),(9,4),(10,3)]:icon.put('#007f85',to=(x,y,x+2,y+2))
        self._check_images[checked]=icon
      tree.bind('<Button-1>',self._channel_tree_click);tree.bind('<Double-Button-1>',self._channel_tree_edit);tree.bind('<space>',self._channel_tree_space);tree.bind('<Button-3>',self._channel_tree_menu);tree.bind('<Menu>',lambda e:self._channel_tree_menu(e,True));tree.bind('<Shift-F10>',lambda e:self._channel_tree_menu(e,True))
    tree=self.channel_tree;highlighted=tree.selection();closed={iid for iid in tree.get_children() if not tree.item(iid,'open')};scroll=tree.yview();focus=tree.focus()
    for iid in tree.get_children():tree.delete(iid)
    self._tree_rows={};q=self.filter.get().casefold();axis_labels=self._source_axis_labels()
    for di,d in enumerate(self.datasets):
      names=[name for name in d['channels'] if q in name.casefold() or q in d['name'].casefold()]
      if not names:continue
      group='d_'+d['uid'];rates=list(d['channel_rates'].values());durations=[len(d['channels'][n])/d['channel_rates'][n] for n in d['channels']]
      def summary(values):return self._number(values[0]) if values and all(math.isclose(v,values[0],rel_tol=1e-8,abs_tol=1e-9) for v in values) else 'Karışık'
      tree.insert('','end',iid=group,text=d['name'],values=(summary(rates),summary(durations),self._number(d.get('data_multiplier',1)),self._dataset_axis_label(d,axis_labels)),open=group not in closed,image=self._check_images[self._channel_group_state(d)],tags=('dataset',))
      self._tree_rows[group]=(di,None)
      for ci,name in enumerate(d['channels']):
        if name not in names:continue
        iid=f'{group}_c{ci}';rate=d['channel_rates'][name];label=name
        axis_label=axis_labels.get((d['uid'],name),Y_AXIS_LABELS[self._channel_axes.get((d['uid'],name),'L1')]);tree.insert(group,'end',iid=iid,text=label,image=self._check_images[name in d['_selected']],values=(self._number(rate),self._number(len(d['channels'][name])/rate),self._number(d.get('multipliers',{}).get(name,1)),axis_label))
        self._tree_rows[iid]=(di,name)
    if focus in self._tree_rows:tree.focus(focus)
    tree.selection_set(tuple(iid for iid in highlighted if iid in self._tree_rows))
    if self._tree_anchor not in self._tree_rows:self._tree_anchor=None
    if scroll:tree.yview_moveto(scroll[0])
    self._sidebar_bind_widgets(self.sidebar_content);self._schedule_sidebar_layout()
 def _channel_group_state(self,d):
    count=sum(name in d['_selected'] for name in d['channels'])
    return False if count==0 else True if count==len(d['channels']) else 'mixed'
 def _visible_channel_rows(self):
    tree=self.channel_tree;rows=[]
    def visit(parent=''):
      for iid in tree.get_children(parent):
        rows.append(iid)
        if tree.item(iid,'open'):visit(iid)
    visit();return rows
 def _channel_tree_click(self,event):
    tree=self.channel_tree;iid=tree.identify_row(event.y)
    if iid not in self._tree_rows:return
    element=tree.identify_element(event.x,event.y)
    if 'indicator' in element:return
    di,name=self._tree_rows[iid];self.active=di;self.selected=set(self.datasets[di]['_selected']);self.filelist.selection_clear(0,'end');self.filelist.selection_set(di);previous_focus=tree.focus();tree.focus(iid);tree.focus_set();checkbox='image' in element;shift=bool(event.state&1);control=bool(event.state&4)
    if shift:
      visible=self._visible_channel_rows();anchor=self._tree_anchor if self._tree_anchor in visible else previous_focus if previous_focus in visible else iid;self._tree_anchor=anchor;a,b=sorted((visible.index(anchor),visible.index(iid)));chosen=visible[a:b+1]
      tree.selection_set(tuple(dict.fromkeys(list(tree.selection())+chosen)) if control else tuple(chosen))
    elif control and not checkbox:
      if iid in tree.selection():tree.selection_remove(iid)
      else:tree.selection_add(iid)
      self._tree_anchor=iid
    elif not checkbox or iid not in tree.selection():tree.selection_set(iid);self._tree_anchor=iid
    if checkbox:self._toggle_tree_row(iid)
    return 'break'
 def _channel_tree_menu(self,event,keyboard=False):
    tree=self.channel_tree;iid=tree.focus() if keyboard else tree.identify_row(event.y)
    if iid not in self._tree_rows or (not keyboard and tree.identify_column(event.x)!='#0'):return 'break'
    di,name=self._tree_rows[iid];d=self.datasets[di];self.active=di;self.selected=set(d['_selected']);self.filelist.selection_clear(0,'end');self.filelist.selection_set(di);tree.focus(iid)
    if iid not in tree.selection():tree.selection_set(iid);self._tree_anchor=iid
    names=tuple(n for n in d['channels'] if n in d['_selected']) if name is None else (name,);uid=d['uid'];options=dict(tearoff=False,bg='#f4f8fb',fg='#203449',activebackground='#d7efee',activeforeground='#164e58',disabledforeground='#60758a',relief='flat',borderwidth=1,font=('Segoe UI',10))
    previous=getattr(self,'_channel_menu',None)
    if previous is not None:previous.destroy()
    menu=tk.Menu(self,**options);self._channel_menu=menu;menu.add_command(label=(d['name']+f' / {len(names)} işaretli kanal') if name is None else name,state='disabled');menu.add_separator();rows=tk.Menu(menu,**options)
    for row in self.timeline_rows:rows.add_command(label=row['name']+' satırına ekle',command=lambda row_uid=row['uid']:self._timeline_add_source(uid,names,row_uid))
    menu.add_cascade(label='Mevcut satıra ekle',menu=rows,state='normal' if names else 'disabled');menu.add_command(label='Yeni satıra ekle',command=lambda:self._timeline_add_source(uid,names,new_row=True),state='normal' if names else 'disabled')
    menu.add_separator();axis_menu=tk.Menu(menu,**options)
    for slot,label in Y_AXIS_LABELS.items():axis_menu.add_command(label=label,command=lambda selected_slot=slot:self._assign_source_axis(uid,names,selected_slot))
    menu.add_cascade(label='Y eksenine ata',menu=axis_menu,state='normal' if names else 'disabled')
    if keyboard:
      box=tree.bbox(iid,'#0')
      if not box:return 'break'
      x=tree.winfo_rootx()+box[0]+min(120,box[2]);y=tree.winfo_rooty()+box[1]+box[3]
    else:x,y=event.x_root,event.y_root
    try:menu.tk_popup(x,y)
    finally:menu.grab_release()
    return 'break'
 def _channel_check_targets(self,iids):
    targets={}
    for iid in iids:
      if iid not in self._tree_rows:continue
      di,name=self._tree_rows[iid];d=self.datasets[di];targets.setdefault(di,set()).update(d['channels'] if name is None else (name,))
    return targets
 def _update_channel_checks(self):
    for iid,(di,name) in self._tree_rows.items():
      d=self.datasets[di];state=self._channel_group_state(d) if name is None else name in d['_selected'];self.channel_tree.item(iid,image=self._check_images[state])
 def _set_channel_checks(self,checked=None):
    tree=self.channel_tree;iids=tree.selection() or ((tree.focus(),) if tree.focus() in self._tree_rows else ());targets=self._channel_check_targets(iids)
    if not targets:self.status.set('Önce kanalları seçin • Shift+tık ile bir aralık seçebilirsiniz');return
    if checked is None:checked=not all(names<=self.datasets[di]['_selected'] for di,names in targets.items())
    count=0
    for di,names in targets.items():
      selected=self.datasets[di]['_selected']
      if checked:selected.update(names)
      else:selected.difference_update(names)
      count+=len(names)
    self.selected=set(self.datasets[self.active]['_selected']);self._update_channel_checks();self.status.set(f'{count} kanal '+('işaretlendi' if checked else 'işareti kaldırıldı')+' • Grafik için zaman çizelgesine ekleyin')
 def _channel_tree_space(self,event):
    self._set_channel_checks();return 'break'
 def _toggle_tree_row(self,iid):
    di,name=self._tree_rows[iid];d=self.datasets[di];checked=self._channel_group_state(d) is not True if name is None else name not in d['_selected']
    self._set_channel_checks(checked)
 def _channel_tree_edit(self,event):
    tree=self.channel_tree;iid=tree.identify_row(event.y);column=tree.identify_column(event.x)
    if iid not in self._tree_rows:return 'break'
    if 'indicator' in tree.identify_element(event.x,event.y) or 'image' in tree.identify_element(event.x,event.y):return 'break'
    di,name=self._tree_rows[iid];self.active=di;self.selected=set(self.datasets[di]['_selected'])
    if column=='#0':
      if name is None:self.rename_dataset()
      else:self.rename_channel(name)
    elif column=='#1':self.edit_timing(di,name,'rate')
    elif column=='#2':self.edit_timing(di,name,'duration')
    elif column=='#3':
      if name is None:self.edit_dataset_multiplier()
      else:self.edit_channel_multiplier(name)
    elif column=='#4':
      names=tuple(n for n in self.datasets[di]['channels'] if n in self.datasets[di]['_selected']) if name is None else (name,);self._source_axis_menu(self.datasets[di]['uid'],names,event.x_root,event.y_root)
    return 'break'
 def edit_timing(self,index,name,field):
    d=self.datasets[index];names=[name] if name is not None else list(d['channels']);label=name or (d['name']+' / tüm kanallar')
    current=[d['channel_rates'][n] if field=='rate' else len(d['channels'][n])/d['channel_rates'][n] for n in names]
    same=all(math.isclose(v,current[0],rel_tol=1e-8,abs_tol=1e-9) for v in current)
    prompt=f'{label}\n'+('Veri okuma frekansı (Hz):' if field=='rate' else 'Test süresi (saniye veya HH:MM:SS.SSSS):')
    value=simpledialog.askstring('Frekansı düzenle' if field=='rate' else 'Test süresini düzenle',prompt,initialvalue=f'{current[0]:.12g}' if same else '',parent=self)
    if value is None:return
    try:
      raw=value.strip().replace(',','.')
      if field=='duration' and ':' in raw:
        parts=raw.split(':')
        if len(parts)!=3:raise ValueError('Süre HH:MM:SS.SSSS biçiminde olmalı.')
        hours,minutes,seconds=map(float,parts)
        if hours<0 or not 0<=minutes<60 or not 0<=seconds<60:raise ValueError('Süre alanlarını kontrol edin.')
        number=hours*3600+minutes*60+seconds
      else:number=float(raw)
      set_timing(d,names,field,number)
    except ValueError as exc:messagebox.showerror('Geçersiz zaman değeri',str(exc),parent=self);return
    self.mouse_data=None;self.span=None;self.redraw_all();self.status.set(f'{label} zaman bilgisi güncellendi • özgün örnek sayısı korundu')

 def _activate_dataset(self,index):
    self.active=index;self.selected=set(self.datasets[index]['_selected']);self.filelist.selection_clear(0,'end');self.filelist.selection_set(index);self.render_channels()


 def edit_dataset_multiplier(self,event=None):
    if not self.datasets:return
    if event is not None:
      index=self.filelist.nearest(event.y)
      if 0<=index<len(self.datasets):self.filelist.selection_clear(0,'end');self.filelist.selection_set(index);self.active=index;self.selected=set(self.datasets[index].get('_selected',list(self.datasets[index]['channels'])[:6]))
    current=float(self.datasets[self.active].get('data_multiplier',1.0));value=simpledialog.askstring('Veri çarpanı',f"{self.datasets[self.active]['name']} için tüm kanallara uygulanacak çarpan:",initialvalue=str(current),parent=self)
    if value is None:return
    try:factor=float(value.replace(',','.'))
    except ValueError:messagebox.showerror('Geçersiz çarpan','Sayısal bir çarpan girin.',parent=self);return
    if not math.isfinite(factor):messagebox.showerror('Geçersiz çarpan','Sonlu bir sayı girin.',parent=self);return
    self.datasets[self.active]['data_multiplier']=factor;self._refresh_values();self.redraw_all();self.status.set(f"{self.datasets[self.active]['name']} veri çarpanı {self._number(factor)} olarak ayarlandı")
 def edit_channel_multiplier(self,name):
    if not self.datasets:return
    d=self.datasets[self.active];current=float(d.get('multipliers',{}).get(name,1.0));value=simpledialog.askstring('Kanal çarpanı',f'{name} için çarpan:',initialvalue=str(current),parent=self)
    if value is None:return
    try:factor=float(value.replace(',','.'))
    except ValueError:messagebox.showerror('Geçersiz çarpan','Sayısal bir çarpan girin.',parent=self);return
    if not math.isfinite(factor):messagebox.showerror('Geçersiz çarpan','Sonlu bir sayı girin.',parent=self);return
    d.setdefault('multipliers',{})[name]=factor;self._refresh_values();self.redraw_all();self.status.set(f'{name} çarpanı {self._number(factor)} olarak ayarlandı')
 def rename_channel(self,old):
    if not self.datasets:return
    d=self.datasets[self.active];new=simpledialog.askstring('Kanal adını değiştir','Yeni kanal adı:',initialvalue=old,parent=self)
    if new is None or not new.strip() or new.strip()==old:return
    new=new.strip()
    if new in d['channels']:messagebox.showwarning('Kanal adı kullanılıyor',f'“{new}” adlı kanal zaten var.',parent=self);return
    for field in ('channels','units','ids','_base_channels','multipliers','channel_rates','sample_rates','_channel_x','_base_stats','_envelopes'):
      if old in d.get(field,{}):d[field]={new if key==old else key:value for key,value in d[field].items()}
    axis_key=(d['uid'],old)
    if axis_key in self._channel_axes:self._channel_axes[(d['uid'],new)]=self._channel_axes.pop(axis_key)
    if old in d['_selected']:d['_selected'].remove(old);d['_selected'].add(new)
    for clip in self.timeline:
      if clip['dataset_uid']==d['uid'] and 'channels' in clip:clip['channels']=[new if n==old else n for n in clip['channels']]
    contexts=[d['uid']]+['clip:'+c['uid'] for c in self.timeline if c['dataset_uid']==d['uid']]
    for context in contexts:
      old_key=(context,old);new_key=(context,new)
      if old_key in self.probes:self.probes[new_key]=self.probes.pop(old_key)
    self.selected=set(d['_selected']);self.redraw_all();self.status.set(f'Kanal adı değiştirildi: {old} → {new}')


 def redraw_all(self,preserve_view=False):
    self.filelist.delete(0,'end')
    for d in self.datasets:self.filelist.insert('end',d['name'])
    if self.datasets:
      self.filelist.selection_set(self.active);self.filelist.activate(self.active);self.selected=set(self.datasets[self.active]['_selected'])
    self._xchoices={};self.xcombo['values']=['Geçen süre'];self.xcombo.set('Geçen süre')
    self.render_channels();self._render_timeline();self.redraw(preserve_view=preserve_view)

 def _key_label(self,key):
    row_counts={}
    for clip,d,start,end in self._timeline_layout():
      row_uid=clip.get('row_uid',self.timeline_rows[0]['uid']);row_counts[row_uid]=row_counts.get(row_uid,0)+1
      if key[0]=='clip:'+clip['uid']:return f"{self._timeline_row_info(row_uid)['name']} / {d['name']} / {key[1]} [Paket {row_counts[row_uid]}]"
    for d in self.datasets:
      if d['uid']==key[0]:return f"{d['name']} / {key[1]}"
    return str(key[1])
 def _plot_series(self,limited=True):
    series=[];limit=(999999 if self.limit.get()=='Tümü' else int(self.limit.get() or 12)) if limited else 999999
    tracks=set();policy=self.timeline_match.get();row_counts={}
    for clip,d,start,end in self._timeline_layout():
      row_uid=clip.get('row_uid',self.timeline_rows[0]['uid']);row=self._timeline_row_info(row_uid);ci=row_counts.get(row_uid,0);row_counts[row_uid]=ci+1;names=set(self._clip_channels(clip,d))
      for column,(name,y) in enumerate(d['channels'].items()):
        if name not in names:continue
        key=('clip:'+clip['uid'],name);channel_track=name if policy=='Kanal adına göre' else column if policy=='Sütun sırasına göre' else key;track=(row_uid,channel_track)
        if track not in tracks and len(tracks)>=limit:continue
        tracks.add(track);clock=SampleTimeAxis(len(y),d['channel_rates'][name],origin=start);channel_label=f'Sütun {column+1} / {name}' if policy=='Sütun sırasına göre' else name if policy=='Kanal adına göre' else f"{d['name']} / {name} [Paket {ci+1}]"
        series.append({'key':key,'name':name,'dataset':d,'label':f"{row['name']} / {d['name']} / {name} [Paket {ci+1}]",'x':clock,'time':clock,'y':y,'track':track,'track_label':f"{row['name']} / {channel_label}",'row_uid':row_uid,'clip_index':ci,'clip_start':start,'clip_end':end})
    return series
 def _axis_slot(self,entry):
    return self._track_axes.setdefault(entry['track'],self._channel_axes.get((entry['dataset']['uid'],entry['name']),'L1'))
 def _source_axis_labels(self):
    slots={}
    for entry in self._plot_series(limited=False):slots.setdefault((entry['dataset']['uid'],entry['name']),set()).add(self._axis_slot(entry))
    return {key:Y_AXIS_LABELS[next(iter(values))] if len(values)==1 else 'Karışık' for key,values in slots.items()}
 def _dataset_axis_label(self,d,labels):
    values={labels.get((d['uid'],name),Y_AXIS_LABELS[self._channel_axes.get((d['uid'],name),'L1')]) for name in d['channels']}
    return next(iter(values)) if len(values)==1 else 'Karışık'
 def _axis_menu(self,tracks,x,y):
    if not tracks:return
    old=getattr(self,'_y_axis_menu',None)
    if old is not None:old.destroy()
    menu=tk.Menu(self,tearoff=False,bg='#f4f8fb',fg='#203449',activebackground='#d7efee',activeforeground='#164e58',font=('Segoe UI',10));self._y_axis_menu=menu
    for slot,label in Y_AXIS_LABELS.items():menu.add_command(label='Y ekseni: '+label,command=lambda chosen=slot:self._assign_track_axes(tracks,chosen))
    menu.add_separator();menu.add_command(label='Y eksenleri penceresi…',command=self._show_y_axes)
    try:menu.tk_popup(round(x),round(y))
    finally:menu.grab_release()
 def _source_axis_menu(self,uid,names,x,y):
    if not names:self.status.set('Önce bir kanal işaretleyin');return
    menu=tk.Menu(self,tearoff=False,bg='#f4f8fb',fg='#203449',activebackground='#d7efee',activeforeground='#164e58',font=('Segoe UI',10));self._y_axis_menu=menu
    for slot,label in Y_AXIS_LABELS.items():menu.add_command(label='Y ekseni: '+label,command=lambda chosen=slot:self._assign_source_axis(uid,names,chosen))
    try:menu.tk_popup(round(x),round(y))
    finally:menu.grab_release()
 def _assign_source_axis(self,uid,names,slot):
    if slot not in Y_AXIS_LABELS:return
    entries=self._plot_series(limited=False);names=set(names);tracks={entry['track'] for entry in entries if entry['dataset']['uid']==uid and entry['name'] in names}
    self._reset_axis_slots.update(self._axis_slot(entry) for entry in entries if entry['track'] in tracks)
    for name in names:self._channel_axes[(uid,name)]=slot
    for entry in entries:
      if entry['track'] in tracks:self._reset_axis_slots.add(self._axis_slot(entry));self._channel_axes[(entry['dataset']['uid'],entry['name'])]=slot
    self._track_axes.update({track:slot for track in tracks});self._reset_axis_slots.add(slot);self.redraw_all(preserve_view=True);self.status.set(f'{len(names)} kanal → {Y_AXIS_LABELS[slot]}')
 def _assign_track_axes(self,tracks,slot):
    if slot not in Y_AXIS_LABELS:return
    tracks=set(tracks);entries=self._plot_series(limited=False)
    for entry in entries:
      if entry['track'] in tracks:self._reset_axis_slots.add(self._axis_slot(entry))
    self._track_axes.update({track:slot for track in tracks});self._reset_axis_slots.add(slot);self.redraw_all(preserve_view=True);self.status.set(f'{len(tracks)} eğri → {Y_AXIS_LABELS[slot]}')
 def _show_y_axes(self):
    win=tk.Toplevel(self);win.title('Y eksenleri');win.geometry('790x470');win.configure(bg='#f4f8fb');win.transient(self)
    tk.Label(win,text='Solda 2, sağda 2 bağımsız Y ekseni. Kanal seçip eksene atayın.',bg='#f4f8fb',fg='#203449',font=('Segoe UI',11,'bold')).pack(fill='x',padx=14,pady=(14,8))
    area=tk.Frame(win,bg='#f4f8fb');area.pack(fill='both',expand=True,padx=14);tree=ttk.Treeview(area,columns=('channel','unit','axis'),show='headings',selectmode='extended');tree.heading('channel',text='Zaman çizelgesi / kanal');tree.heading('unit',text='Birim');tree.heading('axis',text='Y ekseni');tree.column('channel',width=500);tree.column('unit',width=90);tree.column('axis',width=100);self._pack_measurement_table(tree,area)
    by_track={}
    for entry in self._plot_series(limited=False):by_track.setdefault(entry['track'],entry)
    keys=list(by_track)
    def fill():
      selected=tree.selection()
      for iid in tree.get_children():tree.delete(iid)
      for i,key in enumerate(keys):
        entry=by_track[key];tree.insert('','end',iid=str(i),values=(entry['track_label'],entry['dataset'].get('units',{}).get(entry['name'],''),Y_AXIS_LABELS[self._axis_slot(entry)]))
      tree.selection_set(tuple(i for i in selected if tree.exists(i)))
    fill();bar=tk.Frame(win,bg='#f4f8fb');bar.pack(fill='x',padx=14,pady=12);choice=ttk.Combobox(bar,state='readonly',values=list(Y_AXIS_LABELS.values()),width=12);choice.set('Sol 1');choice.pack(side='left',padx=(0,6))
    def apply():
      selected=[keys[int(i)] for i in tree.selection()]
      if not selected:return
      slot=next(slot for slot,label in Y_AXIS_LABELS.items() if label==choice.get());self._assign_track_axes(selected,slot);fill()
    def reset():
      self._channel_axes.clear();self._track_axes.clear();self._reset_axis_slots=set(Y_AXIS_LABELS);self.redraw_all(preserve_view=True);fill()
    self._button(bar,'Seçilenlere uygula',apply).pack(side='left');self._button(bar,'Tümünü Sol 1’e al',reset).pack(side='left',padx=6);self._button(bar,'Kapat',win.destroy).pack(side='right');tk.Label(win,text='Shift / Ctrl ile çoklu seçim • Lejanttaki kanal adına tıklayarak da eksen seçebilirsiniz.',bg='#f4f8fb',fg='#60758a').pack(fill='x',padx=14,pady=(0,10))
 def _configure_y_axes(self,series):
    for axis in list(self.fig.axes):
      if axis is not self.ax:axis.remove()
    self._y_axes={'L1':self.ax};self._used_axis_slots={self._axis_slot(entry) for entry in series};self._layout_y_axes()
    for slot in Y_AXIS_LABELS:
      if slot=='L1' or slot not in self._used_axis_slots:continue
      axis=self.ax.twinx();axis.patch.set_visible(False);axis.xaxis.set_visible(False)
      for spine in axis.spines.values():spine.set_visible(False)
      side='left' if slot=='L2' else 'right';axis.spines[side].set_visible(True);axis.spines[side].set_position(('outward',68 if slot in ('L2','R2') else 0));axis.yaxis.set_ticks_position(side);axis.yaxis.set_label_position(side);axis.grid(False);self._y_axes[slot]=axis
    for slot,axis in self._y_axes.items():
      units={str(entry['dataset'].get('units',{}).get(entry['name'],'')).strip() for entry in series if self._axis_slot(entry)==slot};units.discard('');label=Y_AXIS_LABELS[slot]+(' · '+next(iter(units)) if len(units)==1 else '');color=Y_AXIS_COLORS[slot];axis.set_ylabel(label,color=color,fontsize=9);axis.tick_params(axis='y',colors=color,labelsize=8);axis.yaxis.set_major_formatter(FuncFormatter(lambda value,pos:self._axis_tick(value)))
      side='left' if slot.startswith('L') else 'right';axis.spines[side].set_color(color);axis.spines[side].set_linewidth(1.1)
    self.ax.spines['right'].set_visible(False);self.ax.spines['top'].set_visible(False)
    if series and 'L1' not in self._used_axis_slots:self.ax.tick_params(axis='y',left=False,labelleft=False);self.ax.set_ylabel('');self.ax.spines['left'].set_visible(False)
 def _layout_y_axes(self):
    width=max(450,self.fig.bbox.width);left=(170 if 'L2' in self._used_axis_slots else 80)/width;right=1-(170 if 'R2' in self._used_axis_slots else 88 if 'R1' in self._used_axis_slots else 18)/width
    self.fig.subplots_adjust(left=min(.30,max(.09,left)),right=max(.65,min(.985,right)),top=.97,bottom=.12)
 def _on_graph_resize(self,event):
    if not hasattr(self,'_used_axis_slots'):return
    self._layout_y_axes();self._background=None;self._schedule_detail()
 def _axis_tick(self,value):
    text=f'{value:.6g}'
    return text.replace('.',',') if self.decimal.get()==',' else text
 def _graph_point(self,e,axis=None):return (axis or self.ax).transData.inverted().transform((e.x,e.y))
 def _in_graph(self,e):return e.x is not None and e.y is not None and self.ax.bbox.contains(e.x,e.y)
 def _axis_at_margin(self,e):
    if e.x is None or e.y is None or not self.ax.bbox.y0<=e.y<=self.ax.bbox.y1 or self._in_graph(e):return None
    candidates=[]
    for slot in self._used_axis_slots:
      pos=self.ax.bbox.x0 if slot.startswith('L') else self.ax.bbox.x1;pos+=(-1 if slot.startswith('L') else 1)*(68*self.fig.dpi/72 if slot in ('L2','R2') else 0);candidates.append((abs(e.x-pos),slot))
    return min(candidates)[1] if candidates and min(candidates)[0]<=70 else None
 def _display_indices(self,entry,bounds,budget):
    clock=entry['x'];count=len(clock);start=0;stop=count
    if bounds is not None and self.xcombo.get()=='Geçen süre':
      selection=visible_slice(clock,*sorted(bounds));start=selection.start;stop=selection.stop
    return envelope_indices(entry['dataset']['_base_channels'][entry['name']],start,stop,entry['dataset']['_envelopes'][entry['name']],budget)

 def redraw(self,preserve_view=False):
    if self._lod_after is not None:self.after_cancel(self._lod_after);self._lod_after=None
    view=(self.ax.get_xlim(),{slot:axis.get_ylim() for slot,axis in self._y_axes.items()}) if preserve_view else None
    for axis in list(self.fig.axes):
      if axis is not self.ax:axis.remove()
    self._background=None;self.ax.clear();self._guide_artists=[];self._line_data={};self._series_map={};self._legend_artist=None;self._legend_targets=[];self.ax.set_facecolor('#ffffff');self.ax.set_axisbelow(True);self.ax.tick_params(colors='#40596f')
    for spine in self.ax.spines.values():spine.set_color('#cbdbe7');spine.set_visible(True)
    self.ax.tick_params(axis='y',left=True,labelleft=True);series=self._plot_series();self._configure_y_axes(series);elapsed=self.xcombo.get()=='Geçen süre';budget=max(256,min(4000,60000//max(1,len(series))))
    if not series:
      self.ax.set_xlim(0,1);self.ax.set_ylim(0,1);self.ax.text(.5,.5,'Grafik için Dosya/Kanal sütununa sağ tıklayıp zaman çizelgesine ekleyin',color='#40596f',ha='center',va='center',transform=self.ax.transAxes);self.span_artist=None;self.cursor_x=None;self.cursor_y=None;self._reset_axis_slots.clear();self._draw_guides();self.canvas.draw_idle();self._update_tables();return
    track_colors={};previous_tracks={};legend_entries=[]
    for entry in series:
      track=entry['track'];first=track not in track_colors;track_colors.setdefault(track,PALETTE[len(track_colors)%len(PALETTE)]);color=track_colors[track];slot=self._axis_slot(entry);axis=self._y_axes[slot];entry['axis']=axis;entry['axis_slot']=slot
      key=entry['key'];x=entry['x'];y=entry['y'];indices=self._display_indices(entry,view[0] if view else None,budget);valid=np.isfinite(x[indices])&np.isfinite(y[indices]);indices=indices[valid];label=entry['track_label']+' ['+Y_AXIS_LABELS[slot]+']'
      line,=axis.plot(x[indices],y[indices],lw=1.15,color=color,label=label if first else '_nolegend_',picker=8,rasterized=True);self._line_data[line]=(key,x,y,indices);self._series_map[key]=entry
      if first:legend_entries.append((line,label,track))
      previous=previous_tracks.get(track)
      if previous is not None and previous['clip_index']==entry['clip_index']-1:
        px=previous['x'];py=previous['y'];rate=previous['dataset']['channel_rates'][previous['name']]
        if len(px) and len(x) and math.isclose(float(px[-1])+1/rate,entry['clip_start'],rel_tol=1e-10,abs_tol=1e-9) and np.isfinite(py[-1]) and np.isfinite(y[0]):axis.plot([px[-1],x[0]],[py[-1],y[0]],color=color,lw=1.15,label='_nolegend_')
      previous_tracks[track]=entry
      for probe_no,probe in enumerate(self.probes.get(key,[]),1):
        index=probe['index']
        if index>=len(x) or not np.isfinite(x[index]) or not np.isfinite(y[index]):continue
        axis.plot([x[index]],[y[index]],marker='o',ms=8,markerfacecolor='none',markeredgecolor=color,mew=1.5,zorder=9)
        if probe['label']:axis.annotate(f"P{probe_no}  X: {elapsed_text(x[index])}\nY: {self._number(y[index])}",(x[index],y[index]),xytext=(8,10),textcoords='offset points',color='#203449',fontsize=8,fontweight='bold',bbox=dict(boxstyle='round,pad=.3',facecolor='#eef5fa',edgecolor=color,alpha=.96),zorder=10)
    self.ax.set_xlabel('Geçen süre (HH:MM:SS.SSSS)' if elapsed else self.xcombo.get(),color='#526c82');self.ax.xaxis.set_major_formatter(FuncFormatter(lambda value,pos:elapsed_text(value) if elapsed else self._number(value)))
    self.span_artist=self.ax.axvspan(*self.span,color='#007f85',alpha=.16,zorder=0) if self.span else None;top_axis=list(self._y_axes.values())[-1];self._cursor_axis=top_axis
    legend=top_axis.legend([item[0] for item in legend_entries],[item[1] for item in legend_entries],loc='upper left',facecolor='#f4f8fb',edgecolor='#cbdbe7',labelcolor='#203449',fontsize=8,ncol=2);self._legend_artist=legend;legend.set_visible(self.legend_visible.get());self._legend_targets=[(artist,entry[2]) for artist,entry in zip(legend.get_texts(),legend_entries)]+[(artist,entry[2]) for artist,entry in zip(legend.legend_handles,legend_entries)]
    self.cursor_x=top_axis.axvline(0,color='#608ca1',lw=.8,ls='--',visible=False,animated=True);self.cursor_y=top_axis.axhline(0,color='#608ca1',lw=.8,ls='--',visible=False,animated=True)
    if self._timeline_active() and not view:self.ax.set_xlim(0,max(self._timeline_duration(),1e-9))
    if view:
      self.ax.set_xlim(*view[0])
      for slot,limits in view[1].items():
        if slot in self._y_axes and slot not in self._reset_axis_slots:self._y_axes[slot].set_ylim(*limits)
    self._reset_axis_slots.clear();self._draw_guides();self.ax.callbacks.connect('xlim_changed',lambda axis:self._schedule_detail());self.canvas.draw_idle();self._update_tables()
 def _toggle_legend(self):
    legend=self._legend_artist
    if legend is not None:legend.set_visible(self.legend_visible.get())
    self._background=None;self.canvas.draw_idle()
 def _schedule_detail(self):
    self._background=None
    if self._lod_after is None:self._lod_after=self.after(60,self._refresh_detail)
 def _refresh_detail(self):
    self._lod_after=None;bounds=self.ax.get_xlim();budget=max(256,min(4000,60000//max(1,len(self._line_data))))
    for line,(key,x,y,previous) in list(self._line_data.items()):
      entry=self._series_map[key];indices=self._display_indices(entry,bounds,budget);valid=np.isfinite(x[indices])&np.isfinite(y[indices]);indices=indices[valid]
      line.set_data(x[indices],y[indices]);self._line_data[line]=(key,x,y,indices)
    self._background=None;self.canvas.draw_idle()
 def _on_canvas_draw(self,event):
    if event.canvas is not self.canvas:return
    self._background=self.canvas.copy_from_bbox(self.ax.bbox)
    self._blit_cursor()
 def _blit_cursor(self):
    if self._background is None or getattr(self,'cursor_x',None) is None:return
    self.canvas.restore_region(self._background)
    for artist in (self.cursor_x,self.cursor_y):
      if artist.get_visible():artist.axes.draw_artist(artist)
    self.canvas.blit(self.ax.bbox)

 def on_motion(self,e):
    if not self._in_graph(e):
      if getattr(self,'cursor_x',None) is not None:self.cursor_x.set_visible(False);self.cursor_y.set_visible(False);self._blit_cursor()
      return
    now=time.perf_counter()
    if now-self._motion_clock<1/35:return
    self._motion_clock=now;xvalue,yvalue=self._graph_point(e);self.mouse_data=(xvalue,yvalue);values='  '.join(Y_AXIS_LABELS[slot]+' = '+self._number(self._graph_point(e,axis)[1]) for slot,axis in self._y_axes.items() if slot in self._used_axis_slots);self.coords.set('X = '+elapsed_text(xvalue)+'    '+values)
    if self.drag_mode in ('pan','axis_zoom') and self.drag_start:
      sx,sy,xlim,ylims=self.drag_start;dx=e.x-sx;dy=e.y-sy;bbox=self.ax.bbox
      if self.drag_mode=='pan':
        shift=-dx/bbox.width*(xlim[1]-xlim[0]);self.ax.set_xlim(xlim[0]+shift,xlim[1]+shift)
        for slot,limits in ylims.items():
          shift=-dy/bbox.height*(limits[1]-limits[0]);self._y_axes[slot].set_ylim(limits[0]+shift,limits[1]+shift)
      else:
        fx=math.exp(-dx/120);fy=math.exp(dy/120);center=sum(xlim)/2;self.ax.set_xlim(center+(xlim[0]-center)*fx,center+(xlim[1]-center)*fx)
        for slot,limits in ylims.items():
          center=sum(limits)/2;self._y_axes[slot].set_ylim(center+(limits[0]-center)*fy,center+(limits[1]-center)*fy)
      self._background=None;self.canvas.draw_idle()
    if getattr(self,'cursor_x',None) is not None:
      cy=self._graph_point(e,self._cursor_axis)[1];self.cursor_x.set_xdata([xvalue]*2);self.cursor_y.set_ydata([cy]*2);self.cursor_x.set_visible(True);self.cursor_y.set_visible(True)
      if self.drag_mode not in ('pan','axis_zoom'):self._blit_cursor()
 def on_scroll(self,e):
    step=getattr(e,'step',0)
    if not step:return
    factor=1/(1.2**step);slot=self._axis_at_margin(e)
    if slot:
      axis=self._y_axes[slot];center=self._graph_point(e,axis)[1];a,b=axis.get_ylim();axis.set_ylim(center+(a-center)*factor,center+(b-center)*factor);self._background=None;self.canvas.draw_idle()
    elif self._in_graph(e):
      x,y=self._graph_point(e);self._zoom_axes(factor,factor,x,y)
 def _zoom_axes(self,fx,fy,cx=None,cy=None):
    xa,xb=self.ax.get_xlim();ya,yb=self.ax.get_ylim();cx=(xa+xb)/2 if cx is None else cx;cy=(ya+yb)/2 if cy is None else cy;pixel=self.ax.transData.transform((cx,cy));self.ax.set_xlim(cx+(xa-cx)*fx,cx+(xb-cx)*fx)
    for axis in self._y_axes.values():
      a,b=axis.get_ylim();center=axis.transData.inverted().transform(pixel)[1];axis.set_ylim(center+(a-center)*fy,center+(b-center)*fy)
    self._background=None;self.canvas.draw_idle()
 def on_span(self,xmin,xmax):
    if abs(xmax-xmin)<=max(abs(xmin),abs(xmax),1)*1e-12:return
    self._span_generation+=1;self.span=(min(xmin,xmax),max(xmin,xmax))
    if getattr(self,'span_artist',None):self.span_artist.remove()
    self.span_artist=self.ax.axvspan(self.span[0],self.span[1],color='#007f85',alpha=.16,zorder=0);self.status.set(f'Seçili aralık: {self._number(self.span[0])} — {self._number(self.span[1])}');self.canvas.draw_idle()
 def on_press(self,e):
    if e.button==1 and self._legend_artist is not None and self._legend_artist.get_visible():
      for artist,track in self._legend_targets:
        if artist.contains(e)[0]:
          self.click_start=None;self._graph_button=None;widget=self.canvas.get_tk_widget();self._axis_menu([track],widget.winfo_rootx()+e.x,widget.winfo_rooty()+widget.winfo_height()-e.y);return
    if not self._in_graph(e):return
    x,y=self._graph_point(e);ylims={slot:axis.get_ylim() for slot,axis in self._y_axes.items()}
    if e.button in (1,3):
      mode='span' if e.button==1 or (e.key and 'shift' in str(e.key).lower()) else 'pan';self._graph_button=e.button;self.drag_mode=mode;self.drag_start=(e.x,e.y,self.ax.get_xlim(),ylims);self.click_start=(e.x,e.y,self._span_generation,mode,x,y)
    elif e.button==2:self._graph_button=2;self.drag_mode='axis_zoom';self.drag_start=(e.x,e.y,self.ax.get_xlim(),ylims)
 def on_release(self,e):
    if e.button in (1,3) and self.click_start and self._graph_button==e.button:
      start=self.click_start;self.click_start=None;self.drag_mode=None;self.drag_start=None;self._graph_button=None;dx=abs(e.x-start[0]);dy=abs(e.y-start[1]);inside=self._in_graph(e)
      if start[3]=='span' and inside and dx>=5:self.on_span(start[4],self._graph_point(e)[0])
      elif dx<5 and dy<5 and inside:
        if e.button==1:self.after_idle(lambda:self._finish_click(e,start[2]))
        else:
          hit=self._nearest_probe(e)
          if hit:
            name,index=hit;probe=self.probes[name][index];probe['label']=not probe['label'];self.status.set(f'{self._key_label(name)} P{index+1} etiketi '+('gösteriliyor' if probe['label'] else 'gizlendi'));self.redraw(preserve_view=True)
    elif e.button==2 and self._graph_button==2:self._graph_button=None;self.drag_mode=None;self.drag_start=None
 def _finish_click(self,e,generation):
    if generation!=self._span_generation or not self._in_graph(e) or not getattr(self,'_line_data',None):return
    hit=self._nearest_probe(e)
    if hit:
      n,j=hit;self.probes[n].pop(j)
      if not self.probes[n]:self.probes.pop(n)
      self.status.set(f'{self._key_label(n)} P{j+1} probe kaldırıldı');self.redraw(preserve_view=True);return
    best=None
    for line,(name,x,y,sample_indices) in self._line_data.items():
      contains,ind=line.contains(e)
      if contains and ind.get('ind') is not None:
        positions=np.asarray(ind['ind'],dtype=int);positions=positions[(positions>=0)&(positions<len(sample_indices))]
        if not len(positions):continue
        indices=sample_indices[positions];pixels=line.axes.transData.transform(np.column_stack((x[indices],y[indices])));distances=np.hypot(pixels[:,0]-e.x,pixels[:,1]-e.y);nearest=int(np.argmin(distances));dist=float(distances[nearest]);idx=int(indices[nearest])
        if best is None or dist<best[0]:best=(dist,name,idx)
    if best:
      n=best[1];items=self.probes.setdefault(n,[])
      if len(items)>=5:self.status.set(f'{self._key_label(n)} için en fazla 5 probe eklenebilir.');return
      items.append({'index':best[2],'label':True});self.status.set(f'{self._key_label(n)} kanalına P{len(items)} probe eklendi');self.redraw(preserve_view=True);return
    if self.span is not None:self.clear_span()
 def _nearest_probe(self,e,threshold=13):
    if not self._in_graph(e):return None
    nearest=None;distance=threshold
    for n,items in self.probes.items():
      entry=next((entry for entry in getattr(self,'_line_data',{}).values() if entry[0]==n),None)
      if entry is None:continue
      x,y=entry[1],entry[2]
      for j,p in enumerate(items):
        i=p['index'];axis=self._series_map[n]['axis'];px,py=axis.transData.transform((x[i],y[i]));dist=((px-e.x)**2+(py-e.y)**2)**.5
        if dist<distance:nearest=(n,j);distance=dist
    return nearest
 def _draw_guides(self):
    if self._guide_artists:return
    positions=np.linspace(0,1,120)
    for kind,color,alpha,width,style in [(0,'#8eacbf',.32,.8,'-'),(1,'#afc6d6',.23,.6,'-'),(2,'#c2d3df',.16,.35,':')]:
      values=[value for i,value in enumerate(positions) if (0 if i%10==0 else (1 if i%5==0 else 2))==kind]
      segments=[[(value,0),(value,1)] for value in values]+[[(0,value),(1,value)] for value in values]
      artist=LineCollection(segments,colors=color,alpha=alpha,linewidths=width,linestyles=style,transform=self.ax.transAxes,zorder=.15);self.ax.add_collection(artist,autolim=False);self._guide_artists.append(artist)

 def reset_zoom(self):
    if self.datasets:self.redraw()
 def _update_tables(self):
    for item in self.table.get_children():self.table.delete(item)
    for item in self.probe_table.get_children():self.probe_table.delete(item)
    for entry in self._series_map.values():
      d=entry['dataset'];name=entry['name'];y=entry['y'];x=entry['x'];key=entry['key'];first,last,low,high=d['_base_stats'][name]
      if first is not None:
        factor=float(d.get('multipliers',{}).get(name,1))*float(d.get('data_multiplier',1));minimum,maximum=sorted((low*factor,high*factor))
        self.table.insert('','end',values=(entry['label'],self._fmt(first*factor),self._fmt(last*factor),self._fmt(minimum),self._fmt(maximum)))
      for j,probe in enumerate(self.probes.get(key,[]),1):
        i=probe['index']
        if i>=len(x):continue
        xvalue=elapsed_text(x[i]) if self.xcombo.get()=='Geçen süre' and np.isfinite(x[i]) else self._fmt(x[i]);self.probe_table.insert('','end',values=(entry['label'],f'P{j}',xvalue,self._fmt(y[i])))

 def _number(self,x):
    if not np.isfinite(x):return '—'
    value=f'{x:.10g}'
    return value.replace('.',',') if hasattr(self,'decimal') and self.decimal.get()==',' else value
 def _fmt(self,x):return self._number(x)
 def clear_probes(self):self.probes.clear();self.redraw()
 def clear_span(self):
    if self.span is None:return
    self.span=None
    if getattr(self,'span_artist',None):
      try:self.span_artist.remove()
      except ValueError:pass
      self.span_artist=None
    self.status.set('Seçili grafik aralığı temizlendi');self.canvas.draw_idle()
 def sort_tree(self,tree,col):
    key=(str(tree),col);reverse=self.sort_state.get(key,False);self.sort_state[key]=not reverse
    def value(item):
      raw=str(tree.set(item,col)).strip()
      try:return (0,float(raw.replace(',','.')))
      except ValueError:
        try:return (0,datetime.fromisoformat(raw).timestamp())
        except ValueError:return (1,raw.casefold())
    items=list(tree.get_children(''));items.sort(key=value,reverse=reverse)
    for index,item in enumerate(items):tree.move(item,'',index)
 def _csv_options(self,title,initial):
    return filedialog.asksaveasfilename(title=title,defaultextension='.csv',initialfile=initial,filetypes=[('CSV dosyası','*.csv')])
 def export_graph_csv(self):
    if self._job is not None:return
    series=self._export_series()
    if not series:messagebox.showinfo('CSV dışa aktar','Önce grafikte gösterilecek kanalları seçin.',parent=self);return
    lo,hi=sorted(self.span if self.span else self.ax.get_xlim());path=self._csv_options('Grafikte görünen verileri CSV olarak kaydet','tracedock-grafik.csv')
    if not path:return
    decimal=self.decimal.get();elapsed=self.xcombo.get()=='Geçen süre'
    def work(progress,cancel):return write_series_csv(path,series,lo,hi,decimal,elapsed,progress,cancel)
    self._start_job('CSV dışa aktarılıyor',work,lambda count:self.status.set(f'{count:,} satır dışa aktarıldı • {len(series)} kanal • {Path(path).name}'))

 def export_graph_png(self):
    if not self._plot_series():
      messagebox.showinfo('PNG dışa aktar','Önce bir veri dosyası ve grafikte gösterilecek kanal seçin.');return
    p=filedialog.asksaveasfilename(title='Grafik görüntüsünü PNG olarak kaydet',defaultextension='.png',initialfile='tracedock-grafik.png',filetypes=[('PNG görüntüsü','*.png')])
    if not p:return
    cursor_visibility=[]
    for name in ('cursor_x','cursor_y'):
      artist=getattr(self,name,None)
      if artist is not None:
        cursor_visibility.append((artist,artist.get_visible()))
        artist.set_visible(False)
    try:
      self.fig.savefig(p,format='png',dpi=200,facecolor=self.fig.get_facecolor(),bbox_inches='tight')
      self.status.set(f'Grafik PNG olarak kaydedildi • {Path(p).name}')
    except Exception as exc:messagebox.showerror('PNG dışa aktarılamadı',str(exc))
    finally:
      for artist,visible in cursor_visibility:artist.set_visible(visible)
      self.canvas.draw_idle()
 def export_span_csv(self):
    if self.span is None:
      messagebox.showinfo('CSV dışa aktar','Önce grafikte sol tuşla sürükleyerek bir aralık seçin.');return
    self.export_graph_csv()
 def export_stats_csv(self):
    items=self.table.get_children()
    if not items:messagebox.showinfo('CSV dışa aktar','Dışa aktarılacak kanal istatistiği bulunmuyor.');return
    p=self._csv_options('Kanal istatistiklerini CSV olarak kaydet','tracedock-istatistikler.csv')
    if not p:return
    delimiter=';' if self.decimal.get()==',' else ',';headers=['Kanal','Başlangıç','Bitiş','Minimum','Maksimum']
    try:
      with open(p,'w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,delimiter=delimiter);writer.writerow(headers)
        for item in items:writer.writerow(self.table.item(item,'values'))
      self.status.set(f'{len(items)} kanal istatistiği dışa aktarıldı • {Path(p).name}')
    except Exception as exc:messagebox.showerror('CSV dışa aktarılamadı',str(exc))
 def save_config(self):
    payload={'format':'TraceDock-config-v2','view':{'legend_visible':self.legend_visible.get()}}
    path=filedialog.asksaveasfilename(title='Görünüm ayarlarını kaydet',defaultextension='.json',initialfile='tracedock-config.json',filetypes=[('JSON ayarları','*.json')])
    if not path:return
    try:
      Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');CONFIG_PATH.parent.mkdir(parents=True,exist_ok=True);CONFIG_PATH.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');self.status.set(f'Ayarlar kaydedildi: {Path(path).name}')
    except Exception as exc:messagebox.showerror('Ayarlar kaydedilemedi',str(exc),parent=self)
 def load_config_dialog(self):
    path=filedialog.askopenfilename(title='Görünüm ayarlarını yükle',filetypes=[('JSON ayarları','*.json'),('Tüm dosyalar','*.*')])
    if not path:return
    try:
      payload=json.loads(Path(path).read_text(encoding='utf-8-sig'));self.legend_visible.set(bool(payload.get('view',{}).get('legend_visible',self.legend_visible.get())));self._toggle_legend();self.status.set(f'Ayarlar yüklendi: {Path(path).name}')
    except Exception as exc:messagebox.showerror('Ayarlar yüklenemedi',str(exc),parent=self)
 def load_default_config(self):
    try:
      source=CONFIG_PATH if CONFIG_PATH.exists() else LEGACY_CONFIG_PATH
      if source.exists():self.legend_visible.set(bool(json.loads(source.read_text(encoding='utf-8-sig')).get('view',{}).get('legend_visible',True)))
    except (OSError,ValueError,AttributeError,TypeError):pass

def verify_runtime_workers(report_path,input_path):
    size=os.path.getsize(input_path);plan=resource_plan(size)
    if size<32*2**20:plan.update(workers=min(4,plan['workers']),chunk_bytes=256*1024)
    started=time.perf_counter()
    with new_process_pool(plan) as pool:
        d=parse_text_file(input_path,kind='strain',pool=pool,plan=plan)
        chunks=[(np.array([0.,.01,.02]),np.array([1.25,2.5,3.75]))]
        futures=[pool.submit(format_export_block,chunks,True,',',True) for i in range(8)]
        for future in futures:
            text=future.result()
            if '00:00:00.0100;2,5' not in text:raise AssertionError('Parallel export mismatch')
        spawned=len(pool._processes)
    parallel_seconds=time.perf_counter()-started
    if not len(d['channels']) or len(d['x'])==0 or d.get('timing_warning'):raise AssertionError('Strain file did not load correctly')
    if spawned<2 or os.getpid() in d['reader_pids']:raise AssertionError('Child processes were not used')
    started=time.perf_counter();serial=parse_text_file(input_path,kind='strain');serial_seconds=time.perf_counter()-started
    for name in d['channels']:
        if not np.array_equal(d['channels'][name],serial['channels'][name],equal_nan=True):raise AssertionError('Parallel reader differs from serial reader')
    report={'status':'PASS','rows':len(d['x']),'channels':len(d['channels']),'spawned_processes':spawned,'active_reader_processes':d['reader_workers'],'reader_process_ids':d['reader_pids'],'parallel_export':True,'logical_cpus':plan['cpus'],'parallel_seconds':round(parallel_seconds,3),'serial_seconds':round(serial_seconds,3)}
    Path(report_path).write_text(json.dumps(report,indent=2),encoding='utf-8')

if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--verify-workers':
  try:verify_runtime_workers(sys.argv[2],sys.argv[3])
  except Exception:
   Path(sys.argv[2]).write_text(json.dumps({'status':'FAIL','error':traceback.format_exc()}),encoding='utf-8');sys.exit(1)
  sys.exit(0)
 try:TraceDock().mainloop()
 except Exception as exc:
  try:messagebox.showerror('TraceDock hata',str(exc)+'\n\n'+traceback.format_exc())
  except Exception:pass


