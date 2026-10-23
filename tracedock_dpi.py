"""Native Windows rendering without bitmap virtualization between monitors."""
import ctypes
import sys


def set_windows_app_id():
    """Group the frozen application under its own identity, including taskbar icons."""
    if sys.platform == 'win32':
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('boanx.TraceDock.Desktop')
        except (OSError, AttributeError):
            pass


def enable_dpi_awareness():
    # Run before Tk creates any HWND. Frozen builds also need the manifest:
    # Windows can reject changing a process mode already set by its manifest.
    if sys.platform != 'win32':
        return
    try:
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        set_context = user32.SetProcessDpiAwarenessContext
        set_context.argtypes = [ctypes.c_void_p]
        set_context.restype = ctypes.c_bool
        if set_context(ctypes.c_void_p(-4)):
            return
        if ctypes.get_last_error() == 5:  # Manifest already selected the mode.
            return
    except (OSError, AttributeError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (OSError, AttributeError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (OSError, AttributeError):
            pass


def window_dpi(root):
    if sys.platform != 'win32':
        return 96
    try:
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.GetParent.argtypes = [ctypes.c_void_p]
        user32.GetParent.restype = ctypes.c_void_p
        user32.GetDpiForWindow.argtypes = [ctypes.c_void_p]
        user32.GetDpiForWindow.restype = ctypes.c_uint
        return user32.GetDpiForWindow(user32.GetParent(root.winfo_id()) or root.winfo_id()) or 96
    except (OSError, AttributeError):
        return 96


class DisplayFonts:
    """Keep original point sizes and explicitly render every Tk font in pixels.

    Anonymous Tk fonts can retain the old monitor's metrics after tk scaling
    changes. Widgets, ttk styles and Canvas text must share named fonts instead.
    """
    def __init__(self, root):
        from tkinter import font
        self.root = root
        self.dpi = window_dpi(root)
        self.points = {}
        self.cache = {}
        self.owned = []
        root.tk.call('tk', 'scaling', self.dpi/72.0)
        self.refresh_named_fonts()

    def refresh_named_fonts(self):
        from tkinter import font
        changed = False
        for name in font.names(self.root):
            current = font.nametofont(name, root=self.root)
            if name not in self.points:
                size = int(current.cget('size'))
                self.points[name] = size if size > 0 else abs(size)*72/self.dpi
                changed = True
            pixels = -max(1, round(self.points[name]*self.dpi/72))
            if int(current.cget('size')) != pixels:
                current.configure(size=pixels)
        return changed

    def get(self, spec):
        from tkinter import font
        if str(spec) in self.points:
            return font.nametofont(str(spec), root=self.root)
        key = str(spec)
        if key not in self.cache:
            current = font.Font(root=self.root, font=spec)
            size = int(current.cget('size'))
            self.points[current.name] = size if size > 0 else abs(size)*72/self.dpi
            current.configure(size=-max(1, round(self.points[current.name]*self.dpi/72)))
            self.cache[key] = current
            self.owned.append(current)
        return self.cache[key]

    def normalize_widgets(self):
        import tkinter as tk
        changed = self.refresh_named_fonts()
        pending = [self.root]
        while pending:
            widget = pending.pop()
            pending.extend(widget.winfo_children())
            if 'font' in widget.keys():
                original = widget.cget('font')
                if original:
                    managed = self.get(original)
                    if str(original) != managed.name:
                        widget.configure(font=managed)
                        changed = True
        return changed

    def change_dpi(self, dpi):
        # Discover newly created fonts using the previous monitor's scale first.
        self.normalize_widgets()
        self.dpi = dpi
        self.root.tk.call('tk', 'scaling', dpi/72.0)
        self.refresh_named_fonts()


def display_fonts(root):
    root = root._root()
    if not hasattr(root, '_display_fonts'):
        root._display_fonts = DisplayFonts(root)
    return root._display_fonts


def ui_font(root, size=9, weight='normal'):
    return display_fonts(root).get(('Segoe UI', size, weight))


def watch_window_dpi(root):
    import tkinter as tk
    book = display_fonts(root)
    timer = None
    first = True

    def poll():
        nonlocal timer, first
        timer = None
        try:
            dpi = window_dpi(root)
            changed = first or dpi != book.dpi
            if changed:
                book.change_dpi(dpi)
            changed = book.normalize_widgets() or changed
            if changed:
                pending = [root]
                while pending:
                    widget = pending.pop()
                    widget.event_generate('<<DisplayScaleChanged>>', when='tail')
                    pending.extend(widget.winfo_children())
            first = False
            timer = root.after(350, poll)
        except tk.TclError:
            return

    def stop(event):
        nonlocal timer
        if event.widget is root and timer is not None:
            root.after_cancel(timer)
            timer = None

    root.bind('<Destroy>', stop, add='+')
    root.after_idle(poll)
