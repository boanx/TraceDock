"""Native Windows rendering without bitmap virtualization between monitors."""
import ctypes
import sys


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


def watch_window_dpi(root):
    """Rescale Tk fonts/custom controls when this window changes monitors.

    TkAgg handles its own device pixel ratio; never multiply figure DPI here.
    """
    if sys.platform != 'win32':
        return
    import tkinter as tk
    from tkinter import font as tkfont
    try:
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        get_dpi = user32.GetDpiForWindow
        get_dpi.argtypes = [ctypes.c_void_p]
        get_dpi.restype = ctypes.c_uint
        get_parent = user32.GetParent
        get_parent.argtypes = [ctypes.c_void_p]
        get_parent.restype = ctypes.c_void_p
    except (OSError, AttributeError):
        return
    last_dpi = None
    timer = None

    def poll():
        nonlocal last_dpi, timer
        timer = None
        try:
            hwnd = get_parent(root.winfo_id()) or root.winfo_id()
            dpi = get_dpi(hwnd)
            if dpi and dpi != last_dpi:
                last_dpi = dpi
                root.tk.call('tk', 'scaling', dpi / 72.0)
                # Refresh cached named fonts, including GlassButton's fonts.
                for name in tkfont.names(root):
                    font = tkfont.nametofont(name, root=root)
                    font.configure(size=font.cget('size'))
                pending = [root]
                while pending:
                    widget = pending.pop()
                    widget.event_generate('<<DisplayScaleChanged>>', when='tail')
                    pending.extend(widget.winfo_children())
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
