# ============================================================
#  automation/mastery.py — Full Mastery automation logic
#  Snake navigation: 12 cars in 3x4 grid, no detection needed
#  All output via log_cb / status_cb instead of print()
# ============================================================

import cv2
import numpy as np
import time
import threading
import ctypes
from ctypes import wintypes
import pydirectinput

from app_lang import t as _at
import config
from config import get_mastery_templates, get_nodes_file
from capture import grab_frame, load_template, load_nodes, get_monitor_dims, force_english_ime
from detector import ScreenDetector




_VK_MAP = {
    'enter':  0x0D, 'return': 0x0D,
    'esc':    0x1B, 'escape': 0x1B,
    'x':      0x58,
    # Arrows (keys mode): in _EXTENDED_VKS, so _send_vk sets
    # KEYEVENTF_EXTENDEDKEY — without it Down collides with numpad-2.
    'up':     0x26, 'down':   0x28,
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
_EXTENDED_VKS = frozenset({0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
                           0x2D, 0x2E, 0xA3, 0xA5})

def _send_vk(key_name, key_up=False):
    vk = _VK_MAP.get(key_name.lower())
    if vk is None:
        return
    # Send BOTH the virtual key (wVk) and the hardware scancode (wScan) so the
    # game receives input whether it reads the Windows message / VK path
    # (WM_KEYDOWN / GetAsyncKeyState) or the DirectInput / Raw Input scancode
    # path. Scancode-only (wVk=0) regressed VK-path games; VK-only (wScan=0)
    # leaves DirectInput games with scancode 0. Both populated is the most
    # compatible. CJK IME is handled by capture.force_english_ime() at run start.
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)  # MAPVK_VK_TO_VSC
    flags = _KEYEVENTF_KEYUP if key_up else 0
    if vk in _EXTENDED_VKS:
        flags |= _KEYEVENTF_EXTENDEDKEY
    inp = _INPUT(type=1, union=_INPUT_UNION(
        ki=_KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=flags,
                       time=0, dwExtraInfo=None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

def _key_press(key, post_wait=1.2):
    _send_vk(key, key_up=False)
    time.sleep(0.05)
    _send_vk(key, key_up=True)
    time.sleep(post_wait)


def _mouse_click(x, y, mon_left=0, mon_top=0, post_wait=0.8):
    ctypes.windll.user32.SetCursorPos(x + mon_left, y + mon_top)
    time.sleep(0.1)

    class _MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class _MINPUT_UNION(ctypes.Union):
        _fields_ = [("mi", _MOUSEINPUT), ("_pad", ctypes.c_byte * 28)]

    class _MINPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", _MINPUT_UNION)]

    for flag in (0x0002, 0x0004):
        inp = _MINPUT(type=0, union=_MINPUT_UNION(mi=_MOUSEINPUT(
            dx=0, dy=0, mouseData=0, dwFlags=flag,
            time=0, dwExtraInfo=None)))
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_MINPUT))
        time.sleep(0.05)
    time.sleep(post_wait)


def _capture_frame(monitor_index):
    return grab_frame(monitor_index)


def _screen_matches(screen, template, threshold):
    if template.shape[0] > screen.shape[0] or template.shape[1] > screen.shape[1]:
        return False, 0.0, (0, 0)
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, best_conf, _, best_loc = cv2.minMaxLoc(result)
    return best_conf >= threshold, best_conf, best_loc


def _find_on_screen(screen, template, threshold):
    matched, conf, loc = _screen_matches(screen, template, threshold)
    if matched:
        cx = loc[0] + template.shape[1] // 2
        cy = loc[1] + template.shape[0] // 2
        return True, conf, (cx, cy)
    return False, conf, (0, 0)


TEMPLATE_KEYS = [
    "mastery_ride_car",
    "mastery_esc_hint",
    "mastery_upgrade_item",
    "mastery_mastery_item",
    "mastery_anchor",
    "mastery_my_cars",
    "mastery_sort_recent",
]

