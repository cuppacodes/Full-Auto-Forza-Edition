# ============================================================
#  automation/wheelspin.py — Auto Spin Wheel automation logic
#  One loop = one wheelspin: spin → fast-forward → settle →
#  collect → handle any duplicate-reward menus.
#  Uses ONE detect-only template (wheelspin_duplicate) with a
#  TIME-BOXED check — NOT the indefinite race/mastery wait_for.
#  Output via log_cb / status_cb; stop via stop_event.
# ============================================================

import time
import threading

import config
from config import get_wheelspin_templates
from app_lang import t as _at
from capture import grab_frame, load_template, get_monitor_dims, force_english_ime
from detector import ScreenDetector
# Reuse the IME-safe (dual VK+scancode) key sender shared by Delete/Buy.
# wheelspin only presses 'enter' and 'down' (down is an extended VK there).
from delete_cars import key_press


# ── Tunable values (constants; some overridable via Settings) ──
FF_WAIT          = 1.0    # step 2: spin → fast-forward Enter
SETTLE_WAIT      = 5.0    # step 3: REQUIRED settle before collect (default;
                          #         overridden by the wheelspin_settle_wait setting)
DUP_CHECK_WINDOW = 2.0    # step 5: max time to look for the duplicate menu
# Safety cap on chained duplicates per spin. The game chains at most ~3, but if
# detection wrongly keeps matching (e.g. a menu is stuck open) this bounds the
# inner loop so it can never spin forever on one wheelspin.
MAX_DUP_CHAIN    = 5

TEMPLATE_KEY = "wheelspin_duplicate"


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
             time-boxed and a non-detection is the NORMAL outcome, so the 3s
             red "not detected" warning must NOT fire here.
    """
    section       = section_cb or log_cb
    lang          = cfg.get("lang", "en")
    monitor_index = cfg.get("monitor_index", 1)

    # Always read settings fresh from config.json at start.
    import config as _cfg_mod
    _fresh   = _cfg_mod.load()
    post_kw  = _fresh.get("wheelspin_post_key_wait", 0.5)
    settle   = max(0.0, float(_fresh.get("wheelspin_settle_wait", SETTLE_WAIT)))
    dup_mode = _fresh.get("wheelspin_dup_mode", "garage")
    res      = _fresh.get("wheelspin_resolution", "custom")
    tpl_lang = _cfg_mod.resolve_template_lang(_fresh)
    # Detection mode follows the template type (preset → default/OCR-confirm,
    # custom → pixel-only), same rule as race/mastery. See ScreenDetector.
    _fresh['detector_ocr_primary'] = (res != 'custom')
    threshold = _fresh.get(f"thresh_{TEMPLATE_KEY}", 0.60)

    # Load the single detect-only template.
    current_w, current_h, _, _ = get_monitor_dims(monitor_index)
    folder   = get_wheelspin_templates(res, tpl_lang)
    # Single-reference fallback for preset resolutions (no bundled wheelspin
    # defaults today, so this only matters once any are shipped). Custom uses
    # the user's own capture.
    ref_folder = None
    prefer_ref = False
    if res != 'custom':
        ref_folder = get_wheelspin_templates(_cfg_mod.REFERENCE_RES, tpl_lang)
        prefer_ref = _fresh.get('template_prefer_reference', True)
    log_cb(f"  Templates: {tpl_lang} / {res}")
    detector = ScreenDetector(_fresh)
    try:
        template, scale, meta = load_template(folder, TEMPLATE_KEY,
                                        current_w, current_h, grayscale=True,
                                        ref_folder=ref_folder, prefer_ref=prefer_ref)
        _box = meta.get("box")
        if _box:
            detector.set_template_geometry(
                TEMPLATE_KEY, _box, meta.get("screen_width", current_w),
                meta.get("screen_height", current_h))
        log_cb(_at("log_template_loaded", lang, key=TEMPLATE_KEY,
                   scale=f"{scale:.2f}"))
    except FileNotFoundError:
        log_cb(_at("log_template_missing", lang, key=TEMPLATE_KEY))
        status_cb(_at("status_setup_incomplete", lang))
        return

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

    def _detect_once(window_s: float) -> bool:
        """TIME-BOXED yes/no detection of the duplicate menu.

        Polls for up to window_s seconds, returning True the instant it matches
        and False if the window elapses. This is deliberately NOT the
        race/mastery wait_for (which waits indefinitely): a normal, non-duplicate
        spin has no menu and MUST fall through after the window — the timeout is
        the loop's natural "the wheel has rolled over / no more duplicates"
        signal, not an error. No warning is emitted on timeout.
        """
        end = time.time() + window_s
        while time.time() < end:
            if stop():
                return False
            try:
                frame = grab_frame(monitor_index)
                r = detector.detect(frame, TEMPLATE_KEY, template,
                                    threshold, stable=False)
                if r.matched:
                    return True
            except Exception:
                pass
            time.sleep(0.15)
        return False

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

    loop_count = 0
    while not stop():
        loop_count += 1
        section(f"-- {_at('spin_loop', lang)} #{loop_count}" +
                (f" / {max_loops}" if max_loops > 0 else "") + " --")

        # ── 1. Spin ───────────────────────────────────────────
        # post_wait=0.0: the gap to the fast-forward Enter is the explicit
        # FF_WAIT below, not stacked on top of the key-pacing wait.
        announce(_at("log_spin_spin", lang))
        press('enter', post_wait=0.0)
        if stop(): break

        # ── 2. Fast-forward the spin animation ────────────────
        wait(FF_WAIT)
        if stop(): break
        press('enter', post_wait=0.0)   # gap to collect = the SETTLE_WAIT below

        # ── 3. Settle (REQUIRED — the result must land even after
        #       fast-forward, before collect) ──────────────────
        announce(_at("log_spin_settle", lang))
        wait(settle)
        if stop(): break

        # ── 4. Collect the reward ─────────────────────────────
        announce(_at("log_spin_collect", lang))
        press('enter')
        if stop(): break

        # ── 5. Duplicate-handling inner loop ──────────────────
        # Up to MAX_DUP_CHAIN duplicate menus may chain. The menu cursor resets
        # to the top option each time, so the down-count is constant.
        chain = 0
        while not stop():
            if not _detect_once(DUP_CHECK_WINDOW):
                # No (more) duplicate within the window → wheel is already
                # spinning again. End this spin's inner loop.
                announce(_at("log_spin_no_dup", lang))
                break
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
            if chain >= MAX_DUP_CHAIN:
                break
        if stop(): break

        # Failure mode (documented): if the duplicate template never matches
        # (mismatch / threshold too high), a duplicate menu may be left open and
        # the next spin's Enter lands on it. The SETTLE before collect bounds
        # most of this; raising thresh sensitivity / recapturing fixes it.

        # ── 6. Count limit ────────────────────────────────────
        if max_loops > 0 and loop_count >= max_loops:
            log_cb(_at("log_spin_limit_reached", lang, n=max_loops))
            break

    log_cb(_at("log_spin_stopped", lang))
    status_cb(_at("status_stopped", lang))
