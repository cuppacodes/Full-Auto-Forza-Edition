# ============================================================
#  automation/wheelspin.py — Auto Spin Wheel automation logic
#  ENTRY: from the My Horizon menu, detect the Super Wheelspin tile
#  and click it (starts the first spin; the spin screen then persists).
#  Each spin is DETECTION-GATED, not timed. FAFE never presses to spin
#  (the entry click starts spin #1; every later spin auto-starts from the
#  previous collect's "…and Spin Again"). A Super Wheelspin has 3 wheels and
#  ONE Enter collects all three prizes at once, so per spin:
#    1. BEST-EFFORT skip: if the brief "Skip" prompt shows, Enter to fast-
#       forward the reveal (it lands on the collect prompt). Optional — if the
#       skip template is absent or the prompt is missed, we just wait for the
#       collect prompt as normal, so skip can only save time, never desync.
#    2. wait for the collect prompt → Enter (collects all 3 prizes)
#    3. duplicate-handling inner loop (a dup menu per duplicate car, up to 3,
#       OR the next spin's collect prompt once none are left)
#  Stage waits use detector.wait_for (wait until the screen is actually
#  present — F9/Stop recovers). Skip is viable now that ROI-only detection is
#  ~23ms (fast enough to catch the brief skip window); the older skip attempt
#  was dropped because ~680ms full-screen detection couldn't keep up.
#  Output via log_cb / status_cb; stop via stop_event.
# ============================================================

import time
import threading

import config
from config import get_wheelspin_templates
from app_lang import t as _at
from capture import (grab_frame, load_template, get_monitor_dims,
                     force_english_ime, mouse_click)
from detector import ScreenDetector
# Reuse the IME-safe (dual VK+scancode) key sender shared by Delete/Buy.
# wheelspin only presses 'enter' and 'down' (down is an extended VK there).
from delete_cars import key_press


# ── Tunable values (constants; some overridable via Settings) ──
SUPER_FIND_WINDOW = 12.0  # max time to find the Super Wheelspin tile at start
MH_TAB_WINDOW     = 8.0   # max time to find the My Horizon tab (menu-start entry)
# A Super Wheelspin has 3 wheels, so at most 3 duplicates can appear per spin.
# Hard-cap the inner loop at 3 — without this a mis-detection (e.g. a stuck/
# re-matched menu) let it handle 5+ in a real bug report. Reaching the cap
# means something misfired; the per-detection confidence log helps diagnose it.
MAX_DUP_CHAIN    = 3

