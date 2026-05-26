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
    try:
        mb.showerror("Forza Auto — Error", msg)
    except Exception:
        print(msg)

sys.excepthook = _except_hook

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
