# ============================================================
#  automation/race.py — Race automation logic
#  All output goes through log_cb(message) instead of print()
#  Stop is signalled via stop_event (threading.Event)
# ============================================================

import cv2
import numpy as np
import time
import threading
import ctypes
from ctypes import wintypes

import config
from config import get_race_templates, get_nodes_file
from app_lang import t as _at
from capture import grab_frame, load_template, get_monitor_dims, force_english_ime
from detector import ScreenDetector




# Keys
_VK_MAP = {
    'enter':  0x0D, 'return': 0x0D,
    'x':      0x58,
    'w':      0x57,
    'escape': 0x1B, 'esc': 0x1B,
    'f9':     0x78,
}

class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("_pad", ctypes.c_byte * 28)]

class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]

_KEYEVENTF_EXTENDEDKEY = 0x0001
_KEYEVENTF_KEYUP       = 0x0002
_KEYEVENTF_SCANCODE    = 0x0008
# VKs that map to an extended scancode (none used here, kept for safety if
# extended keys are ever added — see delete_cars.py for the rationale).
_EXTENDED_VKS = frozenset({0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
                           0x2D, 0x2E, 0xA3, 0xA5})

def _vk_for_key(name: str):
    """Virtual-key code for a toggle-key name (e.g. 'f9', 'enter'), for
    GetAsyncKeyState polling. Handles F1–F24 and the keys in _VK_MAP."""
    name = (name or "").strip().lower()
    if name in _VK_MAP:
        return _VK_MAP[name]
    if name.startswith("f") and name[1:].isdigit():
        n = int(name[1:])
        if 1 <= n <= 24:
            return 0x70 + (n - 1)   # VK_F1 = 0x70
    if len(name) == 1:
        return ord(name.upper())    # letters / digits
    return None