def _nav_keys_for_loop(loop: int) -> list:
    """
    Infinite snake navigation.
    Loop 1: [] (start at row1 col1)
    Loop 2: [S]  Loop 3: [S]  (finish col1 going down)
    Loop 4: [D]  (move to col2 at row3)
    Loop 5: [W]  Loop 6: [W]  (finish col2 going up)
    Loop 7: [D]  (move to col3 at row1)
    ... and so on indefinitely
    """
    if loop == 1:
        return []
    # Build the repeating unit: [move1, move2, D]
    # Col going down: S, S, D
    # Col going up:   W, W, D
    # idx is 0-based position after the first car
    idx = loop - 2
    unit = idx % 3        # 0=first move, 1=second move, 2=D to next col
    col  = idx // 3       # which column transition we're in
    going_down = (col % 2 == 0)
    if unit == 2:
        return ['d']
    return ['s'] if going_down else ['w']



def run(cfg: dict, stop_event: threading.Event,
        log_cb, status_cb, max_cars: int = 0, warn_cb=None, section_cb=None):
    # Mode dispatch: "keys" = blind timed key sequences (run_keys, experimental),
    # anything else = the original detection flow below. Toggled per-tab in the
    # UI; saved as mastery_mode in config.
    if str(cfg.get("mastery_mode", "detect")).strip().lower() == "keys":
        return run_keys(cfg, stop_event, log_cb, status_cb,
                        max_cars=max_cars, section_cb=section_cb)
    section       = section_cb or log_cb
    lang          = cfg.get("lang", "en")
    monitor_index = cfg.get("monitor_index", 1)
    # Per-template thresholds
    def _thresh(key):
        return _fresh.get(f'thresh_{key}', 0.80)

    post_kw       = cfg.get("mastery_post_key_wait", 1.2)
    post_cw       = cfg.get("mastery_post_click_wait", 0.8)
    post_ncw      = cfg.get("mastery_node_click_wait", post_cw)
    check_iv      = cfg.get("mastery_check_interval", 0.5)
    start_loop    = max(1, min(3, int(cfg.get("mastery_start_loop", 1))))

    current_w, current_h, mon_left, mon_top = get_monitor_dims(monitor_index)

    # Load templates
    templates = {}
    # Always read resolution fresh from config.json at start
    import config as _cfg_mod
    _fresh = _cfg_mod.load()
    res      = _fresh.get('mastery_resolution', 'custom')
    tpl_lang = _cfg_mod.resolve_template_lang(_fresh)
    folder   = get_mastery_templates(res, tpl_lang)
    detector = ScreenDetector(_fresh)
    log_cb(_at('log_template_set', lang, res=res, folder=folder))
    for key in TEMPLATE_KEYS:
        try:
            img, scale = load_template(folder, key,
                                       current_w, current_h, grayscale=True)
            templates[key] = img
            log_cb(_at("log_template_loaded", lang, key=key, scale=f"{scale:.2f}"))
        except FileNotFoundError:
            log_cb(_at("log_template_missing", lang, key=key))
            status_cb(_at("status_setup_incomplete", lang))
            return

    # Load nodes
    try:
        nodes_file = get_nodes_file(res, tpl_lang)
        nodes = load_nodes(nodes_file, current_w, current_h,
                           aspect_fix=_fresh.get("nodes_aspect_fix", True))
        log_cb(_at("log_nodes_loaded", lang, n=len(nodes)))
    except Exception:
        log_cb(_at("log_nodes_missing", lang))
        status_cb(_at("status_setup_incomplete", lang))
        return

    def stop():
        return stop_event.is_set()

    def wait_for(label, template, key, timeout=float('inf'), warn=True):
        # warn=False suppresses the 10s "not detected" red warning for steps
        # where a long wait is NORMAL (e.g. the ESC hint / My Cars screen can
        # legitimately take a while to appear). Detection still continues.
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

    def click_template(label, template, key):
        result = detector.detect(
            _capture_frame(monitor_index), key, template, _thresh(key),
            stable=False)
        if result.matched:
            log_cb(_at("log_clicking", lang, label=label,
                       conf=f"{result.score:.0%}"))
            _mouse_click(result.location[0], result.location[1],
                         mon_left, mon_top, post_cw)
            return True
        return False

    if max_cars > 0:
        log_cb(_at("log_mastery_started_count", lang, n=max_cars))
    else:
        log_cb(_at("log_mastery_started", lang))
    # Switch the game to English input only if it isn't already (see
    # capture.force_english_ime). Disable with auto_english_ime=false.
    if _fresh.get("auto_english_ime", True):
        force_english_ime()
        time.sleep(0.2)
    loop_count = start_loop - 1
    car_num    = 0

    while not stop():
        loop_count += 1
        car_num    += 1
        is_first   = (car_num == 1)

        # ── Navigate to next car ──────────────────────────────
        # Skip navigation on the first car — the user is already positioned there.
        nav_keys = [] if is_first else _nav_keys_for_loop(loop_count)
        section(_at("log_car", lang, n=car_num) +
                (f" / {max_cars}" if max_cars > 0 else ""))

        if nav_keys:
            log_cb(_at("log_navigating", lang, keys=' '.join(k.upper() for k in nav_keys)))
            for key in nav_keys:
                pydirectinput.press(key)
                time.sleep(0.4)
            time.sleep(0.3)
        else:
            log_cb(_at("log_loop1_start", lang, row=start_loop))

        # ── Open action menu ──────────────────────────────────
        log_cb(_at("log_open_action_menu", lang))
        _send_vk('enter', key_up=False); time.sleep(0.05)
        _send_vk('enter', key_up=True)
        time.sleep(1.5)

        # ── Detect and click Ride This Car ────────────────────
        status_cb(_at("status_waiting_for", lang, label="Ride This Car"))
        matched, conf, loc = False, 0.0, (0, 0)
        for _ in range(10):
            if stop(): break
            result = detector.detect(
                _capture_frame(monitor_index),
                "mastery_ride_car",
                templates["mastery_ride_car"],
                _thresh("mastery_ride_car"),
                stable=False)
            matched = result.matched
            conf = result.score
            loc = result.location
            if matched: break
            time.sleep(0.5)

        if not matched:
            log_cb(_at("log_action_menu_not_found", lang))
            continue

        log_cb(_at("log_clicking", lang, label="Ride This Car", conf=f"{conf:.0%}"))
        _mouse_click(loc[0], loc[1], mon_left, mon_top, post_cw)

        # ── Cutscene ──────────────────────────────────────────
        ok = wait_for("ESC hint", templates["mastery_esc_hint"], "mastery_esc_hint",
                      warn=False)
        if stop(): break
        if not ok:
            log_cb(_at("log_cutscene_continuing", lang))

        # ── ESC → Upgrade & Tuning ────────────────────────────
        log_cb(_at("log_pressing_esc", lang))
        _key_press('esc', post_wait=post_kw)

        wait_for("Upgrade & Tuning", templates["mastery_upgrade_item"], "mastery_upgrade_item")
        if stop(): break
        click_template("Upgrade & Tuning", templates["mastery_upgrade_item"], "mastery_upgrade_item")

        time.sleep(0.8)

        # ── Car Mastery ───────────────────────────────────────
        wait_for("Car Mastery", templates["mastery_mastery_item"], "mastery_mastery_item")
        if stop(): break
        click_template("Car Mastery", templates["mastery_mastery_item"], "mastery_mastery_item")

        wait_for("Mastery screen", templates["mastery_anchor"], "mastery_anchor")
        if stop(): break

        # ── Click 6 nodes ─────────────────────────────────────
        log_cb(_at("log_clicking_nodes", lang, n=len(nodes)))
        for i, (nx, ny) in enumerate(nodes, start=1):
            if stop(): break
            log_cb(_at("log_node", lang, i=i, n=len(nodes), x=nx, y=ny))
            _mouse_click(nx, ny, mon_left, mon_top, post_ncw)
            time.sleep(0.3)

        if stop(): break

        # ── ESC x2 → My Cars ─────────────────────────────────
        log_cb(_at("log_esc_back", lang))
        _key_press('esc', post_wait=1.0)
        _key_press('esc', post_wait=1.0)

        wait_for("My Cars", templates["mastery_my_cars"], "mastery_my_cars",
                 warn=False)
        if stop(): break
        click_template("My Cars", templates["mastery_my_cars"], "mastery_my_cars")
        time.sleep(0.8)

        # ── Sort by Recently Added ────────────────────────────
        matched_sort = False
        for attempt in range(1, 3):
            if stop(): break
            log_cb(_at("log_sort_pressing_x", lang, n=attempt))
            pydirectinput.press('x')
            time.sleep(1.2)
            result = detector.detect(
                _capture_frame(monitor_index),
                "mastery_sort_recent",
                templates["mastery_sort_recent"],
                _thresh("mastery_sort_recent"),
                stable=False)
            matched_sort = result.matched
            conf = result.score
            loc = result.location
            if matched_sort:
                break
            log_cb(_at("log_sort_not_detected", lang))

        if stop(): break

        if matched_sort:
            log_cb(_at("log_clicking", lang, label="Recently Added",
                        conf=f"{conf:.0%}"))
            _mouse_click(loc[0], loc[1], mon_left, mon_top, post_cw)
        else:
            log_cb(_at("log_sort_not_found", lang))

        time.sleep(0.8)

        if max_cars > 0 and car_num >= max_cars:
            log_cb(_at("log_mastery_limit_reached", lang, n=max_cars))
            break

    log_cb(_at("log_mastery_stopped", lang))
    status_cb(_at("status_stopped", lang))


