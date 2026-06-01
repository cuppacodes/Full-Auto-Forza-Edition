# ============================================================
#  theme.py — Central design tokens for FAFE.
#
#  Single source of truth for fonts, spacing, semantic colors,
#  icons, and accent presets.  Import from here instead of
#  hardcoding font/color/padding values throughout the app.
# ============================================================


# ── Typography ────────────────────────────────────────────────
# The UI font family is LOCKED per language at startup by init_fonts() so the
# app always renders in a fixed, known-good face. Why this matters: "Segoe UI"
# (and CustomTkinter's default "Roboto") have no CJK glyphs, so when drawing
# Chinese text Windows falls back via its font-linking registry — and on some
# machines that fallback resolves to a decorative/brush font, making the whole
# UI look wrong (this was a real user report). Naming a CJK-capable Windows
# font explicitly (Microsoft JhengHei for 繁中, YaHei for 简中) bypasses that
# fallback entirely. English keeps Segoe UI.
#
# All callers reference these as `theme.X_FONT` (attribute access, never a
# by-value `from theme import X_FONT`), so reassigning them in init_fonts()
# before the UI is built propagates the family everywhere.

UI_FAMILY = "Segoe UI"   # resolved/overwritten by init_fonts()

TITLE_FONT  = (UI_FAMILY, 20, "bold")    # App title
H2_FONT     = (UI_FAMILY, 16, "bold")    # Section headers
BODY_FONT   = (UI_FAMILY, 13, "normal")  # Descriptions / paragraph text
LABEL_FONT  = (UI_FAMILY, 12, "normal")  # Setting labels
HINT_FONT   = (UI_FAMILY, 11, "normal")  # Captions / sub-text
BUTTON_FONT = (UI_FAMILY, 13, "bold")    # Primary action buttons
VALUE_FONT  = (UI_FAMILY, 11, "normal")  # Slider value readouts
ICON_FONT   = (UI_FAMILY, 16, "normal")  # ⚙ etc. — chunky icon

# Preferred families per UI language. All ship with Windows 8+/10/11, so one
# of these is always present; the list ends in a deterministic fallback.
_FAMILY_BY_LANG = {
    "zh-tw": ["Microsoft JhengHei UI", "Microsoft JhengHei", "PMingLiU", "Segoe UI"],
    "zh-cn": ["Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "Segoe UI"],
    "en":    ["Segoe UI"],
}


def _first_installed(candidates):
    """First font family in `candidates` that's actually installed; else the
    last candidate (deterministic). Needs a Tk root to query tkfont.families()."""
    try:
        import tkinter.font as tkfont
        available = {f.lower() for f in tkfont.families()}
        for fam in candidates:
            if fam.lower() in available:
                return fam
    except Exception:
        pass
    return candidates[-1] if candidates else "Segoe UI"


def init_fonts(lang="en", root=None):
    """Lock the UI font family for `lang` and rebuild every font token + the
    CustomTkinter/Tk defaults so the whole app renders in a fixed face,
    independent of the user's system font-linking. Call once after the Tk root
    exists and before building widgets. Idempotent."""
    global UI_FAMILY, TITLE_FONT, H2_FONT, BODY_FONT, LABEL_FONT, \
        HINT_FONT, BUTTON_FONT, VALUE_FONT, ICON_FONT

    UI_FAMILY = _first_installed(_FAMILY_BY_LANG.get(lang, ["Segoe UI"]))

    TITLE_FONT  = (UI_FAMILY, 20, "bold")
    H2_FONT     = (UI_FAMILY, 16, "bold")
    BODY_FONT   = (UI_FAMILY, 13, "normal")
    LABEL_FONT  = (UI_FAMILY, 12, "normal")
    HINT_FONT   = (UI_FAMILY, 11, "normal")
    BUTTON_FONT = (UI_FAMILY, 13, "bold")
    VALUE_FONT  = (UI_FAMILY, 11, "normal")
    ICON_FONT   = (UI_FAMILY, 16, "normal")

    # CTk widgets given no explicit font fall back to this default family
    # (out of the box "Roboto" — no CJK glyphs). Point it at our family.
    try:
        import customtkinter as ctk
        ctk.ThemeManager.theme["CTkFont"]["family"] = UI_FAMILY
    except Exception:
        pass

    # Plain-Tk named fonts (menus, default text). Leave TkFixedFont alone so
    # anything that wants monospace still gets it.
    if root is not None:
        try:
            import tkinter.font as tkfont
            for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont",
                         "TkHeadingFont", "TkTooltipFont"):
                try:
                    tkfont.nametofont(name).configure(family=UI_FAMILY)
                except Exception:
                    pass
        except Exception:
            pass
    return UI_FAMILY


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


def apply_font_family_to_tree(root, family: str | None = None) -> None:
    """Walk the widget tree from `root` and force every widget's font family to
    `family` (defaults to the locked UI_FAMILY), preserving size/weight/slant.

    Why this is needed on top of init_fonts(): lots of widgets are built with a
    hardcoded font tuple like ('Arial', 14) or ('Segoe UI', 11) instead of a
    theme.* token. Those families have NO CJK glyphs, so on a Chinese UI Windows
    substitutes a fallback — on some machines a decorative/brush font — and the
    widget (buttons, dropdowns, segmented buttons, some labels) renders wrong
    while theme.*-token widgets look fine. Rewriting every hardcoded tuple by
    hand is fragile and misses CTk internals (e.g. CTkOptionMenu's separate
    `dropdown_font`) and future additions; this single post-build pass fixes
    them all and is idempotent. Call after _build_ui and after building any
    on-demand panel.
    """
    import customtkinter as ctk

    fam = family or UI_FAMILY

    def _fix_attr(w, attr):
        try:
            f = w.cget(attr)
        except Exception:
            return  # widget doesn't have this option
        try:
            if isinstance(f, ctk.CTkFont):
                if f.cget("family") != fam:
                    f.configure(family=fam)
            elif isinstance(f, tuple) and len(f) >= 1:
                if f[0] != fam:
                    w.configure(**{attr: (fam,) + tuple(f[1:])})
            elif isinstance(f, str) and f and not f.startswith("Tk"):
                # A bare family string (rare). Named Tk fonts ("Tk…") are
                # handled by init_fonts() — don't disturb them.
                parts = f.split()
                if parts and parts[0] != fam:
                    w.configure(**{attr: (fam,) + tuple(parts[1:])})
        except Exception:
            pass

    def walk(w):
        _fix_attr(w, "font")
        _fix_attr(w, "dropdown_font")   # CTkOptionMenu / CTkComboBox popup
        try:
            for child in w.winfo_children():
                walk(child)
        except Exception:
            pass

    walk(root)
