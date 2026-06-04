# ============================================================
#  config.py — Central configuration and path management
# ============================================================

import os
import mss
import sys
import json
import ctypes

# ── Base path (works both frozen exe and dev) ────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Flat structure — config.py sits alongside forza_app.py
    BASE_DIR = os.path.dirname(os.path.abspath(
        sys.argv[0] if '__file__' not in dir() else __file__))
    # If we're inside an app/ subfolder, go up one level
    if os.path.basename(BASE_DIR).lower() == 'app':
        BASE_DIR = os.path.dirname(BASE_DIR)

CONFIG_FILE       = os.path.join(BASE_DIR, "config.json")
TEMPLATES_DIR     = os.path.join(BASE_DIR, "templates")

RESOLUTION_SETS = ["1080p", "1440p", "2160p", "custom"]

# ── Template languages ───────────────────────────────────────
# Templates are organised by the language of the GAME's on-screen menus (NOT
# the app UI) — the captured images contain that text, so the set must match
# what's rendered in-game. Layout: templates/<lang>/<category>/<res>/ plus
# templates/<lang>/examples/.
#   cht = Traditional Chinese · chs = Simplified Chinese · en = English
TEMPLATE_LANGS = ["cht", "chs", "en"]
DEFAULT_TEMPLATE_LANG = "cht"

# Default game-template language per app-UI language (used when the
# `template_lang` setting is "auto").
_APP_LANG_TO_TPL = {"zh-tw": "cht", "zh-cn": "chs", "en": "en"}


def resolve_template_lang(cfg: dict) -> str:
    """Which game-template language set to use.

    `template_lang` config: "auto" (follow the app UI language) or an explicit
    cht / chs / en. Defaults to auto."""
    val = str(cfg.get("template_lang", "auto") or "auto").lower()
    if val in TEMPLATE_LANGS:
        return val
    return _APP_LANG_TO_TPL.get(cfg.get("lang", "zh-tw"), DEFAULT_TEMPLATE_LANG)


def _lang_dir(lang: str) -> str:
    return os.path.join(TEMPLATES_DIR,
                        lang if lang in TEMPLATE_LANGS else DEFAULT_TEMPLATE_LANG)


def get_race_templates(res: str = "custom",
                       lang: str = DEFAULT_TEMPLATE_LANG) -> str:
    path = os.path.join(_lang_dir(lang), "race", res)
    os.makedirs(path, exist_ok=True)
    return path


def get_mastery_templates(res: str = "custom",
                          lang: str = DEFAULT_TEMPLATE_LANG) -> str:
    path = os.path.join(_lang_dir(lang), "mastery_full", res)
    os.makedirs(path, exist_ok=True)
    return path


def get_nodes_file(res: str = "custom",
                   lang: str = DEFAULT_TEMPLATE_LANG) -> str:
    return os.path.join(get_mastery_templates(res, lang), "mastery_nodes.json")


def get_examples_dir(lang: str = DEFAULT_TEMPLATE_LANG) -> str:
    path = os.path.join(_lang_dir(lang), "examples")
    os.makedirs(path, exist_ok=True)
    return path


def _migrate_flat_templates():
    """Move any pre-language flat layout (templates/{race,mastery_full,examples})
    into templates/cht/, preserving the user's custom captures. The old presets
    were all Traditional Chinese, so cht is the correct destination. Merges
    rather than overwrites (so updater-installed cht presets aren't clobbered),
    then removes the emptied old tree. Idempotent."""
    import shutil
    cht = _lang_dir("cht")
    for sub in ("race", "mastery_full", "examples"):
        old = os.path.join(TEMPLATES_DIR, sub)
        if not os.path.isdir(old):
            continue
        new = os.path.join(cht, sub)
        for root, _dirs, files in os.walk(old):
            rel = os.path.relpath(root, old)
            dst_root = new if rel == "." else os.path.join(new, rel)
            os.makedirs(dst_root, exist_ok=True)
            for fn in files:
                dst_f = os.path.join(dst_root, fn)
                if not os.path.exists(dst_f):
                    try:
                        shutil.move(os.path.join(root, fn), dst_f)
                    except Exception:
                        pass
        try:
            shutil.rmtree(old)
        except Exception:
            pass


# Migrate any old flat layout, THEN ensure the per-language tree exists.
_migrate_flat_templates()
for _lang in TEMPLATE_LANGS:
    for _mode in ("race", "mastery_full"):
        for _res in RESOLUTION_SETS:
            os.makedirs(os.path.join(TEMPLATES_DIR, _lang, _mode, _res),
                        exist_ok=True)
    os.makedirs(os.path.join(TEMPLATES_DIR, _lang, "examples"), exist_ok=True)

# ── Defaults ─────────────────────────────────────────────────
def _get_primary_monitor_index() -> int:
    """Return the mss index of the primary monitor (left=0, top=0)."""
    try:
        with mss.mss() as sct:
            for i, m in enumerate(sct.monitors[1:], start=1):
                if m["left"] == 0 and m["top"] == 0:
                    return i
    except Exception:
        pass
    return 1


