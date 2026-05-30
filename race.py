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

_KEYEVENTF_KEYUP    = 0x0002
_KEYEVENTF_SCANCODE = 0x0008

def _send_vk(key_name, key_up=False):
    vk = _VK_MAP.get(key_name.lower())
    if vk is None:
        return
    # Send the hardware SCANCODE instead of the virtual key. A Traditional
    # Chinese IME in native mode intercepts virtual-key input (e.g. X, W) for
    # composition before the game receives it, which makes the script fail.
    # Scancode input is delivered via the DirectInput / Raw Input path the game
    # actually reads, bypassing the IME — the same approach pydirectinput uses
    # for the nav keys. (All keys here are non-extended, so no extended flag.)
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC
    flags = _KEYEVENTF_SCANCODE | (_KEYEVENTF_KEYUP if key_up else 0)
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
    res    = _fresh.get('race_resolution', 'custom')
    folder = get_race_templates(res)
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
        return stop_event.is_set()

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
    # Take the game out of native IME mode — a CJK IME otherwise eats the
    # keystrokes (incl. injected scancodes) before the game reads them.
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
        key_down('w')

        wait_for("Restart menu", templates["restart_menu"], "restart_menu")
        key_up('w')
        if stop(): break
        log_cb(_at("log_released_w", lang))

        press(RESTART_KEY, "Restart Race")

        wait_for("Confirmation", templates["confirm"], "confirm")
        if stop(): break
        press(CONFIRM_KEY, "Confirm")

    key_up('w')   # safety release
    log_cb(_at("log_race_stopped", cfg.get("lang","en")))
    status_cb(_at("status_stopped", lang))