MH_TAB_KEY   = "my_horizon_tab"       # top-nav tab, clicked to start from main menu
SUPER_KEY    = "super_wheelspin"      # left-column tile, clicked to start a run
SKIP_KEY     = "wheelspin_skip"       # reveal "Skip" prompt — Enter fast-forwards
COLLECT_KEY  = "wheelspin_collect"    # prize/result — Enter collects
TEMPLATE_KEY = "wheelspin_duplicate"  # the 3-option duplicate-reward menu
# Skip is BEST-EFFORT: loaded only if the template exists; a missing/missed skip
# falls back to waiting for the collect prompt (no desync, just no speed-up).


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
    for key in (SUPER_KEY, COLLECT_KEY, TEMPLATE_KEY):
        try:
            templates[key] = _load(key)
        except FileNotFoundError:
            log_cb(_at("log_template_missing", lang, key=key))
            status_cb(_at("status_setup_incomplete", lang))
            return
    super_tpl             = templates[SUPER_KEY]
    collect_tpl, dup_tpl  = templates[COLLECT_KEY], templates[TEMPLATE_KEY]
    # Skip is best-effort: load it if present, else disable skip-forward (the
    # collect wait alone still works — just no speed-up). Never aborts the run.
    try:
        skip_tpl = _load(SKIP_KEY)
    except FileNotFoundError:
        skip_tpl = None
        log_cb(_at("log_spin_skip_off", lang))
    # My Horizon tab is best-effort too: present → the run can START from the
    # main menu (click the tab → My Horizon menu); absent → assume we're already
    # on the My Horizon menu and go straight to the Super Wheelspin tile.
    try:
        mh_tab_tpl = _load(MH_TAB_KEY)
    except FileNotFoundError:
        mh_tab_tpl = None
        log_cb(_at("log_spin_mh_tab_off", lang))

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
        """Wait until EITHER template is on screen; return ('a'|'b', result), or
        (None, None) if stopped. Used after a duplicate is handled: the next
        screen is either the NEXT duplicate menu (a) or the next spin's collect
        prompt (b). Indefinite (F9/Stop recovers). One grab serves both checks;
        `a` is checked first as the tiebreak."""
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
            time.sleep(0.10)
        return (None, None)

    def _wait_dup_or_next():
        """Wait until a duplicate menu OR the next spin appears; return
        ('dup', result) or ('next', result), or (None, None) if stopped. Used
        after handling a duplicate. The "next spin" is detected by its SKIP
        prompt (when skip is enabled) OR its collect prompt — watching skip too
        means we break the instant the next spin starts, so its skip window
        isn't waited past (otherwise the next spin's reveal would play out fully
        and skip would never apply beyond the first spin). Indefinite; one grab
        serves all checks; dup is checked first as the tiebreak."""
        while not stop():
            try:
                frame = grab_frame(monitor_index)
                dr = detector.detect(frame, TEMPLATE_KEY, dup_tpl,
                                     _thr(TEMPLATE_KEY), stable=False)
                if dr.matched:
                    return ('dup', dr)
                if skip_tpl is not None:
                    skr = detector.detect(frame, SKIP_KEY, skip_tpl,
                                          _thr(SKIP_KEY), stable=False)
                    if skr.matched:
                        return ('next', skr)
                cr = detector.detect(frame, COLLECT_KEY, collect_tpl,
                                     _thr(COLLECT_KEY), stable=False)
                if cr.matched:
                    return ('next', cr)
            except Exception:
                pass
            time.sleep(0.10)
        return (None, None)

    def _wait_dup_or_menu():
        """Last-loop variant of _wait_dup_or_next. After the FINAL spin's Esc-
        collect, duplicate menus still appear, but no next spin follows — we
        return to the My Horizon menu instead. So watch for a duplicate menu OR
        the Super Wheelspin tile (= back on the My Horizon menu). Returns
        ('dup'|'menu', result), or (None, None) if stopped. dup is checked first
        as the tiebreak so a duplicate dialog overlaying the tile counts as a
        duplicate, never a premature 'menu'."""
        while not stop():
            try:
                frame = grab_frame(monitor_index)
                dr = detector.detect(frame, TEMPLATE_KEY, dup_tpl,
                                     _thr(TEMPLATE_KEY), stable=False)
                if dr.matched:
                    return ('dup', dr)
                mr = detector.detect(frame, SUPER_KEY, super_tpl,
                                     _thr(SUPER_KEY), stable=False)
                if mr.matched:
                    return ('menu', mr)
            except Exception:
                pass
            time.sleep(0.10)
        return (None, None)

    def _wait_gone(key, tpl, timeout=8.0):
        """Wait (bounded) until `key` is NO LONGER on screen. Used for the
        COLLECT prompt after pressing it, so the lingering just-pressed prompt
        isn't re-detected and double-pressed. Safe for collect because the NEXT
        collect is a whole spin away (seconds), so this can't overshoot onto it.

        NOTE: do NOT use this between consecutive DUPLICATE menus — they're only
        ~0.23s apart, which is shorter than the post-key wait the action already
        did, so by the time this ran the next menu would already be up and it
        would sit waiting for THAT menu to vanish until timeout (stalling every
        stacked duplicate). Bounded timeout so a genuinely stuck screen can't
        hang the loop."""
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
        t0 = time.time()
        res = detector.wait_for(
            frame_cb=lambda: grab_frame(monitor_index),
            key=key, template=tpl, threshold=_thr(key),
            stop_cb=stop, interval=0.2, on_warn=_warn)
        if res.matched:
            # Detailed diagnostic line: what was detected, confidence, source,
            # and how long the wait took (the elapsed time exposes detection
            # latency / how long the on-screen stage took to appear).
            log_cb(_at("log_spin_detected", lang, label=label,
                       conf=f"{res.score:.0%}, {res.source}",
                       secs=f"{time.time() - t0:.1f}"))
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

    # ── Optional menu-start (ONCE): if the My Horizon tab template is captured,
    #    click it first so the run can START from the main menu (the chaining
    #    entry point). The tab is in the fixed top nav, visible from any menu, so
    #    this also works if we're already on My Horizon. Best-effort: if the
    #    template is absent or the tab isn't found, we fall straight through to
    #    the Super Wheelspin tile detection (which assumes we're already on the
    #    My Horizon menu and aborts if not). ──
    if mh_tab_tpl is not None and not stop():
        announce(_at("log_spin_select_mh_tab", lang))
        _t_mh = time.time()
        res_mh = _detect(MH_TAB_KEY, mh_tab_tpl, MH_TAB_WINDOW)
        if res_mh is not None:
            log_cb(_at("log_spin_detected", lang,
                       label=_at("spin_tpl_my_horizon", lang),
                       conf=f"{res_mh.score:.0%}, {res_mh.source}",
                       secs=f"{time.time() - _t_mh:.1f}"))
            mouse_click(res_mh.location[0], res_mh.location[1],
                        mon_left, mon_top, post_kw)   # → My Horizon menu

    # ── Entry (ONCE): from the My Horizon menu, find the Super Wheelspin tile
    #    and click its centre. Clicking it starts the first spin and moves to
    #    the spin screen, which then persists. Every later spin auto-starts from
    #    the previous collect ("…and Spin Again"), so FAFE never presses to spin
    #    again — it just waits for each spin's skip/collect prompts. ──
    announce(_at("log_spin_select_super", lang))
    _t_super = time.time()
    res_super = _detect(SUPER_KEY, super_tpl, SUPER_FIND_WINDOW)
    if res_super is None:
        if not stop():
            log_cb(_at("log_spin_super_not_found", lang))
        log_cb(_at("log_spin_stopped", lang))
        status_cb(_at("status_stopped", lang))
        return
    log_cb(_at("log_spin_detected", lang, label=_at("spin_tpl_super", lang),
               conf=f"{res_super.score:.0%}, {res_super.source}",
               secs=f"{time.time() - _t_super:.1f}"))
    mouse_click(res_super.location[0], res_super.location[1],
                mon_left, mon_top, post_kw)   # starts spin #1

    loop_count = 0
    while not stop():
        loop_count += 1
        section(f"-- {_at('spin_loop', lang)} #{loop_count}" +
                (f" / {max_loops}" if max_loops > 0 else "") + " --")
        # Last counted spin: collect with Esc (collects all 3 prizes AND exits
        # to the My Horizon menu) instead of Enter (which would auto-start
        # another spin). Duplicates STILL appear after the Esc, so they're
        # handled the same way — but the "done" signal is the My Horizon menu
        # reappearing, not the next spin. Unlimited runs (max_loops == 0) never
        # hit this; they stop via F9.
        is_last = max_loops > 0 and loop_count >= max_loops

        # ── 1. (Best-effort skip) then collect ────────────────
        # The spin ALWAYS auto-starts — FAFE never presses to spin (spin #1 was
        # the Super Wheelspin click, every later spin the previous collect's
        # "…and Spin Again"). A Super Wheelspin has 3 wheels and ONE Enter
        # collects all three at once, so collect is pressed exactly ONCE per spin.
        #
        # Best-effort skip: the brief "Skip" prompt appears at the START of the
        # reveal and the "Collect Prize and Spin Again" prompt at the END, so
        # they're never on screen together. We wait for whichever shows first:
        #   • skip first  → Enter (fast-forward; lands on the collect prompt) →
        #                   wait for the collect prompt
        #   • collect first (skip missed / no skip template) → just collect
        # A missed/flaky skip therefore only costs the reveal time — it can never
        # press the wrong prompt or desync.
        if stop(): break
        if skip_tpl is not None:
            _t0 = time.time()
            announce(_at("log_spin_wait_skip", lang))
            which, sr = _wait_either(SKIP_KEY, skip_tpl, COLLECT_KEY, collect_tpl)
            if which is None:
                break
            _el = f"{time.time() - _t0:.1f}"
            if which == 'a':                       # Skip prompt
                log_cb(_at("log_spin_detected", lang,
                           label=_at("spin_tpl_skip", lang),
                           conf=f"{sr.score:.0%}, {sr.source}", secs=_el))
                announce(_at("log_spin_skip", lang))
                press('enter', post_wait=0.0)      # fast-forward → collect prompt
                if stop(): break
                # No _wait_gone(skip) here: the next wait is for the COLLECT
                # prompt, not skip, so a lingering "Skip" can't cause a re-press.
                # The collect prompt is often already up under the fading skip
                # prompt, so waiting for skip to vanish first is pure dead time —
                # go straight to detecting collect (caught the instant it shows).
                if not _wait_stage(COLLECT_KEY, collect_tpl,
                                   _at("log_spin_wait_collect", lang),
                                   _at("spin_tpl_collect", lang)):
                    break
            else:                                  # 'b' = collect already up
                log_cb(_at("log_spin_detected", lang,
                           label=_at("spin_tpl_collect", lang),
                           conf=f"{sr.score:.0%}, {sr.source}", secs=_el))
        else:
            if not _wait_stage(COLLECT_KEY, collect_tpl,
                               _at("log_spin_wait_collect", lang),
                               _at("spin_tpl_collect", lang)):
                break
        if is_last:
            announce(_at("log_spin_end_esc", lang))
            press('escape', post_wait=0.0)         # collect all 3 + exit to menu
        else:
            announce(_at("log_spin_collect", lang))
            press('enter', post_wait=0.0)          # _wait_gone below is the guard
        if stop(): break
        # Let the collect prompt dismiss before watching for the next screen, so
        # the prompt we just pressed isn't re-detected (which would fire a second
        # collect and desync). Bounded inside _wait_gone. This wait is the game's
        # collecting animation — log how long it takes so any post-collect lag is
        # visible (the duplicate menu can't be detected until this clears).
        _t_clear = time.time()
        _wait_gone(COLLECT_KEY, collect_tpl)
        log_cb(_at("log_spin_collect_cleared", lang,
                   secs=f"{time.time() - _t_clear:.1f}"))
        if stop(): break

        # ── 2. Resolve duplicates — detect-after-settle ──
        # After the collect, 0–3 duplicate menus appear in sequence (one per
        # duplicate car). We detect a duplicate, handle it, then the confirming
        # key's post-wait (0.5s, > the ~0.23s it takes the menu to advance to the
        # next car / dismiss) settles before we look again — so the menu has
        # MOVED ON to the next duplicate (or to the spin) before the next check,
        # and the one we just handled can't be re-counted.
        #
        # NOT rising-edge: the "Car Already Owned" header is so stable it stays
        # detected continuously from one duplicate straight into the next (no
        # absent gap), so edge-counting would never see dup #2 and would get
        # stuck. NOT _wait_gone: the header never goes absent between dupes, so
        # it would just time out. The header template is precise (it won't false-
        # match the spinning wheel) and reliable, which is exactly what makes the
        # simple settle-then-detect correct — no re-count, no missed menu.
        #
        # "No more duplicates" is signalled by the NEXT spin starting — detected
        # via its skip OR collect prompt (`_wait_dup_or_next`). We break on the
        # skip prompt (not just collect) so the next spin's skip window isn't
        # waited past; the top-of-loop skip step then catches it.
        chain = 0
        while not stop():
            announce(_at("log_spin_wait_dup", lang))
            _t_dup = time.time()
            # Last spin ended with Esc → no next spin; the "done" signal is the
            # My Horizon menu (Super Wheelspin tile) reappearing. Otherwise the
            # next spin's skip/collect prompt signals "no more duplicates".
            which, r = _wait_dup_or_menu() if is_last else _wait_dup_or_next()
            _el = f"{time.time() - _t_dup:.1f}"
            if which != 'dup':
                # 'next'  = next spin's skip/collect prompt (top-of-loop presses it)
                # 'menu'  = back on the My Horizon menu (last spin done)
                # None    = stopped
                if which == 'next':
                    log_cb(_at("log_spin_no_dup", lang, secs=_el))
                elif which == 'menu':
                    log_cb(_at("log_spin_back_menu", lang, secs=_el))
                break
            log_cb(_at("log_spin_detected", lang,
                       label=_at("spin_tpl_duplicate", lang),
                       conf=f"{r.score:.0%}, {r.source}", secs=_el))
            chain += 1
            if dup_mode == "sell":
                # Sell = 3rd option: Down ×2 → Enter. The Enter's post-key wait
                # is the settle that lets the menu advance before the next check.
                announce(_at("log_spin_dup_sell", lang, n=chain))
                press('down')
                if stop(): break
                press('down')
                if stop(): break
                press('enter')
            else:
                # Garage = top option: Enter (+ its post-key settle).
                announce(_at("log_spin_dup_garage", lang, n=chain))
                press('enter')
            if stop(): break
            if chain >= MAX_DUP_CHAIN:
                break
        if stop(): break

        # ── 3. Count limit ────────────────────────────────────
        # is_last already drove the Esc-collect + return-to-menu above, so we
        # end here on the My Horizon menu (the chaining hand-off point).
        if is_last:
            log_cb(_at("log_spin_limit_reached", lang, n=max_loops))
            break

    log_cb(_at("log_spin_stopped", lang))
    status_cb(_at("status_stopped", lang))
