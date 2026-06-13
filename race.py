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
from capture import (grab_frame, load_template, get_monitor_dims,
                     force_english_ime, get_foreground_window, focus_window)
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

# Two detections: the Start Race screen (start_menu) and the race-END screen
# (restart_menu). start_menu is detected — NOT timed — because the load time
# between finishing a race and the next Start Race screen varies. racing /
# confirm remain blind timing.
TEMPLATE_KEYS = ["start_menu", "restart_menu"]

# Fixed step waits (seconds) for the timed steps.
_PRE_W_WAIT   = 4.0    # step 3: after pressing Enter, wait before holding W
_CONFIRM_WAIT = 1.25   # step 6: after pressing X, wait before Enter (confirm)


def run(cfg: dict, stop_event: threading.Event,
        log_cb, status_cb, max_loops: int = 0,
        warn_cb=None, section_cb=None):
    """
    Main race automation loop.
    cfg: config dict
    stop_event: set this to stop
    log_cb(msg): append a line to the log
    status_cb(msg): update the status bar
    max_loops: stop after this many completed races (0 = unlimited)
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
    # Single-reference templates: preset resolutions fall back to (or prefer)
    # the one REFERENCE_RES set, downscaled. Custom keeps the user's own capture.
    ref_folder = None
    prefer_ref = False
    if res != 'custom':
        ref_folder = get_race_templates(_cfg_mod.REFERENCE_RES, tpl_lang)
        prefer_ref = _fresh.get('template_prefer_reference', True)
    log_cb(f"  Templates: {tpl_lang} / {res}")
    # Detection mode follows the template type automatically (no manual toggle):
    # preset resolutions use the robust OCR-confirm "default" detection; custom
    # templates use the pixel-only "custom" method. See ScreenDetector.
    _fresh['detector_ocr_primary'] = (res != 'custom')
    # VK of the stop hotkey, for the hook-independent stop poll in stop().
    _toggle_vk = _vk_for_key(_fresh.get('toggle_key', 'f9'))
    detector = ScreenDetector(_fresh)
    for key in TEMPLATE_KEYS:
        try:
            img, scale = load_template(folder, key,
                                       current_w, current_h, grayscale=True,
                                       ref_folder=ref_folder, prefer_ref=prefer_ref)
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

    def wait_for(label, template, key, timeout=float('inf'), warn=True):
        # warn=False suppresses the 10s "not detected" red warning for steps
        # where a long wait is NORMAL — e.g. waiting for the Restart menu, which
        # only appears once the whole race finishes (far more than 10s).
        # Detection still continues; only the noisy warning is silenced.
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
            on_warn=_warn if warn else None,
        )
        if result.matched:
            log_cb(_at("log_detected", lang, label=label,
                       conf=f"{result.score:.0%}"))
            return True
        return False

    def press(key, label):
        log_cb(_at("log_pressing", lang, key=key.upper(), label=label))
        key_press(key, post_wait=post_kw)

    def wait(seconds):
        """Stop-aware sleep so F9/Stop isn't blocked by the fixed timing waits."""
        end = time.time() + seconds
        while time.time() < end:
            if stop():
                return
            time.sleep(0.1)

    def announce(msg):
        """Log a step AND reflect it in the status bar / overlay (the fixed
        waits have no detection to drive status, so set it explicitly)."""
        log_cb(msg)
        status_cb(msg)

    log_cb(_at("log_race_started", cfg.get("lang","en")))
    if max_loops > 0:
        log_cb(_at("log_race_started_count", lang, n=max_loops))
    # Switch the game to English input only if it isn't already (see
    # capture.force_english_ime). Disable entirely with auto_english_ime=false
    # for users who manage their IME themselves.
    if _fresh.get("auto_english_ime", True):
        force_english_ime()
        time.sleep(0.2)
    loop_count = 0
    # Foreground (game) window captured while racing, so W can be released to
    # the GAME even if the user stopped via the FAFE UI button (which moves
    # focus to FAFE). See _release_w / capture.focus_window.
    game_hwnd = None

    def _release_w():
        # Restore game focus first: if stopped via the FAFE UI button, focus is
        # now on FAFE, so a keyup sent now would go to FAFE and the game would
        # keep W held (stuck throttle). Refocusing the game (a no-op on the
        # hotkey/detection path, where it's already foreground) makes the
        # release reach the game on BOTH scancode and VK paths.
        if game_hwnd:
            focus_window(game_hwnd)
        key_up('w')
        _send_scancode('w', key_up=True)

    while not stop():
        loop_count += 1
        section(f"-- {_at('log_loop', lang)} #{loop_count} --")

        # ── 1. Wait for the Start Race screen (DETECTED, not timed — the
        #       load time after a restart varies). On loop 1 the user is
        #       already here, so it detects immediately. ──────────────────
        wait_for("Start Race menu", templates["start_menu"], "start_menu")
        if stop(): break

        # ── 2. Press Enter to start the race ──────────────────────────
        press(START_RACE_KEY, "Start Race")
        if stop(): break

        # ── 3. Wait for the race to begin, then hold W ────────────────
        announce(_at("log_race_wait_start", lang))
        wait(_PRE_W_WAIT)
        if stop(): break

        log_cb(_at("log_holding_w", lang))
        status_cb(_at("status_racing", lang))
        # Hold W by re-asserting the keydown at ~30ms (the keyboard auto-repeat
        # rate) in a background thread. A single SendInput keydown isn't reliably
        # treated as a sustained hold by the game — it can register as a tap, so
        # the car coasts/slows. Re-pressing keeps it at full throttle whether the
        # game reads key STATE or keydown EVENTS. A single key_up at the end
        # releases it (auto-repeat is many keydowns + one keyup).
        game_hwnd = get_foreground_window()   # game is focused while racing
        _hold = threading.Event(); _hold.set()
        def _hold_w():
            while _hold.is_set() and not stop():
                _send_scancode('w', key_up=False)   # flagged scancode = held
                time.sleep(0.03)
        _ht = threading.Thread(target=_hold_w, daemon=True)
        _ht.start()

        # ── 4. Hold W until the Restart menu appears (ONLY detection) ─
        # The race lasts minutes, so the "not detected" warning is suppressed
        # (warn=False) — a long wait here is normal, not a detection problem.
        wait_for("Restart menu", templates["restart_menu"], "restart_menu",
                 warn=False)
        _hold.clear()
        _ht.join(timeout=0.3)
        _release_w()
        if stop(): break
        log_cb(_at("log_released_w", lang))

        # One full race completed. Stop here (on the results/restart screen)
        # when the requested number of races is reached, rather than kicking
        # off another race we'd immediately abandon.
        if max_loops > 0 and loop_count >= max_loops:
            log_cb(_at("log_race_limit_reached", lang, n=max_loops))
            break

        # ── 5. Release W (done above), press X to restart ─────────────
        press(RESTART_KEY, "Restart Race")

        # ── 6. Wait, then press Enter to confirm the restart ──────────
        wait(_CONFIRM_WAIT)
        if stop(): break
        press(CONFIRM_KEY, "Confirm")

    _release_w()   # safety release (focus game first, both VK + scancode paths)
    log_cb(_at("log_race_stopped", cfg.get("lang","en")))
    status_cb(_at("status_stopped", lang))
