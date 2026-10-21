"""Responsive panels and tables with content-sized, scrollable columns."""
import tkinter as tk
from tkinter import ttk, font as tkfont


class AutoScrollbar(ttk.Scrollbar):
    def set(self, first, last):
        if float(first) <= 0 and float(last) >= 1:
            self.grid_remove()
        else:
            self.grid()
        super().set(first, last)


class AdaptiveTreeview(ttk.Treeview):
    """Measure cell contents once per update; resizing only redistributes space."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fit_pending = None
        self._content_dirty = True
        self._natural_widths = {}
        self._font = tkfont.nametofont('TkDefaultFont').copy()
        self._bold_font = self._font.copy()
        self._bold_font.configure(weight='bold')
        self.bind('<Configure>', lambda event: self._schedule_fit(), add='+')
        self.bind('<Shift-MouseWheel>', self._horizontal_wheel, add='+')
        self.bind('<Destroy>', self._destroy_fit, add='+')
        self._schedule_fit()

    def _destroy_fit(self, event):
        if event.widget is self and self._fit_pending is not None:
            self.after_cancel(self._fit_pending)
            self._fit_pending = None

    def _horizontal_wheel(self, event):
        if event.delta:
            self.xview_scroll(-max(1, abs(event.delta)//120) if event.delta > 0 else max(1, abs(event.delta)//120), 'units')
        return 'break'

    def _schedule_fit(self, dirty=False):
        self._content_dirty |= dirty
        if self._fit_pending is None:
            self._fit_pending = self.after_idle(self._fit_columns)

    def insert(self, *args, **kwargs):
        result = super().insert(*args, **kwargs)
        self._schedule_fit(True)
        return result

    def delete(self, *args):
        result = super().delete(*args)
        self._schedule_fit(True)
        return result

    def item(self, item, option=None, **kwargs):
        result = super().item(item, option, **kwargs)
        if kwargs:
            self._schedule_fit(True)
        return result

    def _fit_columns(self):
        self._fit_pending = None
        if not self.winfo_exists():
            return
        columns = list(self['columns'])
        if 'tree' in tuple(map(str, self.tk.splitlist(self.cget('show')))):
            columns.insert(0, '#0')
        if self._content_dirty:
            widths = {col: max(60, self._bold_font.measure(self.heading(col, 'text')) + 28) for col in columns}
            pending = [(item, 0) for item in self.get_children()]
            measured = {}
            def measure(value, bold=False):
                key = (str(value), bold)
                if key not in measured:
                    font = self._bold_font if bold else self._font
                    measured[key] = max((font.measure(line) for line in str(value).splitlines()), default=0)
                return measured[key]
            while pending:
                item, depth = pending.pop()
                data = super().item(item)
                if '#0' in widths:
                    widths['#0'] = max(widths['#0'], measure(data['text'], True) + 52 + depth*20)
                for col, value in zip(self['columns'], data['values']):
                    widths[col] = max(widths[col], measure(value) + 28)
                pending.extend((child, depth+1) for child in self.get_children(item))
            self._natural_widths = widths
            self._content_dirty = False
        widths = dict(self._natural_widths)
        if not widths:
            return
        extra = max(0, self.winfo_width()-4-sum(widths.values()))
        widths[columns[0]] += extra
        for col, width in widths.items():
            if self.column(col, 'width') != width or self.column(col, 'stretch'):
                self.column(col, width=width, minwidth=width, stretch=False)


class ResponsivePanedWindow(tk.PanedWindow):
    def __init__(self, *args, fraction=.7, **kwargs):
        super().__init__(*args, **kwargs)
        self.fraction = fraction
        self._resize_pending = None
        self.bind('<Configure>', self._schedule, add='+')
        self.bind('<ButtonRelease-1>', self._remember_split, add='+')
        self.bind('<Destroy>', self._destroy_resize, add='+')

    def _destroy_resize(self, event):
        if event.widget is self and self._resize_pending is not None:
            self.after_cancel(self._resize_pending)
            self._resize_pending = None

    def _remember_split(self, event):
        if len(self.panes()) != 2:
            return
        vertical = str(self.cget('orient')) == 'vertical'
        size = self.winfo_height() if vertical else self.winfo_width()
        self.fraction = self.sash_coord(0)[1 if vertical else 0]/max(1, size)

    def _schedule(self, event=None):
        if self._resize_pending is None:
            self._resize_pending = self.after_idle(self.resize_panes)

    def resize_panes(self):
        self._resize_pending = None
        panes = self.panes()
        if len(panes) != 2:
            return
        vertical = str(self.cget('orient')) == 'vertical'
        size = self.winfo_height() if vertical else self.winfo_width()
        first = int(self.panecget(panes[0], 'minsize'))
        second = int(self.panecget(panes[1], 'minsize'))
        position = max(first, min(size-second-int(self.cget('sashwidth')), round(size*self.fraction)))
        self.sash_place(0, 0 if vertical else position, position if vertical else 0)


class HorizontalScrollFrame(tk.Frame):
    """Let control rows fill their panel, with horizontal scrolling if necessary."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, bg=self.cget('bg'), highlightthickness=0, height=1)
        self.canvas.grid(row=0, column=0, sticky='ew')
        self.scroll = AutoScrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.scroll.grid(row=1, column=0, sticky='ew')
        self.canvas.configure(xscrollcommand=self.scroll.set)
        self.content = tk.Frame(self.canvas, bg=self.cget('bg'))
        self.window = self.canvas.create_window((0, 0), window=self.content, anchor='nw')
        self._pending = None
        self.content.bind('<Configure>', self._schedule)
        self.canvas.bind('<Configure>', self._schedule)
        self.bind('<Destroy>', self._destroy_layout, add='+')

    def _destroy_layout(self, event):
        if event.widget is self and self._pending is not None:
            self.after_cancel(self._pending)
            self._pending = None

    def _schedule(self, event=None):
        if self._pending is None:
            self._pending = self.after_idle(self._layout)

    def _layout(self):
        self._pending = None
        width = max(self.canvas.winfo_width(), self.content.winfo_reqwidth())
        height = self.content.winfo_reqheight()
        self.canvas.configure(height=height, scrollregion=(0, 0, width, height))
        self.canvas.itemconfigure(self.window, width=width, height=height)


def size_dialog(window, parent, width, height):
    """Choose an initial dialog size from its parent and available screen space."""
    max_width = max(320, window.winfo_screenwidth()-60)
    max_height = max(240, window.winfo_screenheight()-100)
    width = min(width, max_width, max(420, int(parent.winfo_width()*.9)))
    height = min(height, max_height, max(300, int(parent.winfo_height()*.85)))
    x = max(0, min(max_width-width, parent.winfo_rootx()+(parent.winfo_width()-width)//2))
    y = max(0, min(max_height-height, parent.winfo_rooty()+(parent.winfo_height()-height)//2))
    window.geometry(f'{width}x{height}+{x}+{y}')
    window.minsize(min(420, width), min(300, height))
    window.resizable(True, True)
