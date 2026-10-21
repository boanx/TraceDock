"""TraceDock's light glass controls and Windows window decoration."""
import ctypes
import math
import sys
import tkinter as tk
from tkinter import ttk, font as tkfont, messagebox as native_messages, simpledialog as native_inputs
from tracedock_layout import size_dialog

BG='#e8eff5'
SURFACE='#f4f8fb'
FIELD='#ffffff'
TEXT='#203449'
MUTED='#60758a'
BORDER='#cbdbe7'
ACCENT='#007f85'
SELECT='#d7efee'


def rounded_rect(canvas,x1,y1,x2,y2,r=12,**options):
    r=max(0,min(r,(x2-x1)/2,(y2-y1)/2))
    return canvas.create_polygon(x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1,smooth=True,splinesteps=24,**options)


def apply_native_glass(window):
    """Request supported Windows decorations; keep a regular window on older systems."""
    if sys.platform!='win32':return
    try:
        window.update_idletasks()
        user32=ctypes.windll.user32
        user32.GetParent.argtypes=[ctypes.c_void_p];user32.GetParent.restype=ctypes.c_void_p
        hwnd=user32.GetParent(window.winfo_id()) or window.winfo_id()
        dwm=ctypes.windll.dwmapi
        dwm.DwmSetWindowAttribute.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint]
        # Rounded corners, light caption, and the OS-managed translucent backdrop.
        for attribute,value in ((20,0),(33,2),(35,0xF5EFE8),(36,0x493420),(38,3)):
            setting=ctypes.c_int(value);dwm.DwmSetWindowAttribute(hwnd,attribute,ctypes.byref(setting),ctypes.sizeof(setting))
    except (OSError,AttributeError,tk.TclError):pass


class GlassButton(tk.Canvas):
    def __init__(self,parent,text,command,**kwargs):
        self._text=text;self._command=command;self._enabled=True;self._hover=False;self._pressed=False;self._pad_y=7
        self._font=tkfont.Font(root=parent,family='Segoe UI',size=9)
        super().__init__(parent,bg=parent.cget('background'),highlightthickness=0,bd=0,takefocus=True,cursor='hand2',**kwargs)
        self._size()
        self.bind('<Configure>',lambda e:self._paint());self.bind('<Enter>',lambda e:self._state(hover=True));self.bind('<Leave>',lambda e:self._state(hover=False,pressed=False))
        self.bind('<ButtonPress-1>',self._press);self.bind('<ButtonRelease-1>',self._release)
        self.bind('<Return>',lambda e:(self.invoke(),'break')[1]);self.bind('<space>',lambda e:(self.invoke(),'break')[1]);self.bind('<FocusIn>',lambda e:self._paint());self.bind('<FocusOut>',lambda e:self._paint())
    def _size(self):
        super().configure(width=self._font.measure(self._text)+24,height=self._font.metrics('linespace')+2*self._pad_y+4)
    def configure(self,cnf=None,**kwargs):
        if cnf is not None:
            if not isinstance(cnf,dict):return super().configure(cnf,**kwargs)
            kwargs={**cnf,**kwargs}
        resize=False
        if 'text' in kwargs:self._text=kwargs.pop('text');resize=True
        if 'command' in kwargs:self._command=kwargs.pop('command')
        if 'state' in kwargs:self._enabled=kwargs.pop('state')!='disabled'
        if 'pady' in kwargs:self._pad_y=int(kwargs.pop('pady'));resize=True
        kwargs.pop('padx',None)
        result=super().configure(**kwargs) if kwargs else None
        if resize:self._size()
        self._paint();return result
    config=configure
    def _state(self,hover=None,pressed=None):
        if hover is not None:self._hover=hover
        if pressed is not None:self._pressed=pressed
        self._paint()
    def _press(self,event):
        if self._enabled:self.focus_set();self._state(pressed=True)
    def _release(self,event):
        invoke=self._enabled and self._pressed and 0<=event.x<self.winfo_width() and 0<=event.y<self.winfo_height();self._state(pressed=False)
        if invoke:self.invoke()
    def invoke(self):
        if self._enabled and self._command:return self._command()
    def _paint(self):
        if not self.winfo_exists():return
        self.delete('all');w=max(4,self.winfo_width());h=max(4,self.winfo_height());radius=min(14,(h-4)/2)
        rounded_rect(self,1,3,w-1,h-1,r=radius,fill='#dce6ee',outline='')
        top=(248,255,255) if self._hover else (255,255,255);bottom=(210,237,239) if self._pressed else (225,241,245) if self._hover else (233,241,247)
        for y in range(1,max(2,h-3)):
            fraction=(y-1)/max(1,h-5);color='#'+''.join(f'{round(a+(b-a)*fraction):02x}' for a,b in zip(top,bottom));inset=0.
            if y<radius+1:inset=radius-math.sqrt(max(0,radius**2-(radius+1-y)**2))
            elif y>h-3-radius:inset=radius-math.sqrt(max(0,radius**2-(y-(h-3-radius))**2))
            self.create_line(1+inset,y,w-2-inset,y,fill=color)
        focused=self.focus_get()==self
        rounded_rect(self,1,1,w-2,h-3,r=radius,fill='',outline=ACCENT if focused or self._hover else BORDER,width=1)
        self.create_line(radius+2,2,w-radius-3,2,fill='#ffffff')
        self.create_text(w/2,(h-3)/2,text=self._text,font=self._font,fill=TEXT if self._enabled else '#96a6b4')


