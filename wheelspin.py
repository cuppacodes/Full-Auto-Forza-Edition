# ============================================================
#  automation/wheelspin.py — Auto Spin Wheel automation logic
#  ENTRY: from the My Horizon menu, detect the Super Wheelspin tile
#  and click it (starts the first spin; the spin screen then persists).
#  Each spin is DETECTION-GATED, not timed:
#    1. spin   (click for #1 / Enter for #2+)
#    2. wait for the skip/spin stage  → Enter (skip-forward)
#    3. wait for the prize/collect stage → Enter (collect)
#    4. duplicate-handling inner loop
#  Stage waits use detector.wait_for (wait until the screen is actually
#  present — F9/Stop recovers); the duplicate check is TIME-BOXED
#  (a non-detection is the NORMAL "no duplicate" outcome).
#  Output via log_cb / status_cb; stop via stop_event.
# ============================================================

import time
import threading
import ctypes
from ctypes import wintypes

import config
from config import get_wheelspin_templates
from app_lang import t as _at
from capture import grab_frame, load_template, get_monitor_dims, force_english_ime
from detector import ScreenDetector
# Reuse the IME-safe (dual VK+scancode) key sender shared by Delete/Buy.
# wheelspin only presses 'enter' and 'down' (down is an extended VK there).
from delete_cars import key_press


# ── Tunable values (constants; some overridable via Settings) ──
SUPER_FIND_WINDOW = 12.0  # max time to find the Super Wheelspin tile at start
# A Super Wheelspin has 3 wheels, so at most 3 duplicates can appear per spin.
# Hard-cap the inner loop at 3 — without this a mis-detection (e.g. a stuck/
# re-matched menu) let it handle 5+ in a real bug report. Reaching the cap
# means something misfired; the per-detection confidence log helps diagnose it.
MAX_DUP_CHAIN    = 3

SUPER_KEY    = "super_wheelspin"      # left-column tile, clicked to start a run
SKIP_KEY     = "wheelspin_skip"       # spin animation — Enter skips forward
COLLECT_KEY  = "wheelspin_collect"    # prize/result — Enter collects
TEMPLATE_KEY = "wheelspin_duplicate"  # the 3-option duplicate-reward menu


# ── Mouse click (SendInput) — used once to click the Super Wheelspin tile ──
class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class _MINPUT_UNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT), ("_pad", ctypes.c_byte * 28)]

class _MINPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _MINPUT_UNION)]

def _mouse_click(x: int, y: int, mon_left: int = 0, mon_top: int = 0,
                 post_wait: float = 0.5):
    """Left-click at frame-local (x, y), offset to the monitor's screen origin."""
    ctypes.windll.user32.SetCursorPos(int(x + mon_left), int(y + mon_top))
    time.sleep(0.1)
    for flag in (0x0002, 0x0004):   # LEFTDOWN, LEFTUP
        inp = _MINPUT(type=0, union=_MINPUT_UNION(mi=_MOUSEINPUT(
            dx=0, dy=0, mouseData=0, dwFlags=flag, time=0, dwExtraInfo=None)))
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_MINPUT))
        time.sleep(0.05)
    time.sleep(post_wait)


