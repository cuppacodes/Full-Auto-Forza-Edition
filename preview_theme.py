# ============================================================
#  preview_theme.py — Standalone design-review sandbox.
#
#  Run this file directly (`python preview_theme.py`) to explore
#  design directions for FAFE without touching the main app:
#
#    Polish        — typography / colors / spacing / icons
#                    (#1 #2 #4 #9)
#    Accent picker — inline accordion drill-down inside Settings →
#                    Appearance (#14)
#
#  Use the palette toggle at the top to flip Start / Stop colors
#  between Classic and Modern muted.  Use the theme toggle to test
#  light vs dark backgrounds.
# ============================================================

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ── Shared constants ───────────────────────────────────────────

CURRENT_FONTS = {
    "title":  ("Arial", 18, "bold"),  "h2": ("Arial", 14, "normal"),
    "body":   ("Segoe UI", 12, "normal"), "label": ("Segoe UI", 12, "normal"),
    "hint":   ("Segoe UI", 10, "normal"), "button": ("Arial", 13, "bold"),
    "value":  ("Segoe UI", 10, "normal"),
}
PROPOSED_FONTS = {
    "title":  ("Segoe UI", 20, "bold"),  "h2": ("Segoe UI", 16, "bold"),
    "body":   ("Segoe UI", 13, "normal"), "label": ("Segoe UI", 12, "normal"),
    "hint":   ("Segoe UI", 11, "normal"), "button": ("Segoe UI", 13, "bold"),
    "value":  ("Segoe UI", 11, "normal"),
}
CURRENT_SPACING  = {"inline": 8, "row": 4, "section": 12}
PROPOSED_SPACING = {"inline": 8, "row": 8, "section": 16}

PALETTES = {
    "Classic":      {"start_fg": "#2ECC71", "start_hover": "#27AE60",
                     "stop_fg":  "#E74C3C", "stop_hover":  "#C0392B",
                     "status_running": "#2ECC71", "status_warn": "#F39C12"},
    "Modern muted": {"start_fg": "#10B981", "start_hover": "#059669",
                     "stop_fg":  "#EF4444", "stop_hover":  "#DC2626",
                     "status_running": "#10B981", "status_warn": "#F59E0B"},
}

ACCENT_THEMES = {
    "Blue":    ("#3B82F6", "#2563EB"),
    "Indigo":  ("#6366F1", "#4F46E5"),
    "Purple":  ("#8B5CF6", "#7C3AED"),
    "Teal":    ("#14B8A6", "#0D9488"),
    "Emerald": ("#10B981", "#059669"),
    "Amber":   ("#F59E0B", "#D97706"),
    "Rose":    ("#F43F5E", "#E11D48"),
    "Slate":   ("#64748B", "#475569"),
}

ICONS = {"start": "▶  Start", "stop": "■  Stop", "back": "←  Back",
         "set": "⚙"}


# ── Animation engine (kept — used by accordion expand) ────────