def glass_dialog(title,message,parent=None,initialvalue=None,input_mode=False,question=False):
    parent=parent or tk._default_root
    if parent is None:
        if input_mode:return native_inputs.askstring(title,message,initialvalue=initialvalue)
        return native_messages.askyesno(title,message) if question else native_messages.showinfo(title,message)
    win=tk.Toplevel(parent);win.withdraw();win.title(title);win.configure(bg=BG);win.transient(parent.winfo_toplevel());win.resizable(True,True)
    icon=getattr(sys,'_MEIPASS',None)
    if icon:
        try:win.iconbitmap(icon+'/tracedock.ico')
        except tk.TclError:pass
    result={'value':False if question else None}
    card=tk.Frame(win,bg=SURFACE,highlightbackground='#ffffff',highlightthickness=1);card.pack(fill='both',expand=True,padx=14,pady=14)
    tk.Label(card,text=title,font=('Segoe UI',13,'bold'),fg=TEXT,bg=SURFACE,anchor='w').pack(fill='x',padx=18,pady=(16,9))
    if len(str(message))>1000:
        area=tk.Frame(card,bg=SURFACE);area.pack(fill='both',expand=True,padx=18,pady=(0,12));text=tk.Text(area,height=12,width=64,wrap='word',bg=FIELD,fg=TEXT,relief='flat',font=('Segoe UI',10));scroll=ttk.Scrollbar(area,command=text.yview);scroll.pack(side='right',fill='y');text.pack(fill='both',expand=True);text.configure(yscrollcommand=scroll.set);text.insert('1.0',str(message));text.configure(state='disabled')
    else:
        label=tk.Label(card,text=str(message),wraplength=460,justify='left',fg=MUTED,bg=SURFACE,font=('Segoe UI',10));label.pack(fill='x',padx=18,pady=(0,12));label.bind('<Configure>',lambda event:label.configure(wraplength=max(100,event.width-4)))
    entry=None
    if input_mode:
        entry=ttk.Entry(card,width=52);entry.pack(fill='x',padx=18,pady=(0,14));entry.insert(0,'' if initialvalue is None else str(initialvalue));entry.select_range(0,tk.END)
    buttons=tk.Frame(card,bg=SURFACE);buttons.pack(fill='x',padx=18,pady=(0,16))
    def finish(accepted):
        result['value']=entry.get() if input_mode and accepted else None if input_mode else bool(accepted) if question else 'ok';win.destroy()
    if input_mode or question:GlassButton(buttons,'Vazgeç' if input_mode else 'Hayır',lambda:finish(False)).pack(side='right',padx=(7,0))
    ok=GlassButton(buttons,'Evet' if question else 'Tamam',lambda:finish(True));ok.pack(side='right')
    win.protocol('WM_DELETE_WINDOW',lambda:finish(False));win.bind('<Escape>',lambda e:finish(False));win.bind('<Return>',lambda e:finish(True));win.update_idletasks()
    size_dialog(win,parent,win.winfo_reqwidth(),win.winfo_reqheight());win.deiconify();apply_native_glass(win);win.grab_set()
    (entry or ok).focus_set()
    try:parent.wait_window(win)
    finally:
        # Restore the grab when a validation message was opened from another modal.
        if isinstance(parent,tk.Toplevel) and parent.winfo_exists():parent.grab_set()
    return result['value']


class GlassMessages:
    @staticmethod
    def showinfo(title,message,**kwargs):return glass_dialog(title,message,parent=kwargs.get('parent'))
    showwarning=showinfo
    showerror=showinfo
    @staticmethod
    def askyesno(title,message,**kwargs):return glass_dialog(title,message,parent=kwargs.get('parent'),question=True)


class GlassInputs:
    @staticmethod
    def askstring(title,prompt,initialvalue=None,**kwargs):return glass_dialog(title,prompt,parent=kwargs.get('parent'),initialvalue=initialvalue,input_mode=True)