def _send_vk(key_name, key_up=False):
    vk = _VK_MAP.get(key_name.lower())
    if vk is None:
        return
    # Send BOTH the virtual key (wVk) and the hardware scancode (wScan) so the
    # game receives input whether it reads the Windows message / VK path
    # (WM_KEYDOWN / GetAsyncKeyState) or the DirectInput / Raw Input scancode
    # path. Scancode-only (wVk=0) regressed VK-path games — notably the held W
    # during a race; VK-only (wScan=0) leaves DirectInput games with scancode
    # 0. Populating both is the most compatible. The CJK IME is handled
    # separately by capture.force_english_ime() at the start of the run.
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC
    flags = _KEYEVENTF_KEYUP if key_up else 0
    if vk in _EXTENDED_VKS:
        flags |= _KEYEVENTF_EXTENDEDKEY
    inp = _INPUT(type=1, union=_INPUT_UNION(
        ki=_KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=flags,
                       time=0, dwExtraInfo=None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

def _send_scancode(key_name, key_up=False):
    """Scancode injection WITH the KEYEVENTF_SCANCODE flag (wVk=0) — the
    DirectInput / Raw Input path the game uses for *gameplay* (held W). This is
    the same method pydirectinput uses for mastery's WASD nav, which works
    in-game. The dual `_send_vk` (no SCANCODE flag) is fine for menu taps but
    doesn't register as a true held key for driving."""
    vk = _VK_MAP.get(key_name.lower())
    if vk is None:
        return
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC
    flags = _KEYEVENTF_SCANCODE | (_KEYEVENTF_KEYUP if key_up else 0)
    if vk in _EXTENDED_VKS:
        flags |= _KEYEVENTF_EXTENDEDKEY
    inp = _INPUT(type=1, union=_INPUT_UNION(
        ki=_KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags,
                       time=0, dwExtraInfo=None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

def key_down(key): _send_vk(key, key_up=False)
def key_up(key):   _send_vk(key, key_up=True)

def key_press(key, post_wait=1.5):
    _send_vk(key, key_up=False)
    time.sleep(0.05)
    _send_vk(key, key_up=True)
    time.sleep(post_wait)


# ── Template matching ─────────────────────────────────────────

def _screen_matches(screen, template, threshold):
    if template.shape[0] > screen.shape[0] or template.shape[1] > screen.shape[1]:
        return False, 0.0
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, best_conf, _, _ = cv2.minMaxLoc(result)
    return best_conf >= threshold, best_conf


def _capture_frame(monitor_index):
    return grab_frame(monitor_index)


# ── Main runner ───────────────────────────────────────────────

TEMPLATE_KEYS = ["start_menu", "racing", "restart_menu", "confirm"]


def run(cfg: dict, stop_event: threading.Event,
        log_cb, status_cb, warn_cb=None, section_cb=None):
    """
    Main race automation loop.
    cfg: config dict
    stop_event: set this to stop
    log_cb(msg): append a line to the log
    status_cb(msg): update the status bar
    section_cb(msg): start a new (bounded) log section; falls back to log_cb
    """
    section = section_cb or log_cb

    lang          = cfg.get("lang", "en")
    monitor_index = cfg.get("monitor_index", 1)
    # Per-template thresholds
    def _thresh(key):
        return _fresh.get(f'thresh_{key}', 0.80)

    check_iv      = cfg.get("race_check_interval", 0.5)
    post_kw       = cfg.get("race_post_key_wait", 0.75)

    START_RACE_KEY = 'enter'
    RESTART_KEY    = 'x'
    CONFIRM_KEY    = 'enter'

    # Load templates
    current_w, current_h, _, _ = get_monitor_dims(monitor_index)
    templates = {}
    # Always read resolution fresh from config.json at start
    import config as _cfg_mod
    _fresh = _cfg_mod.load()
    res      = _fresh.get('race_resolution', 'custom')
    tpl_lang = _cfg_mod.resolve_template_lang(_fresh)
    folder   = get_race_templates(res, tpl_lang)
    log_cb(f"  Templates: {tpl_lang} / {res}")
    # VK of the stop hotkey, for the hook-independent stop poll in stop().
    _toggle_vk = _vk_for_key(_fresh.get('toggle_key', 'f9'))
    detector = ScreenDetector(_fresh)
    for key in TEMPLATE_KEYS:
        try:
            img, scale = load_template(folder, key,
                                       current_w, current_h, grayscale=True)
            templates[key] = img
            log_cb(_at("log_template_loaded", cfg.get("lang","en"), key=key, scale=f"{scale:.2f}"))
        except FileNotFoundError:
            log_cb(_at("log_template_missing", cfg.get("lang","en"), key=key))
            status_cb(_at("status_setup_incomplete", cfg.get("lang","en")))
            return

    def stop():
        if stop_event.is_set():
            return True
        # Hook-independent stop. While holding W we inject ~33 keydowns/sec via
        # SendInput; that flood goes through the same low-level keyboard hook the
        # `keyboard` library uses for the F9 hotkey, and under it the hook can
        # fail to deliver F9 — so the script "can't be stopped" mid-race. Reading
        # the physical key state directly (GetAsyncKeyState, high bit = down)
        # bypasses the hook entirely. The W-hold thread calls stop() at ~33Hz so
        # even a quick tap is caught.
        if _toggle_vk:
            try:
                if ctypes.windll.user32.GetAsyncKeyState(_toggle_vk) & 0x8000:
                    stop_event.set()
                    return True
            except Exception:
                pass
        return False

    def wait_for(label, template, key, timeout=float('inf')):
        status_cb(_at("status_waiting_for", lang, label=label))
        def _warn(best):
            msg = _at("log_warn_not_detected", lang, label=label)
            msg += f" (best {best.source}: {best.score:.0%})"
            (warn_cb or log_cb)(msg)

        result = detector.wait_for(
            frame_cb=lambda: _capture_frame(monitor_index),
            key=key,
            template=template,
            threshold=_thresh(key),
            stop_cb=stop,
            interval=check_iv,
            timeout=timeout,
            on_warn=_warn,
        )
        if result.matched:
            log_cb(_at("log_detected", lang, label=label,
                       conf=f"{result.score:.0%}"))
            return True
        return False

    def press(key, label):
        log_cb(_at("log_pressing", lang, key=key.upper(), label=label))
        key_press(key, post_wait=post_kw)

    log_cb(_at("log_race_started", cfg.get("lang","en")))
    # Switch the game to English input only if it isn't already (see
    # capture.force_english_ime). Disable entirely with auto_english_ime=false
    # for users who manage their IME themselves.
    if _fresh.get("auto_english_ime", True):
        force_english_ime()
        time.sleep(0.2)
    loop_count = 0

    while not stop():
        loop_count += 1
        section(f"-- {_at('log_loop', lang)} #{loop_count} --")

        wait_for("Start Race menu", templates["start_menu"], "start_menu")
        if stop(): break
        press(START_RACE_KEY, "Start Race")

        wait_for("Race HUD", templates["racing"], "racing")
        if stop(): break

        log_cb(_at("log_holding_w", lang))
        status_cb(_at("status_racing", lang))
        # Hold W by re-asserting the keydown at ~30ms (the keyboard auto-repeat
        # rate) in a background thread. A single SendInput keydown isn't reliably
        # treated as a sustained hold by the game — it can register as a tap, so
        # the car coasts/slows. Re-pressing keeps it at full throttle whether the
        # game reads key STATE or keydown EVENTS. A single key_up at the end
        # releases it (auto-repeat is many keydowns + one keyup).
        _hold = threading.Event(); _hold.set()
        def _hold_w():
            while _hold.is_set() and not stop():
                _send_scancode('w', key_up=False)   # flagged scancode = held
                time.sleep(0.03)
        _ht = threading.Thread(target=_hold_w, daemon=True)
        _ht.start()

        wait_for("Restart menu", templates["restart_menu"], "restart_menu")
        _hold.clear()
        _ht.join(timeout=0.3)
        _send_scancode('w', key_up=True)
        if stop(): break
        log_cb(_at("log_released_w", lang))

        press(RESTART_KEY, "Restart Race")

        wait_for("Confirmation", templates["confirm"], "confirm")
        if stop(): break
        press(CONFIRM_KEY, "Confirm")

    key_up('w'); _send_scancode('w', key_up=True)   # safety release (both paths)
    log_cb(_at("log_race_stopped", cfg.get("lang","en")))
    status_cb(_at("status_stopped", lang))
