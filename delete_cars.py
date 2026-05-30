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
from capture import force_english_ime


_VK_MAP = {
    'enter':  0x0D, 'return': 0x0D,
    'esc':    0x1B, 'escape': 0x1B,
    'down':   0x28,
    'space':  0x20,
}

_KEYEVENTF_EXTENDEDKEY = 0x0001
_KEYEVENTF_KEYUP       = 0x0002
_KEYEVENTF_SCANCODE    = 0x0008
# Virtual keys that map to an EXTENDED scancode — must set the extended flag,
# else they collide with the numpad block (e.g. Down arrow's scancode 0x50 is
# also numpad-2). Covers the arrow/navigation cluster + R-Ctrl/Alt.
_EXTENDED_VKS = frozenset({
    0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,  # PgUp/PgDn/End/Home/arrows
    0x2D, 0x2E,                                        # Insert / Delete
    0xA3, 0xA5,                                        # R-Ctrl / R-Alt
})

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
    # Send the hardware SCANCODE instead of the virtual key. A Traditional
    # Chinese IME in native mode intercepts virtual-key input — and for this
    # script the keys (Space=convert, Down=next candidate, Enter=confirm) are
    # exactly the IME candidate-window keys, so they get eaten before the game
    # sees them. Scancodes go through the DirectInput / Raw Input path the game
    # reads, bypassing the IME.
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC
    flags = _KEYEVENTF_SCANCODE | (_KEYEVENTF_KEYUP if key_up else 0)
    if vk in _EXTENDED_VKS:
        flags |= _KEYEVENTF_EXTENDEDKEY
    inp = _INPUT(type=1, union=_INPUT_UNION(
        ki=_KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags,
                       time=0, dwExtraInfo=None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

def _key_press(key, post_wait=0.5):
    _send_vk(key, key_up=False)
    time.sleep(0.05)
    _send_vk(key, key_up=True)
    time.sleep(post_wait)

# Public alias — reused by the Buy worker in main_window.py so all four scripts
# share one IME-safe (scancode) key sender.
key_press = _key_press


def run(cfg: dict, stop_event: threading.Event,
        log_cb, status_cb, max_cars: int = 0):

    lang    = cfg.get('lang', 'en')
    post_kw = cfg.get('delete_post_key_wait', 0.5)

    def stop():
        return stop_event.is_set()

    def press(key, label='', wait=None):
        w = wait if wait is not None else post_kw
        log_cb(f'  [{key.upper()}] {label}')
        _key_press(key, post_wait=w)

    if max_cars > 0:
        log_cb(_at('log_delete_started_count', lang, n=max_cars))
    else:
        log_cb(_at('log_delete_started', lang))
    # Take the game out of native IME mode — a CJK IME otherwise eats the
    # keystrokes (incl. injected scancodes) before the game reads them.
    force_english_ime()
    time.sleep(0.2)
    loop_count = 0

    while not stop():
        loop_count += 1
        log_cb(f"-- {_at('delete_loop', lang)} #{loop_count}" +
               (f" / {max_cars}" if max_cars > 0 else "") + " --")

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

        # ── Check if we've hit the limit ─────────────────────
        if max_cars > 0 and loop_count >= max_cars:
            log_cb(_at('log_delete_limit_reached', lang, n=max_cars))
            break

    log_cb(_at('log_delete_stopped', lang))