DEFAULTS = {
    "lang":              "en",
    # First-run language picker gate. DEFAULTS=True so existing users (whose
    # config.json predates this key) are back-filled True and never see the
    # picker. The SHIPPED config.json sets it false, so a fresh download shows
    # the picker once, then sets it True.
    "lang_chosen":       True,
    "theme":             "system",
    "toggle_key":        "f9",
    "capture_key":       "caps lock",
    "report_key":        "f12",
    "overlay_key":       "f10",
    "monitor_index":     _get_primary_monitor_index(),
    "race_resolution":    "1080p",
    "mastery_resolution": "1080p",
    # Game-menu language for templates: "auto" (follow app UI lang) / cht / chs / en
    "template_lang":      "auto",
    # Race settings
    "race_threshold":    0.60,
    # Per-template thresholds
    "thresh_start_menu":           0.60,
    "thresh_racing":               0.60,
    "thresh_restart_menu":         0.60,
    "thresh_confirm":              0.60,
    "thresh_mastery_ride_car":     0.60,
    "thresh_mastery_esc_hint":     0.60,
    "thresh_mastery_upgrade_item": 0.60,
    "thresh_mastery_mastery_item": 0.60,
    "thresh_mastery_anchor":       0.60,
    "thresh_mastery_my_cars":      0.60,
    "thresh_mastery_sort_recent":  0.60,
    "race_check_interval":    0.5,
    "race_post_key_wait":     0.75,
    # Mastery settings
    "mastery_threshold":      0.85,
    "mastery_post_click_wait":0.8,
    "mastery_post_key_wait":  1.2,
    "mastery_check_interval": 0.5,
    "mastery_node_click_wait":0.8,
    "mastery_start_loop":     1,
    # Buy / Delete settings
    "buy_post_key_wait":      0.5,
    "delete_post_key_wait":   0.5,
    # UI / behavior toggles
    "ui_scale":               "auto",
    "nodes_aspect_fix":       True,
    "auto_english_ime":       True,
    "overlay_enabled":        False,
    # Read-only version check on startup (no download — opens the releases page
    # if a newer version exists). Set false for a fully offline build that makes
    # zero network requests (e.g. to satisfy Nexus's no-internet policy).
    "update_check":           True,
}


def load() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            # Unreadable/corrupt — fall back to defaults but DON'T overwrite the
            # file (it may be recoverable / the user's).
            return dict(DEFAULTS)
        # Fill in any missing keys with defaults, and persist them back so the
        # file stays complete + self-documenting across app updates. The updater
        # leaves config.json untouched, so without this, keys added in a new
        # version (e.g. auto_english_ime) would never appear in an existing
        # user's file for them to see or toggle.
        added = False
        for k, v in DEFAULTS.items():
            if k not in data:
                data[k] = v
                added = True
        # Validate monitor index against available monitors (runtime-only;
        # doesn't itself trigger a rewrite).
        try:
            with mss.mss() as sct:
                n = len(sct.monitors) - 1
            if data['monitor_index'] > n or data['monitor_index'] < 1:
                data['monitor_index'] = _get_primary_monitor_index()
        except Exception:
            pass
        if added:
            save(data)
        return data
    # No config yet — create one from defaults so the file exists + is complete.
    data = dict(DEFAULTS)
    save(data)
    return data


def save(data: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[config] Failed to save: {e}")


# ── DPI / resolution scaling ─────────────────────────────────
# 1080p is the baseline. We scale UI elements proportionally.

def get_scale_factor() -> float:
    """
    Returns a scale factor relative to 1080p height.
    On a 1440p screen this returns ~1.33, on 4K ~2.0.
    Clamped between 0.8 and 2.5 to avoid extreme sizes.
    """
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        h = user32.GetSystemMetrics(1)   # screen height in physical pixels
        factor = h / 1080.0
        return max(0.8, min(2.5, factor))
    except Exception:
        return 1.0


def s(px: int) -> int:
    """Scale a pixel value relative to 1080p baseline."""
    return int(px * get_scale_factor())


# UI scale options shown in Settings. "auto" = derive from screen resolution
# (get_scale_factor); the rest are explicit multipliers stored as e.g. "150%".
UI_SCALE_OPTIONS = ["auto", "100%", "125%", "150%", "175%", "200%", "250%"]


def resolve_ui_scale(cfg: dict) -> float:
    """Resolve the saved `ui_scale` setting to a CustomTkinter scaling factor.

    Accepts "auto" (resolution-derived), a percentage string like "150%", or a
    raw float. Clamped to a sane range so a stale/bad value can't make the UI
    unusable.
    """
    val = cfg.get("ui_scale", "auto")
    if isinstance(val, (int, float)):
        return max(0.8, min(2.5, float(val)))
    v = str(val).strip().lower()
    if v in ("", "auto"):
        return get_scale_factor()
    try:
        n = float(v.rstrip("%"))
        if n > 5:           # given as a percentage (e.g. 150) not a ratio
            n /= 100.0
        return max(0.8, min(2.5, n))
    except ValueError:
        return get_scale_factor()