# ── Keyboard-sequence mode ("keys") ──────────────────────────
# Blind timed key presses instead of screen detection. The menu layout is
# fixed, so each step is a known key sequence + wait; nothing is detected,
# no templates are needed, and the red "not detected" warning can't occur.
# Only the 6 mastery-node positions remain coordinate-driven (mouse clicks).
# Explicit 1s / 11s / 2s waits are fixed by design; mastery_post_key_wait
# still paces the screen-transition Enters and mastery_node_click_wait the
# node clicks. Toggled via the mastery_mode config ("detect" = original).

# Cursor-move tap interval inside a menu (no screen transition → no need for
# the full mastery_post_key_wait between repeated Down/Up presses).
_TAP_WAIT = 0.25


def run_keys(cfg: dict, stop_event: threading.Event,
             log_cb, status_cb, max_cars: int = 0, section_cb=None):
    section       = section_cb or log_cb
    lang          = cfg.get("lang", "en")
    monitor_index = cfg.get("monitor_index", 1)

    # Always read settings fresh from config.json at start (same as detect mode)
    import config as _cfg_mod
    _fresh = _cfg_mod.load()
    post_kw    = _fresh.get("mastery_post_key_wait", 1.2)
    post_cw    = _fresh.get("mastery_post_click_wait", 0.8)
    post_ncw   = _fresh.get("mastery_node_click_wait", post_cw)
    start_loop = max(1, min(3, int(_fresh.get("mastery_start_loop", 1))))
    # TESTING AID: on the first car only, skip ahead to this step (1 = normal).
    try:
        start_step = max(1, int(_fresh.get("mastery_keys_start_step", 1)))
    except (TypeError, ValueError):
        start_step = 1

    current_w, current_h, mon_left, mon_top = get_monitor_dims(monitor_index)

    # Nodes are the ONLY capture this mode needs (no templates).
    res      = _fresh.get('mastery_resolution', 'custom')
    tpl_lang = _cfg_mod.resolve_template_lang(_fresh)
    try:
        nodes_file = get_nodes_file(res, tpl_lang)
        nodes = load_nodes(nodes_file, current_w, current_h,
                           aspect_fix=_fresh.get("nodes_aspect_fix", True))
        log_cb(_at("log_nodes_loaded", lang, n=len(nodes)))
    except Exception:
        log_cb(_at("log_nodes_missing", lang))
        status_cb(_at("status_setup_incomplete", lang))
        return

    def stop():
        return stop_event.is_set()

    def wait(seconds):
        """Stop-aware sleep so F9/Stop isn't blocked by the long fixed waits."""
        end = time.time() + seconds
        while time.time() < end:
            if stop():
                return
            time.sleep(0.1)

    def taps(key, n):
        """n quick presses of a menu-cursor key (Down/Up)."""
        for _ in range(n):
            if stop():
                return
            _key_press(key, post_wait=_TAP_WAIT)

    if max_cars > 0:
        log_cb(_at("log_mastery_started_count", lang, n=max_cars))
    else:
        log_cb(_at("log_mastery_started", lang))
    log_cb(_at("log_mastery_mode_keys", lang))
    if start_step > 1:
        log_cb(f"  [TEST] First car: starting from step {start_step}.")
    # Switch the game to English input only if it isn't already (see
    # capture.force_english_ime). Disable with auto_english_ime=false.
    if _fresh.get("auto_english_ime", True):
        force_english_ime()
        time.sleep(0.2)

    loop_count = start_loop - 1
    car_num    = 0

    while not stop():
        loop_count += 1
        car_num    += 1
        is_first   = (car_num == 1)

        # TESTING AID: on the first car, skip steps before start_step. Later
        # cars always run every step (start_step only affects car #1).
        def _step(n):
            return (not is_first) or (n >= start_step)

        # ── 1. Navigate to next car (snake, unchanged) ────────
        nav_keys = [] if is_first else _nav_keys_for_loop(loop_count)
        section(_at("log_car", lang, n=car_num) +
                (f" / {max_cars}" if max_cars > 0 else ""))

        if _step(1):
            if nav_keys:
                log_cb(_at("log_navigating", lang,
                           keys=' '.join(k.upper() for k in nav_keys)))
                for key in nav_keys:
                    pydirectinput.press(key)
                    time.sleep(0.4)
                time.sleep(0.3)
            else:
                log_cb(_at("log_loop1_start", lang, row=start_loop))

        # ── 2. Enter → open action menu ───────────────────────
        if _step(2):
            log_cb(_at("log_open_action_menu", lang))
            _key_press('enter', post_wait=1.0)
            if stop(): break

        # ── 3. Enter → Ride This Car ──────────────────────────
        if _step(3):
            log_cb(_at("log_mkeys_ride", lang))
            _key_press('enter', post_wait=0.0)

        # ── 4. Timed cutscene skip: 11s → ESC ─────────────────
        if _step(4):
            log_cb(_at("log_mkeys_cutscene", lang))
            status_cb(_at("log_mkeys_cutscene", lang))
            wait(11.0)
            if stop(): break
            _key_press('esc', post_wait=post_kw)

        # ── 5. Down ×1 + Enter → Upgrade & Tuning ─────────────
        if _step(5):
            log_cb(_at("log_mkeys_upgrade", lang))
            taps('down', 1)
            if stop(): break
            _key_press('enter', post_wait=post_kw)

        # ── 6. Down ×7 + Enter → Car Mastery ──────────────────
        if _step(6):
            log_cb(_at("log_mkeys_mastery", lang))
            taps('down', 7)
            if stop(): break
            _key_press('enter', post_wait=0.0)

        # ── 7. Fixed 2s for the mastery screen to load ────────
        if _step(7):
            log_cb(_at("log_mkeys_wait_mastery", lang))
            wait(2.0)
            if stop(): break

        # ── 8. Click 6 nodes (unchanged) ──────────────────────
        if _step(8):
            log_cb(_at("log_clicking_nodes", lang, n=len(nodes)))
            for i, (nx, ny) in enumerate(nodes, start=1):
                if stop(): break
                log_cb(_at("log_node", lang, i=i, n=len(nodes), x=nx, y=ny))
                _mouse_click(nx, ny, mon_left, mon_top, post_ncw)
                time.sleep(0.3)
            if stop(): break

        # ── 9. ESC ×2 to exit (unchanged) ─────────────────────
        if _step(9):
            log_cb(_at("log_esc_back", lang))
            _key_press('esc', post_wait=1.0)
            _key_press('esc', post_wait=1.0)
            if stop(): break

        # ── 10. Up ×1 + Enter → My Cars ───────────────────────
        if _step(10):
            log_cb(_at("log_mkeys_mycars", lang))
            taps('up', 1)
            if stop(): break
            _key_press('enter', post_wait=post_kw)

        # ── 11. X + Down ×6 + Enter → sort by Recently Added ──
        if _step(11):
            log_cb(_at("log_mkeys_sort", lang))
            _key_press('x', post_wait=1.2)
            taps('down', 6)
            if stop(): break
            _key_press('enter', post_wait=0.8)

        if max_cars > 0 and car_num >= max_cars:
            log_cb(_at("log_mastery_limit_reached", lang, n=max_cars))
            break

    log_cb(_at("log_mastery_stopped", lang))
    status_cb(_at("status_stopped", lang))