def animate(host, setter, start, end, duration_ms=180, easing="ease_out",
            on_done=None):
    """Generic numeric animator via after() callbacks at ~60fps."""
    steps = max(1, duration_ms // 16)

    def ease(t):
        if easing == "ease_out":     return 1 - (1 - t) ** 3
        if easing == "ease_in_out":  return 3 * t * t - 2 * t * t * t
        return t

    def step(i):
        if i >= steps:
            setter(end)
            if on_done:
                on_done()
            return
        t = (i + 1) / steps
        setter(start + (end - start) * ease(t))
        host.after(16, lambda: step(i + 1))

    step(0)


# ── Tab 1: Polish (current vs proposed side-by-side) ──────────

def build_polish(parent, palette_name: str):
    for c in parent.winfo_children():
        c.destroy()
    body = ctk.CTkFrame(parent, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=8, pady=8)

    _polish_column(body, "CURRENT", CURRENT_FONTS, CURRENT_SPACING,
                   start_kwargs={"text": "Start"},
                   stop_kwargs={"text": "Stop", "fg_color": "#dc2626",
                                "hover_color": "#b91c1c"},
                   threshold_label="偵測閥值:", value_text="0.60",
                   show_status=False)

    pal = PALETTES[palette_name]
    _polish_column(body, f"PROPOSED  ·  {palette_name}",
                   PROPOSED_FONTS, PROPOSED_SPACING,
                   start_kwargs={"fg_color": pal["start_fg"],
                                 "hover_color": pal["start_hover"],
                                 "text": ICONS["start"]},
                   stop_kwargs={"fg_color": pal["stop_fg"],
                                "hover_color": pal["stop_hover"],
                                "text": ICONS["stop"]},
                   threshold_label="最低所需相似度:", value_text="60%",
                   show_status=True, palette=pal)


def _polish_column(parent, header, fonts, spacing, start_kwargs, stop_kwargs,
                   threshold_label, value_text, show_status, palette=None):
    col = ctk.CTkFrame(parent, fg_color=("gray92", "gray14"), corner_radius=10)
    col.pack(side="left", fill="both", expand=True, padx=8, pady=8)
    inner = ctk.CTkFrame(col, fg_color="transparent")
    inner.pack(fill="both", expand=True,
               padx=spacing["section"] * 2, pady=spacing["section"] * 2)

    ctk.CTkLabel(inner, text=header, font=("Segoe UI", 11, "bold"),
                 text_color=("gray40", "gray60")).pack(anchor="w",
                                                       pady=(0, 12))
    ctk.CTkLabel(inner, text="FAFE", font=fonts["title"]).pack(anchor="w")
    ctk.CTkLabel(inner, text="Race Auto-Grind",
                 font=fonts["h2"]).pack(anchor="w", pady=(spacing["row"], 0))
    ctk.CTkLabel(inner, text="Automates race grinding for skill points.",
                 font=fonts["body"], wraplength=380,
                 text_color=("gray30", "gray70")).pack(
        anchor="w", pady=(spacing["row"], 0))
    ctk.CTkFrame(inner, fg_color="transparent",
                 height=spacing["section"]).pack()

    br = ctk.CTkFrame(inner, fg_color="transparent")
    br.pack(anchor="w", pady=(0, spacing["section"]))
    ctk.CTkButton(br, text=start_kwargs.get("text", "Start"), width=120,
                  font=fonts["button"],
                  fg_color=start_kwargs.get("fg_color"),
                  hover_color=start_kwargs.get("hover_color")
                  ).pack(side="left", padx=(0, spacing["inline"]))
    ctk.CTkButton(br, text=stop_kwargs.get("text", "Stop"), width=100,
                  font=fonts["button"],
                  fg_color=stop_kwargs.get("fg_color"),
                  hover_color=stop_kwargs.get("hover_color")
                  ).pack(side="left")

    sr = ctk.CTkFrame(inner, fg_color="transparent")
    sr.pack(fill="x", pady=(0, spacing["section"]))
    ctk.CTkLabel(sr, text=threshold_label, font=fonts["label"],
                 text_color=("gray50", "gray55")).pack(side="left")
    sl = ctk.CTkSlider(sr, from_=0.5, to=0.9, height=14)
    sl.set(0.60)
    sl.pack(side="left", fill="x", expand=True, padx=8)
    ctk.CTkLabel(sr, text=value_text, font=fonts["value"], width=36,
                 text_color=("gray50", "gray55")).pack(side="left")

    ctk.CTkLabel(inner, text="(small caption / hint text shown here)",
                 font=fonts["hint"],
                 text_color=("gray40", "gray60")).pack(anchor="w")

    if show_status and palette:
        sr2 = ctk.CTkFrame(inner, fg_color="transparent")
        sr2.pack(anchor="w", pady=(spacing["section"], 0))
        ctk.CTkLabel(sr2, text="● Running", font=fonts["body"],
                     text_color=palette["status_running"]).pack(
            side="left", padx=(0, 16))
        ctk.CTkLabel(sr2, text="● Warning", font=fonts["body"],
                     text_color=palette["status_warn"]).pack(
            side="left", padx=(0, 16))
        ctk.CTkLabel(sr2, text="● Idle", font=fonts["body"],
                     text_color=("gray50", "gray60")).pack(side="left")


# ── Tab 2: Accent picker (inline accordion only) ──────────────

_picked_accent = {"name": "Emerald", "fg": "#10B981", "hover": "#059669"}


def build_accent_picker(parent, palette_name: str):
    for c in parent.winfo_children():
        c.destroy()

    # Outer wrapper — bounded width, centered
    body = ctk.CTkFrame(parent, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=24)

    ctk.CTkLabel(body, text="Mock Settings → Appearance",
                 font=("Segoe UI", 11, "bold"),
                 text_color=("gray40", "gray60")).pack(anchor="w",
                                                       pady=(0, 8))

    # The Settings card — fixed size so the accordion is constrained
    # within an area that mimics the real settings panel. Height includes
    # room for the open accordion (~100px) so nothing gets clipped.
    card = ctk.CTkFrame(body, fg_color=("gray95", "gray16"),
                        corner_radius=10, width=520, height=480)
    card.pack(anchor="w")
    card.pack_propagate(False)  # respect width AND height

    panel_inner = ctk.CTkFrame(card, fg_color="transparent")
    panel_inner.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(panel_inner, text="▼  外觀 / Appearance",
                 font=PROPOSED_FONTS["h2"]).pack(anchor="w", pady=(0, 12))

    # Settings rows that appear BEFORE the accent picker (won't move when
    # accordion expands).
    for label in ("Language", "Theme", "Toggle key", "Monitor",
                  "Check interval"):
        row = ctk.CTkFrame(panel_inner, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text=label, font=PROPOSED_FONTS["label"],
                     width=110, anchor="w").pack(side="left")
        ctk.CTkOptionMenu(row, values=["Option A", "Option B"],
                          width=200).pack(side="right")

    # Accent color row — placed LAST so the accordion expands into the
    # empty space below it instead of pushing other rows.
    accent_row = ctk.CTkFrame(panel_inner, fg_color="transparent")
    accent_row.pack(fill="x", pady=4)
    ctk.CTkLabel(accent_row, text="Accent color",
                 font=PROPOSED_FONTS["label"],
                 width=110, anchor="w").pack(side="left")

    swatch_btn = ctk.CTkButton(
        accent_row, text=f"  {_picked_accent['name']}  ▾",
        width=200, height=28,
        font=PROPOSED_FONTS["body"],
        fg_color=_picked_accent["fg"],
        hover_color=_picked_accent["hover"],
        anchor="w")
    swatch_btn.pack(side="right")

    # The expanding accordion — packed below the accent row, initially
    # hidden (height 0).  pack_propagate(False) so our animated height
    # is what's shown (not the natural height of children).
    expand_frame = ctk.CTkFrame(panel_inner, fg_color=("gray97", "gray13"),
                                corner_radius=8, height=0)
    expand_frame.pack_propagate(False)

    # Build swatches once — kept inside expand_frame even when collapsed
    inner_pad = ctk.CTkFrame(expand_frame, fg_color="transparent")
    inner_pad.pack(fill="both", expand=True, padx=12, pady=10)
    for i in range(4):
        inner_pad.columnconfigure(i, weight=1)

    def update_swatch(name, fg, hover):
        _picked_accent.update({"name": name, "fg": fg, "hover": hover})
        swatch_btn.configure(text=f"  {name}  ▾", fg_color=fg,
                             hover_color=hover)

    for i, (name, (fg, hover)) in enumerate(ACCENT_THEMES.items()):
        r, c = divmod(i, 4)
        ctk.CTkButton(inner_pad, text=name, width=100, height=28,
                      font=PROPOSED_FONTS["hint"],
                      fg_color=fg, hover_color=hover,
                      command=lambda n=name, f=fg, h=hover: update_swatch(n, f, h)
                      ).grid(row=r, column=c, padx=4, pady=4, sticky="ew")

    # Accordion target height — 2 swatch rows × 36px + outer padding ≈ 100
    OPEN_HEIGHT = 100
    state = {"open": False}

    def toggle():
        if state["open"]:
            animate(expand_frame,
                    lambda v: expand_frame.configure(height=int(v)),
                    OPEN_HEIGHT, 0, 160,
                    on_done=lambda: expand_frame.pack_forget())
            state["open"] = False
            swatch_btn.configure(text=f"  {_picked_accent['name']}  ▾")
        else:
            expand_frame.pack(fill="x", pady=(6, 0), after=accent_row)
            expand_frame.configure(height=0)
            animate(expand_frame,
                    lambda v: expand_frame.configure(height=int(v)),
                    0, OPEN_HEIGHT, 200)
            state["open"] = True
            swatch_btn.configure(text=f"  {_picked_accent['name']}  ▴")

    swatch_btn.configure(command=toggle)

    # Hint below the card
    ctk.CTkLabel(body,
                 text="↗ Click the accent swatch button to expand the "
                      "inline picker. It pushes the rows below down within "
                      "the same panel — the window itself doesn't resize.",
                 font=PROPOSED_FONTS["hint"],
                 text_color=("gray40", "gray60"),
                 wraplength=520, justify="left").pack(anchor="w",
                                                      pady=(16, 0))


# ── Main window ────────────────────────────────────────────────

class PreviewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FAFE — Design Preview")
        self.geometry("1280x780")
        self.minsize(960, 600)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 0))
        ctk.CTkLabel(top, text="Palette:",
                     font=("Segoe UI", 13)).pack(side="left", padx=(0, 12))
        self._palette_var = ctk.StringVar(value="Modern muted")
        ctk.CTkSegmentedButton(
            top, values=list(PALETTES.keys()),
            variable=self._palette_var,
            command=self._on_palette_change,
            width=260, height=30,
        ).pack(side="left")

        ctk.CTkLabel(top, text="Theme:",
                     font=("Segoe UI", 13)).pack(side="left", padx=(24, 12))
        theme_var = ctk.StringVar(value="dark")
        ctk.CTkSegmentedButton(
            top, values=["light", "dark"],
            variable=theme_var,
            command=lambda v: ctk.set_appearance_mode(v),
            width=160, height=30,
        ).pack(side="left")

        self._tabs = ctk.CTkTabview(self, anchor="nw", height=24)
        self._tabs.pack(fill="both", expand=True, padx=16, pady=12)
        for name in ("Polish", "Accent picker"):
            self._tabs.add(name)

        self._render_all()

    def _render_all(self):
        pal = self._palette_var.get()
        build_polish        (self._tabs.tab("Polish"),        pal)
        build_accent_picker (self._tabs.tab("Accent picker"), pal)

    def _on_palette_change(self, _val: str):
        self._render_all()


if __name__ == "__main__":
    PreviewApp().mainloop()
