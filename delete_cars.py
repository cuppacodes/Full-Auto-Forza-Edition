# ============================================================
#  automation/delete_cars.py — Delete Used Cars automation
#  Same snake navigation as mastery.py
#  Per car: Enter → Down×4 → Enter → Down×1 → Enter
# ============================================================

import time
import threading
import ctypes
from ctypes import wintypes

from app_lang import t as _at


_VK_MAP = {
    'enter':  0x0D, 'return': 0x0D,
    'esc':    0x1B, 'escape': 0x1B,
    'down':   0x28,
}

class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("_pad", ctypes.c_byte * 28)]

class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]

def _send_vk(key_name, key_up=False):
    vk = _VK_MAP.get(key_name.lower())
    if vk is None:
        return
    flags = 0x0002 if key_up else 0
    inp = _INPUT(type=1, union=_INPUT_UNION(
        ki=_KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags,
                       time=0, dwExtraInfo=None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

def _key_press(key, post_wait=0.5):
    _send_vk(key, key_up=False)
    time.sleep(0.05)
    _send_vk(key, key_up=True)
    time.sleep(post_wait)


def run(cfg: dict, stop_event: threading.Event,
        log_cb, status_cb):

    lang    = cfg.get('lang', 'en')
    post_kw = cfg.get('delete_post_key_wait', 0.5)

    def stop():
        return stop_event.is_set()

    def press(key, label='', wait=None):
        w = wait if wait is not None else post_kw
        log_cb(f'  [{key.upper()}] {label}')
        _key_press(key, post_wait=w)

    log_cb(_at('log_delete_started', lang))
    loop_count = 0

    while not stop():
        loop_count += 1
        log_cb(f"-- {_at('delete_loop', lang)} #{loop_count} --")

        if stop(): break

        # ── Open action menu ──────────────────────────────────
        press('enter', 'Open action menu', wait=1.2)
        if stop(): break

        # ── Navigate to Remove / Sell option (Down × 4) ──────
        for i in range(4):
            press('down', f'Down {i+1}/4')
            if stop(): break
        if stop(): break

        # ── Confirm selection ─────────────────────────────────
        press('enter', 'Select option', wait=1.0)
        if stop(): break

        # ── Confirm dialog: Down × 1 → Enter ─────────────────
        press('down', 'Confirm: move to Yes')
        if stop(): break

        press('enter', 'Confirm delete', wait=1.5)
        if stop(): break

    log_cb(_at('log_delete_stopped', lang))
