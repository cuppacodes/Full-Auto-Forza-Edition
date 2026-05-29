# ============================================================
#  theme.py — Central design tokens for FAFE.
#
#  Single source of truth for fonts, spacing, semantic colors,
#  icons, and accent presets.  Import from here instead of
#  hardcoding font/color/padding values throughout the app.
# ============================================================


# ── Typography ────────────────────────────────────────────────
# All fonts use Segoe UI for Windows native look + readability.

TITLE_FONT  = ("Segoe UI", 20, "bold")    # App title
H2_FONT     = ("Segoe UI", 16, "bold")    # Section headers
BODY_FONT   = ("Segoe UI", 13, "normal")  # Descriptions / paragraph text
LABEL_FONT  = ("Segoe UI", 12, "normal")  # Setting labels
HINT_FONT   = ("Segoe UI", 11, "normal")  # Captions / sub-text
BUTTON_FONT = ("Segoe UI", 13, "bold")    # Primary action buttons
VALUE_FONT  = ("Segoe UI", 11, "normal")  # Slider value readouts
ICON_FONT   = ("Segoe UI", 16, "normal")  # ⚙ etc. — chunky icon


# ── Spacing (base unit: 8 px) ─────────────────────────────────

PAD_TIGHT   = 4   # Cramped — only when two things must hug
PAD_INLINE  = 8   # Default between inline widgets
PAD_SECTION = 12  # Within a logical section
PAD_LARGE   = 16  # Between sections
PAD_MAJOR   = 24  # Top-level panel padding


# ── Semantic colors (Modern muted palette) ────────────────────

START_FG    = "#10B981"  # Emerald 500
START_HOVER = "#059669"  # Emerald 600
STOP_FG     = "#EF4444"  # Red 500
STOP_HOVER  = "#DC2626"  # Red 600

# Status text colors
STATUS_RUNNING = "#10B981"
STATUS_WARN    = "#F59E0B"
STATUS_IDLE    = ("gray50", "gray60")


# ── Icons (always followed by a double space for breathing room) ──

ICON_START = "▶  "
ICON_STOP  = "■  "
ICON_BACK  = "←  "


# ── Accent presets (user-pickable in Settings → Appearance) ───
# (display_name -> (fg, hover))

ACCENT_PRESETS: dict[str, tuple[str, str]] = {
    "Blue":    ("#3B82F6", "#2563EB"),
    "Indigo":  ("#6366F1", "#4F46E5"),
    "Purple":  ("#8B5CF6", "#7C3AED"),
    "Teal":    ("#14B8A6", "#0D9488"),
    "Emerald": ("#10B981", "#059669"),
    "Amber":   ("#F59E0B", "#D97706"),
    "Rose":    ("#F43F5E", "#E11D48"),
    "Slate":   ("#64748B", "#475569"),
}
DEFAULT_ACCENT_NAME = "Blue"


def get_accent(cfg: dict) -> tuple[str, str, str]:
    """Returns (name, fg, hover) for the current accent.  Falls back to default
    on unknown / missing config values."""
    name = cfg.get("accent_color", DEFAULT_ACCENT_NAME)
    if name not in ACCENT_PRESETS:
        name = DEFAULT_ACCENT_NAME
    fg, hover = ACCENT_PRESETS[name]
    return name, fg, hover


def slider_kwargs(cfg: dict) -> dict:
    """Accent kwargs to apply to a CTkSlider."""
    _, fg, hover = get_accent(cfg)
    return {
        "button_color":       fg,
        "button_hover_color": hover,
        "progress_color":     fg,
    }


def segbtn_kwargs(cfg: dict) -> dict:
    """Accent kwargs to apply to a CTkSegmentedButton."""
    _, fg, hover = get_accent(cfg)
    return {
        "selected_color":       fg,
        "selected_hover_color": hover,
    }


def switch_kwargs(cfg: dict) -> dict:
    """Accent kwargs to apply to a CTkSwitch."""
    _, fg, _ = get_accent(cfg)
    return {"progress_color": fg}


def apply_accent_to_tree(root, cfg: dict) -> None:
    """Walk the widget tree from `root` and reconfigure every slider,
    segmented button, and switch to use the current accent color.

    Lets accent picks take effect immediately without an app restart —
    widgets bind to their fg/hover/etc. at construction time, so anything
    already on screen needs to be explicitly reconfigured.
    """
    import customtkinter as ctk  # local import to keep theme.py importable
                                  # in headless contexts

    sk = slider_kwargs(cfg)
    bk = segbtn_kwargs(cfg)
    wk = switch_kwargs(cfg)

    def walk(w):
        try:
            if isinstance(w, ctk.CTkSlider):
                w.configure(**sk)
            elif isinstance(w, ctk.CTkSegmentedButton):
                w.configure(**bk)
            elif isinstance(w, ctk.CTkSwitch):
                w.configure(**wk)
        except Exception:
            # Defensive: a widget might not accept one of these kwargs
            # (e.g. CTk version skew). Skip it rather than crashing.
            pass
        try:
            for child in w.winfo_children():
                walk(child)
        except Exception:
            pass

    walk(root)