def run(cfg: dict, stop_event: threading.Event,
        log_cb, status_cb, max_loops: int = 0,
        warn_cb=None, section_cb=None):
    """
    Auto Spin Wheel loop.
    cfg: config dict
    stop_event: set to stop
    log_cb(msg) / status_cb(msg): log line / status bar
    max_loops: stop after this many spins (0 = unlimited)
    section_cb(msg): start a bounded log section; falls back to log_cb
    warn_cb: accepted for call-site parity; UNUSED — the duplicate check is
             time-boxed and a non-detection is its NORMAL outcome. The skip /
             collect stage waits surface their own one-time slow hint instead.
    """
    section       = section_cb or log_cb
    lang          = cfg.get("lang", "en")
    monitor_index = cfg.get("monitor_index", 1)

    # Always read settings fresh from config.json at start.
    import config as _cfg_mod
    _fresh   = _cfg_mod.load()
    post_kw  = _fresh.get("wheelspin_post_key_wait", 0.5)
    dup_mode = _fresh.get("wheelspin_dup_mode", "garage")
    res      = _fresh.get("wheelspin_resolution", "custom")
    tpl_lang = _cfg_mod.resolve_template_lang(_fresh)
    # Detection mode follows the template type (preset → default/OCR-confirm,
    # custom → pixel-only), same rule as race/mastery. See ScreenDetector.
    _fresh['detector_ocr_primary'] = (res != 'custom')

    def _thr(key):
        return _fresh.get(f"thresh_{key}", 0.60)

    current_w, current_h, mon_left, mon_top = get_monitor_dims(monitor_index)
    folder   = get_wheelspin_templates(res, tpl_lang)
    # Single-reference fallback for preset resolutions. Custom uses the user's
    # own capture.
    ref_folder = None
    prefer_ref = False
    if res != 'custom':
        ref_folder = get_wheelspin_templates(_cfg_mod.REFERENCE_RES, tpl_lang)
        prefer_ref = _fresh.get('template_prefer_reference', True)
    log_cb(f"  Templates: {tpl_lang} / {res}")
    detector = ScreenDetector(_fresh)

    def _load(key):
        img, scale, meta = load_template(folder, key, current_w, current_h,
                                         grayscale=True, ref_folder=ref_folder,
                                         prefer_ref=prefer_ref)
        box = meta.get("box")
        if box:
            detector.set_template_geometry(
                key, box, meta.get("screen_width", current_w),
                meta.get("screen_height", current_h))
        log_cb(_at("log_template_loaded", lang, key=key, scale=f"{scale:.2f}"))
        return img

    templates = {}
    for key in (SUPER_KEY, SKIP_KEY, COLLECT_KEY, TEMPLATE_KEY):
        try:
            templates[key] = _load(key)
        except FileNotFoundError:
            log_cb(_at("log_template_missing", lang, key=key))
            status_cb(_at("status_setup_incomplete", lang))
            return
    super_tpl, skip_tpl   = templates[SUPER_KEY], templates[SKIP_KEY]
    collect_tpl, dup_tpl  = templates[COLLECT_KEY], templates[TEMPLATE_KEY]

    def stop():
        return stop_event.is_set()

    def wait(seconds):
        """Stop-aware sleep so F9/Stop isn't blocked by the fixed waits."""
        end = time.time() + seconds
        while time.time() < end:
            if stop():
                return
            time.sleep(0.1)

    def announce(msg):
        log_cb(msg)
        status_cb(msg)

    def press(key, post_wait=None):
        key_press(key, post_wait=post_kw if post_wait is None else post_wait)

    def _detect(key, tpl, window_s):
        """TIME-BOXED detection: poll detect() for up to window_s seconds and
        return the MatchResult the instant it matches, else None. NOT wait_for
        (which is indefinite) — used where a None is a NORMAL outcome (no
        duplicate, or the Super Wheelspin tile not visible), never an error."""
        end = time.time() + window_s
        while time.time() < end:
            if stop():
                return None
            try:
                frame = grab_frame(monitor_index)
                r = detector.detect(frame, key, tpl, _thr(key), stable=False)
                if r.matched:
                    return r
            except Exception:
                pass
            time.sleep(0.15)
        return None

    def _wait_either(key_a, tpl_a, key_b, tpl_b):
        """Wait until EITHER template is on screen; return ('a'|'b', result),
        or (None, None) if stopped. After a collect the next event is always
        one of two screens — the duplicate menu (a) or the NEXT spin's skip
        prompt (b, the wheel auto-spun) — so we react to whichever appears
        first instead of blind-waiting a fixed window for the duplicate. The
        old fixed window delayed skip detection: by the time it decided "no
        duplicate", the auto-spun wheel had already passed the skip period.
        The two screens don't co-occur (a blocking menu means the wheel isn't
        spinning), so checking `a` first is a safe tiebreak. Indefinite
        (F9/Stop recovers) — one of the two always shows while spins remain."""
        while not stop():
            try:
                frame = grab_frame(monitor_index)
                ra = detector.detect(frame, key_a, tpl_a, _thr(key_a),
                                     stable=False)
                if ra.matched:
                    return ('a', ra)
                rb = detector.detect(frame, key_b, tpl_b, _thr(key_b),
                                     stable=False)
                if rb.matched:
                    return ('b', rb)
            except Exception:
                pass
            time.sleep(0.15)
        return (None, None)

    def _wait_gone(key, tpl, timeout=8.0):
        """Wait (bounded) until `key` is NO LONGER on screen. The next
        duplicate menu only appears AFTER the current one is fully dealt with,
        so we must let this menu close before re-checking — otherwise the
        still-visible menu (especially while the slower sell action is
        processing) gets re-counted as fresh duplicates (the real bug: 3
        'duplicates' off one menu before the sell even finished). Bounded
        timeout so a genuinely stuck menu can't hang the loop."""
        end = time.time() + timeout
        while time.time() < end:
            if stop():
                return
            try:
                frame = grab_frame(monitor_index)
                if not detector.detect(frame, key, tpl, _thr(key),
                                       stable=False).matched:
                    return
            except Exception:
                pass
            time.sleep(0.15)

    def _wait_stage(key, tpl, waiting_msg, label):
        """Wait until a spin STAGE that always occurs is on screen (the
        skip-able spin, the prize/collect screen), then return True. Gated on
        detection — the script acts only when the screen is actually present,
        never on a blind timer (fixes mis-timed presses). Waits indefinitely
        (F9/Stop recovers); an over-3s wait logs a one-time hint. Returns
        False if stopped."""
        announce(waiting_msg)
        def _warn(best):
            log_cb(_at("log_spin_stage_slow", lang) +
                   f" ({best.source}: {best.score:.0%})")
        res = detector.wait_for(
            frame_cb=lambda: grab_frame(monitor_index),
            key=key, template=tpl, threshold=_thr(key),
            stop_cb=stop, interval=0.2, on_warn=_warn)
        if res.matched:
            # Log the match + confidence (like race/mastery) so a misfire is
            # visible — a low % or a "full" source hints at a false match.
            log_cb(_at("log_detected", lang, label=label,
                       conf=f"{res.score:.0%}, {res.source}"))
        return res.matched

    if max_loops > 0:
        log_cb(_at("log_spin_started_count", lang, n=max_loops))
    else:
        log_cb(_at("log_spin_started", lang))
    if dup_mode == "sell":
        log_cb(_at("log_spin_sell_warn", lang))
    # Switch the game to English input only if it isn't already.
    if _fresh.get("auto_english_ime", True):
        force_english_ime()
        time.sleep(0.2)

    # ── Entry (ONCE): from the My Horizon menu, find the Super Wheelspin tile
    #    and click its centre. Clicking it starts the first spin and moves to
    #    the spin screen, which then persists. Every later spin auto-starts from
    #    the previous collect ("…and Spin Again"), so FAFE never presses to spin
    #    again — it just waits for each spin's skip/collect prompts. ──
    announce(_at("log_spin_select_super", lang))
    res_super = _detect(SUPER_KEY, super_tpl, SUPER_FIND_WINDOW)
    if res_super is None:
        if not stop():
            log_cb(_at("log_spin_super_not_found", lang))
        log_cb(_at("log_spin_stopped", lang))
        status_cb(_at("status_stopped", lang))
        return
    log_cb(_at("log_detected", lang, label=_at("spin_tpl_super", lang),
               conf=f"{res_super.score:.0%}, {res_super.source}"))
    _mouse_click(res_super.location[0], res_super.location[1],
                 mon_left, mon_top, post_kw)   # starts spin #1

    loop_count = 0
    while not stop():
        loop_count += 1
        section(f"-- {_at('spin_loop', lang)} #{loop_count}" +
                (f" / {max_loops}" if max_loops > 0 else "") + " --")

        # ── 1. Spin ───────────────────────────────────────────
        # The spin ALWAYS auto-starts — FAFE never presses to spin: spin #1
        # was started by the Super Wheelspin click, and every later spin by the
        # previous collect ("Collect Prize and Spin Again"). So we just wait for
        # the running spin's skip prompt. Pressing Enter here would land on an
        # already-spinning wheel and desync (the bug: after a duplicate was
        # dealt with the wheel auto-spun, but FAFE then pressed spin again).
        announce(_at("log_spin_spin", lang))
        if stop(): break

        # ── 2. Skip-forward — wait for the spin stage, then Enter ──
        if not _wait_stage(SKIP_KEY, skip_tpl, _at("log_spin_wait_skip", lang),
                           _at("spin_tpl_skip", lang)):
            break
        press('enter', post_wait=0.0)

        # ── 3. Collect — wait for the prize stage, then Enter ──
        # Detection of the collect prompt IS the gate (the prompt only renders
        # when the prize is ready), so press immediately — no blind grace.
        if not _wait_stage(COLLECT_KEY, collect_tpl,
                           _at("log_spin_wait_collect", lang),
                           _at("spin_tpl_collect", lang)):
            break
        announce(_at("log_spin_collect", lang))
        press('enter')
        if stop(): break

        # ── 4. Resolve duplicates (react to dup-menu OR next skip) ──
        # After collect, wait for whichever appears first: the duplicate menu
        # (handle it; the 2nd+ can stack, capped at MAX_DUP_CHAIN) or the next
        # spin's skip prompt (the wheel auto-spun → no more duplicates this
        # spin). Polling BOTH avoids a blind duplicate window that would delay
        # skip detection and miss the skip period (the reported bug).
        chain = 0
        while not stop():
            which, r = _wait_either(TEMPLATE_KEY, dup_tpl, SKIP_KEY, skip_tpl)
            if which != 'a':
                # 'b' = next spin's skip prompt (wheel rolled over, no more
                # duplicates) — the top-of-loop _wait_stage(skip) catches it;
                # or stopped.
                if which == 'b':
                    announce(_at("log_spin_no_dup", lang))
                break
            log_cb(_at("log_detected", lang, label=_at("spin_tpl_duplicate", lang),
                       conf=f"{r.score:.0%}, {r.source}"))
            chain += 1
            if dup_mode == "sell":
                # Sell = 3rd option: Down ×2 → Enter.
                announce(_at("log_spin_dup_sell", lang, n=chain))
                press('down')
                if stop(): break
                press('down')
                if stop(): break
                press('enter')
            else:
                # Garage = top option: Enter.
                announce(_at("log_spin_dup_garage", lang, n=chain))
                press('enter')
            if stop(): break
            if chain >= MAX_DUP_CHAIN:
                break
            # Let this menu close before re-polling, so it isn't re-counted
            # while the action (esp. the slower sell) is still processing.
            _wait_gone(TEMPLATE_KEY, dup_tpl)
        if stop(): break

        # ── 5. Count limit ────────────────────────────────────
        if max_loops > 0 and loop_count >= max_loops:
            log_cb(_at("log_spin_limit_reached", lang, n=max_loops))
            break

    log_cb(_at("log_spin_stopped", lang))
    status_cb(_at("status_stopped", lang))
