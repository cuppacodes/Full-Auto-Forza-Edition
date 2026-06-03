# ============================================================
#  forza_app.py — Entry point for Forza Auto GUI app
#  Flat file structure — no package folders needed
# ============================================================

import sys
import os
import traceback

def _except_hook(exc_type, exc_value, exc_tb):
    import tkinter.messagebox as mb
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    # Persist the crash so frozen --windowed failures (no stderr, and the
    # message box can be missed/auto-closed during startup) aren't lost.
    try:
        import os as _os, sys as _sys, time as _t
        base = (_os.path.dirname(_sys.executable)
                if getattr(_sys, 'frozen', False)
                else _os.path.dirname(_os.path.abspath(_sys.argv[0])))
        with open(_os.path.join(base, 'fafe_crash.log'), 'a',
                  encoding='utf-8') as f:
            f.write(_t.strftime('%Y-%m-%d %H:%M:%S\n') + msg + '\n')
    except Exception:
        pass
    try:
        mb.showerror("Forza Auto — Error", msg)
    except Exception:
        print(msg)

sys.excepthook = _except_hook

# Background-thread crashes don't reach sys.excepthook either — route them here.
import threading as _threading
def _thread_excepthook(args):
    _except_hook(args.exc_type, args.exc_value, args.exc_traceback)
try:
    _threading.excepthook = _thread_excepthook
except Exception:
    pass

# ── Path setup for frozen exe and dev ────────────────────────
if getattr(sys, 'frozen', False):
    # --onedir: exe and all files are in the same folder
    BASE = os.path.dirname(sys.executable)
    sys.path.insert(0, BASE)
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE)

# ── Launch ────────────────────────────────────────────────────
import customtkinter as ctk
from main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
