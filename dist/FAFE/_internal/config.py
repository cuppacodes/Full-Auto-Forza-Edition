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
RACE_TEMPLATES_BASE    = os.path.join(TEMPLATES_DIR, "race")
MASTERY_FULL_BASE      = os.path.join(TEMPLATES_DIR, "mastery_full")
EXAMPLES_DIR           = os.path.join(TEMPLATES_DIR, "examples")

RESOLUTION_SETS = ["1080p", "1440p", "2160p", "custom"]


def get_race_templates(res: str = "custom") -> str:
    path = os.path.join(RACE_TEMPLATES_BASE, res)
    os.makedirs(path, exist_ok=True)
    return path


def get_mastery_templates(res: str = "custom") -> str:
    path = os.path.join(MASTERY_FULL_BASE, res)
    os.makedirs(path, exist_ok=True)
    return path


def get_nodes_file(res: str = "custom") -> str:
    return os.path.join(get_mastery_templates(res), "mastery_nodes.json")


# Ensure all resolution subfolders exist
for _mode in ["race", "mastery_full"]:
    for _res in RESOLUTION_SETS:
        os.makedirs(os.path.join(TEMPLATES_DIR, _mode, _res), exist_ok=True)
os.makedirs(EXAMPLES_DIR, exist_ok=True)

# Ensure template folders exist

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
    "lang":              "zh-tw",
    "theme":             "system",
    "toggle_key":        "f9",
    "capture_key":       "caps lock",
    "monitor_index":     _get_primary_monitor_index(),
    "race_resolution":    "1080p",
    "mastery_resolution": "1080p",
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
    "race_post_key_wait":     1.5,
    # Mastery settings
    "mastery_threshold":      0.85,
    "mastery_post_click_wait":0.8,
    "mastery_post_key_wait":  1.2,
}


def load() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            # Fill in any missing keys with defaults
            for k, v in DEFAULTS.items():
                data.setdefault(k, v)
            # Validate monitor index against available monitors
            try:
                with mss.mss() as sct:
                    n = len(sct.monitors) - 1
                if data['monitor_index'] > n or data['monitor_index'] < 1:
                    data['monitor_index'] = _get_primary_monitor_index()
            except Exception:
                pass
            return data
        except Exception:
            pass
    return dict(DEFAULTS)


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
