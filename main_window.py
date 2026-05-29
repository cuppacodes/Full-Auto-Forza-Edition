# ============================================================
#  ui/main_window.py — Main application window
# ============================================================

import customtkinter as ctk
import threading
import queue
import json
import os
import sys

import config
import theme
from app_lang import t as _at
from config import (load, save, EXAMPLES_DIR,
                    get_race_templates, get_mastery_templates, get_nodes_file)
from log_widget import LogWidget
from setup_panel import SetupPanel
from updater import check_async, download_and_install
from version import VERSION


# ── Race template definitions ─────────────────────────────────
# Template label keys looked up via app_lang at runtime
RACE_TEMPLATE_KEYS = [
    ("start_menu",   "race_tpl_start_menu"),
    ("racing",       "race_tpl_racing"),
    ("restart_menu", "race_tpl_restart_menu"),
    ("confirm",      "race_tpl_confirm"),
]

MASTERY_TEMPLATE_KEYS_MAP = [
    ("mastery_ride_car",     "mastery_tpl_ride_car"),
    ("mastery_esc_hint",     "mastery_tpl_esc_hint"),
    ("mastery_upgrade_item", "mastery_tpl_upgrade_item"),
    ("mastery_mastery_item", "mastery_tpl_mastery_item"),
    ("mastery_anchor",       "mastery_tpl_anchor"),
    ("mastery_my_cars",      "mastery_tpl_my_cars"),
    ("mastery_sort_recent",  "mastery_tpl_sort_recent"),
]




class Tooltip:
    """Click-based info popup — no hover issues."""
    def __init__(self, widget, text: str):
        self._widget = widget
        self._text   = text
        self._win    = None
        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", self._toggle)

    def _toggle(self, event=None):
        if self._win and self._win.winfo_exists():
            self._win.destroy()
            self._win = None
            return
        x = self._widget.winfo_rootx()
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._win = tw = ctk.CTkToplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        ctk.CTkLabel(
            tw, text=self._text,
            justify="left",
            fg_color=("gray90", "gray20"),
            corner_radius=6,
            font=("Segoe UI", 11),
            padx=10, pady=8,
        ).pack()
        # Click anywhere to close
        tw.bind("<Button-1>", lambda e: (tw.destroy(), setattr(self, '_win', None)))
        # Also close if focus lost
        tw.bind("<FocusOut>", lambda e: (tw.destroy(), setattr(self, '_win', None)))

    def update_text(self, text: str):
        self._text = text


class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()
        self._cfg         = load()
        self._lang        = self._cfg.get('lang', 'en')
        self._restarting   = False
        self._toggle_key   = self._cfg.get('toggle_key', 'f9')
        self._capture_key  = self._cfg.get('capture_key', 'caps lock')
        self._binding_key  = None   # which key is being rebound
        self._stop_event  = threading.Event()
        self._auto_thread = None
        self._in_settings = False

        self._apply_theme()
        self._setup_window()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # Start example window queue poller
        self._example_win = None
        self._poll_example_queue()
        # Register global toggle hotkey at startup
        import keyboard as _kb
        _kb.add_hotkey(self._toggle_key, self._toggle_auto)

        # Check for updates in background (silent if up to date or offline)
        self.after(2000, self._check_for_updates)

    # ── Update check ──────────────────────────────────────────

    def _check_for_updates(self):
        def _on_found(tag, url):
            self.after(0, lambda: self._show_update_dialog(tag, url))
        check_async(_on_found)

    def _show_update_dialog(self, tag: str, url: str):
        lang = self._lang
        dialog = ctk.CTkToplevel(self)
        dialog.title(_at("update_title", lang))
        dialog.geometry("420x220")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=_at("update_available", lang, tag=tag),
            font=("Arial", 14, "bold")
        ).pack(pady=(28, 6))

        ctk.CTkLabel(
            dialog,
            text=_at("update_prompt", lang),
            font=("Arial", 12),
            text_color=("gray40", "gray60")
        ).pack(pady=(0, 20))

        # Progress bar (hidden until download starts)
        prog = ctk.CTkProgressBar(dialog, width=340)
        prog.set(0)

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack()

        def _start_update():
            yes_btn.configure(state="disabled")
            no_btn.configure(state="disabled")
            prog.pack(pady=(10, 0))

            def _progress(pct):
                self.after(0, lambda: prog.set(pct / 100))

            def _done(success, err=""):
                if not success:
                    self.after(0, lambda: ctk.CTkLabel(
                        dialog,
                        text=f"Error: {err}",
                        text_color="red"
                    ).pack())

            download_and_install(url, progress_cb=_progress, done_cb=_done)

        yes_btn = ctk.CTkButton(
            btn_row,
            text=_at("update_yes", lang),
            command=_start_update,
            width=120
        )
        yes_btn.pack(side="left", padx=8)

        no_btn = ctk.CTkButton(
            btn_row,
            text=_at("update_no", lang),
            command=dialog.destroy,
            fg_color="transparent",
            border_width=1,
            width=100
        )
        no_btn.pack(side="left", padx=8)

    # ── Window setup ──────────────────────────────────────────

    def _apply_theme(self):
        theme = self._cfg.get("theme", "system")
        if theme == "system":
            ctk.set_appearance_mode("system")
        else:
            ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

    def _setup_window(self):
        self.title(f"Full Auto Forza Edition v{VERSION}")
        self.geometry("900x650")
        self.minsize(700, 500)
        self.resizable(True, True)

    # ── UI construction ───────────────────────────────────────

    def _build_ui(self):
        # Top bar
        self._build_topbar()

        # Tab selector
        self._tab_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._tab_frame.pack(fill="x", padx=12, pady=(0, 4))

        self._race_tab_btn = ctk.CTkButton(
            self._tab_frame, text=_at("tab_race", self._lang),
            command=lambda: self._switch_tab("race"),
            width=140)
        self._race_tab_btn.pack(side="left", padx=(0, 6))

        self._mastery_tab_btn = ctk.CTkButton(
            self._tab_frame, text=_at("tab_mastery", self._lang),
            command=lambda: self._switch_tab("mastery"),
            width=140)
        self._mastery_tab_btn.pack(side="left")

        self._buy_tab_btn = ctk.CTkButton(
            self._tab_frame, text=_at("tab_buy", self._lang),
            command=lambda: self._switch_tab("buy"),
            width=140)
        self._buy_tab_btn.pack(side="left", padx=(6, 0))

        self._delete_tab_btn = ctk.CTkButton(
            self._tab_frame, text=_at("tab_delete", self._lang),
            command=lambda: self._switch_tab("delete"),
            width=140)
        self._delete_tab_btn.pack(side="left", padx=(6, 0))

        # Content frames
        self._race_frame    = self._build_race_tab()
        self._mastery_frame = self._build_mastery_tab()
        self._buy_frame     = self._build_buy_tab()
        self._delete_frame  = self._build_delete_tab()

        # Status bar
        self._status_var = ctk.StringVar(value=_at("status_ready", self._lang))
        status_bar = ctk.CTkLabel(
            self, textvariable=self._status_var,
            anchor="w", font=("Arial", 11),
            fg_color=("gray85", "gray20"),
            corner_radius=0)
        status_bar.pack(side="bottom", fill="x", padx=0, pady=0)
        status_bar.configure(height=26)

        # Show race tab by default
        self._current_tab = None
        self._switch_tab("race")

        # Support button — fixed bottom right
        support_btn = ctk.CTkButton(
            self,
            text="☕ " + _at("support_btn", self._lang),
            width=110, height=30,
            font=("Segoe UI", 11),
            fg_color="#0070ba",
            hover_color="#005ea6",
            text_color="#ffffff",
            command=lambda: __import__("webbrowser").open("https://paypal.me/Leonbacon")
        )
        support_btn.place(relx=1.0, rely=1.0, anchor="se", x=-12, y=-12)

    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(10, 4))
        self._topbar = bar

        # App title
        ctk.CTkLabel(
            bar, text=_at("app_title", self._lang),
            font=theme.TITLE_FONT).pack(side="left")

        # Monitor picker (left side of topbar)
        mon_left_frame = ctk.CTkFrame(bar, fg_color="transparent")
        mon_left_frame.pack(side="left", padx=(16, 0))
        ctk.CTkLabel(mon_left_frame,
                     text=_at('label_monitor', self._lang),
                     font=theme.LABEL_FONT).pack(side='left')
        from capture import list_monitors
        _monitors   = list_monitors()
        _mon_options = [
            f"{m['index']} — {m['width']}x{m['height']}" +
            (" " + _at('monitor_primary_tag', self._lang)
             if m['left'] == 0 and m['top'] == 0 else "")
            for m in _monitors]
        _saved_idx  = self._cfg.get('monitor_index', 1)
        _primary_opt = next((o for o in _mon_options if
                             _at('monitor_primary_tag', self._lang) in o),
                            _mon_options[0] if _mon_options else '1')
        _saved_opt   = next((o for o in _mon_options
                             if o.startswith(str(_saved_idx) + ' —')),
                            _primary_opt)
        self._mon_var = ctk.StringVar(value=_saved_opt)
        self._mon_menu = ctk.CTkOptionMenu(
            mon_left_frame,
            variable=self._mon_var,
            values=_mon_options if _mon_options else ['1'],
            command=self._on_monitor_change,
            width=220)
        self._mon_menu.pack(side='left', padx=8)

        # Right side controls
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")

        # ── Detection mode toggle (Default / Custom) ──────────────────────
        # Default = OCR-primary (text confirmation, robust across hardware).
        # Custom  = pixel-only (for user-captured templates that differ from
        #           defaults — different language, non-text content, etc.)
        self._det_default_label = _at("det_mode_default", self._lang)
        self._det_custom_label  = _at("det_mode_custom",  self._lang)
        self._det_mode_var = ctk.StringVar(
            value=self._det_default_label
            if self._cfg.get("detector_ocr_primary", True)
            else self._det_custom_label)
        ctk.CTkSegmentedButton(
            right,
            values=[self._det_default_label, self._det_custom_label],
            variable=self._det_mode_var,
            command=self._on_detection_mode_change,
            width=140, height=28,
            **theme.segbtn_kwargs(self._cfg),
        ).pack(side="left", padx=(0, theme.PAD_TIGHT))

        # ? icon — tooltip explains when to use Custom mode
        det_q_lbl = ctk.CTkLabel(
            right, text="?", width=18,
            font=theme.HINT_FONT,
            text_color=("gray50", "gray60"),
            cursor="question_arrow")
        det_q_lbl.pack(side="left", padx=(0, theme.PAD_INLINE))
        Tooltip(det_q_lbl, _at("det_mode_tip", self._lang))

        ctk.CTkButton(
            right, text="⚙", width=36,
            font=theme.ICON_FONT,
            command=self._open_settings,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=("gray20", "gray90")
        ).pack(side="left", padx=(theme.PAD_INLINE, 0))

    def _on_detection_mode_change(self, val: str):
        """Toggle detector_ocr_primary in config.json based on segmented button."""
        self._cfg["detector_ocr_primary"] = (val == self._det_default_label)
        save(self._cfg)

    def _build_race_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkScrollableFrame(self, fg_color="transparent")

        # Description
        ctk.CTkLabel(frame, text=_at("race_description", self._lang),
                     anchor="w", wraplength=480, justify="left",
                     font=("Arial", 12)).pack(fill="x", padx=12, pady=(8, 0))

        # Setup panel
        self._race_setup = SetupPanel(
            frame,
            template_defs=[(k, _at(lk, self._lang)) for k, lk in RACE_TEMPLATE_KEYS],
            folder=get_race_templates('custom'),
            nodes_file=None,
            res_cfg_key='race_resolution',
            mode='race',
            log_cb=self._log,
            status_cb=self._set_status,
            lang=self._lang,
            capture_key=self._capture_key,
            main_cfg=self._cfg,
        )
        self._race_setup.pack(fill="x", padx=8, pady=(4, 8))

        # Run controls
        self._build_run_controls(frame, mode="race")

        # Log
        self._race_log = LogWidget(frame,
                                    placeholder=_at('log_placeholder', self._lang))
        self._race_log.pack(fill="both", expand=True,
                            padx=8, pady=(4, 8))

        return frame

    def _build_mastery_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkScrollableFrame(self, fg_color="transparent")

        # Description
        ctk.CTkLabel(frame, text=_at("mastery_description", self._lang),
                     anchor="w", wraplength=480, justify="left",
                     font=("Arial", 12)).pack(fill="x", padx=12, pady=(8, 0))

        # Setup panel
        self._mastery_setup = SetupPanel(
            frame,
            template_defs=[(k, _at(lk, self._lang)) for k, lk in MASTERY_TEMPLATE_KEYS_MAP],
            folder=get_mastery_templates('custom'),
            nodes_file=get_nodes_file('custom'),
            res_cfg_key='mastery_resolution',
            mode='mastery',
            log_cb=self._log,
            status_cb=self._set_status,
            lang=self._lang,
            capture_key=self._capture_key,
            main_cfg=self._cfg,
        )
        self._mastery_setup.pack(fill="x", padx=8, pady=(4, 8))

        # Car count row
        count_row = ctk.CTkFrame(frame, fg_color="transparent")
        count_row.pack(fill="x", padx=12, pady=(4, 0))
        ctk.CTkLabel(count_row, text=_at("mastery_count_label", self._lang),
                     font=("Arial", 12)).pack(side="left")
        self._mastery_count_var = ctk.StringVar(value="0")
        ctk.CTkEntry(count_row, textvariable=self._mastery_count_var,
                     width=70, justify="center").pack(side="left", padx=8)
        ctk.CTkLabel(count_row, text=_at("delete_count_hint", self._lang),
                     font=("Arial", 11),
                     text_color=("gray40", "gray60")).pack(side="left")

        # Start row selector
        start_row_frame = ctk.CTkFrame(frame, fg_color="transparent")
        start_row_frame.pack(fill="x", padx=12, pady=(8, 0))
        ctk.CTkLabel(start_row_frame,
                     text=_at("mastery_start_row_label", self._lang),
                     font=theme.LABEL_FONT).pack(side="left")
        saved_start_row = str(self._cfg.get("mastery_start_loop", 1))
        self._mastery_start_row_var = ctk.StringVar(value=saved_start_row)
        ctk.CTkSegmentedButton(
            start_row_frame,
            values=["1", "2", "3"],
            variable=self._mastery_start_row_var,
            command=self._on_mastery_start_row_change,
            width=120,
            height=32,
            **theme.segbtn_kwargs(self._cfg),
        ).pack(side="left", padx=theme.PAD_INLINE)
        ctk.CTkLabel(start_row_frame,
                     text=_at("mastery_start_row_hint", self._lang),
                     font=("Arial", 11),
                     text_color=("gray40", "gray60")).pack(side="left")

        # Run controls
        self._build_run_controls(frame, mode="mastery")

        # Log
        self._mastery_log = LogWidget(frame,
                                      placeholder=_at('log_placeholder', self._lang))
        self._mastery_log.pack(fill="both", expand=True,
                               padx=8, pady=(4, 8))

        return frame

    def _build_settings_fields(self, frame, fields):
        # fields: (label, cfg_key, lo, hi, step, tip_key)
        for label, key, lo, hi, step, tip_key in fields:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=4)
            # Label text (no tooltip)
            ctk.CTkLabel(row, text=label, width=160,
                         anchor="w").pack(side="left")
            # ? icon — tooltip only fires here
            q_lbl = ctk.CTkLabel(row, text="?", width=18,
                                 font=("Segoe UI", 11),
                                 text_color=("gray50", "gray60"),
                                 cursor="question_arrow")
            q_lbl.pack(side="left", padx=(0, 6))
            Tooltip(q_lbl, _at(tip_key, self._lang))
            raw = self._cfg.get(key, lo)
            clamped = max(lo, min(hi, float(raw)))
            var = ctk.DoubleVar(value=clamped)
            val_lbl = ctk.CTkLabel(row, text=f"{var.get():.2f}",
                                   width=52, anchor="e",
                                   font=("Segoe UI", 12))
            val_lbl.pack(side="right", padx=(4, 0))
            # Update label while dragging
            var.trace_add("write",
                          lambda *a, vl=val_lbl, va=var:
                          vl.configure(text=f"{va.get():.2f}"))
            slider = ctk.CTkSlider(
                row, variable=var,
                from_=lo, to=hi,
                **theme.slider_kwargs(self._cfg))
            # Save only on mouse release
            slider.bind('<ButtonRelease-1>',
                        lambda e, k=key, va=var: self._on_setting_change(k, va))
            slider.pack(side="left", fill="x", expand=True, padx=4)

    def _build_buy_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color="transparent")

        # Description
        desc = ctk.CTkFrame(frame, fg_color="transparent")
        desc.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(desc, text=_at("buy_description", self._lang),
                     anchor="w", wraplength=480,
                     font=("Arial", 12)).pack(fill="x")

        # Count row
        count_row = ctk.CTkFrame(frame, fg_color="transparent")
        count_row.pack(fill="x", padx=12, pady=(8, 0))
        ctk.CTkLabel(count_row, text=_at("buy_count_label", self._lang),
                     font=("Arial", 12)).pack(side="left")
        self._buy_count_var = ctk.StringVar(value="0")
        ctk.CTkEntry(count_row, textvariable=self._buy_count_var,
                     width=70, justify="center").pack(side="left", padx=8)
        ctk.CTkLabel(count_row, text=_at("delete_count_hint", self._lang),
                     font=("Arial", 11),
                     text_color=("gray40", "gray60")).pack(side="left")

        # Run controls
        self._build_run_controls(frame, mode="buy")

        # Log
        self._buy_log = LogWidget(frame)
        self._buy_log.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        return frame

    def _build_delete_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self, fg_color="transparent")

        desc = ctk.CTkFrame(frame, fg_color="transparent")
        desc.pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(desc, text=_at("delete_description", self._lang),
                     anchor="w", wraplength=480,
                     font=("Arial", 12), justify="left").pack(fill="x")

        # Car count row
        count_row = ctk.CTkFrame(frame, fg_color="transparent")
        count_row.pack(fill="x", padx=12, pady=(8, 0))
        ctk.CTkLabel(count_row, text=_at("delete_count_label", self._lang),
                     font=("Arial", 12)).pack(side="left")
        self._delete_count_var = ctk.StringVar(value="0")
        ctk.CTkEntry(count_row, textvariable=self._delete_count_var,
                     width=70, justify="center").pack(side="left", padx=8)
        ctk.CTkLabel(count_row, text=_at("delete_count_hint", self._lang),
                     font=("Arial", 11),
                     text_color=("gray40", "gray60")).pack(side="left")

        self._build_run_controls(frame, mode="delete")

        self._delete_log = LogWidget(frame)
        self._delete_log.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        return frame

    def _build_run_controls(self, parent, mode: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(4, 0))

        if mode == "race":
            self._race_start_btn = ctk.CTkButton(
                row, text=theme.ICON_START + _at("btn_start", self._lang),
                command=self._start_race,
                width=120, font=theme.BUTTON_FONT,
                fg_color=theme.START_FG, hover_color=theme.START_HOVER)
            self._race_start_btn.pack(side="left", padx=(0, 8))

            self._race_stop_btn = ctk.CTkButton(
                row, text=theme.ICON_STOP + _at("btn_stop", self._lang),
                command=self._stop_auto,
                fg_color=theme.STOP_FG, hover_color=theme.STOP_HOVER,
                width=100, font=theme.BUTTON_FONT, state="disabled")
            self._race_stop_btn.pack(side="left")

            self._race_shortcut_lbl = ctk.CTkLabel(
                parent,
                text=_at("shortcut_toggle", self._lang,
                         key=self._toggle_key.upper()),
                font=theme.HINT_FONT,
                text_color=("gray50", "gray60"))
            self._race_shortcut_lbl.pack(anchor="w", padx=12, pady=(2, 6))

        elif mode == "mastery":
            self._mastery_start_btn = ctk.CTkButton(
                row, text=theme.ICON_START + _at("btn_start", self._lang),
                command=self._start_mastery,
                width=120, font=theme.BUTTON_FONT,
                fg_color=theme.START_FG, hover_color=theme.START_HOVER)
            self._mastery_start_btn.pack(side="left", padx=(0, 8))

            self._mastery_stop_btn = ctk.CTkButton(
                row, text=theme.ICON_STOP + _at("btn_stop", self._lang),
                command=self._stop_auto,
                fg_color=theme.STOP_FG, hover_color=theme.STOP_HOVER,
                width=100, font=theme.BUTTON_FONT, state="disabled")
            self._mastery_stop_btn.pack(side="left")

            self._mastery_shortcut_lbl = ctk.CTkLabel(
                parent,
                text=_at("shortcut_toggle", self._lang,
                         key=self._toggle_key.upper()),
                font=theme.HINT_FONT,
                text_color=("gray50", "gray60"))
            self._mastery_shortcut_lbl.pack(anchor="w", padx=12, pady=(2, 6))

        elif mode == "buy":
            self._buy_start_btn = ctk.CTkButton(
                row, text=theme.ICON_START + _at("btn_start", self._lang),
                command=self._start_buy,
                width=120, font=theme.BUTTON_FONT,
                fg_color=theme.START_FG, hover_color=theme.START_HOVER)
            self._buy_start_btn.pack(side="left", padx=(0, 8))

            self._buy_stop_btn = ctk.CTkButton(
                row, text=theme.ICON_STOP + _at("btn_stop", self._lang),
                command=self._stop_auto,
                fg_color=theme.STOP_FG, hover_color=theme.STOP_HOVER,
                width=100, font=theme.BUTTON_FONT, state="disabled")
            self._buy_stop_btn.pack(side="left")

            self._buy_shortcut_lbl = ctk.CTkLabel(
                parent,
                text=_at("shortcut_toggle", self._lang,
                         key=self._toggle_key.upper()),
                font=theme.HINT_FONT,
                text_color=("gray50", "gray60"))
            self._buy_shortcut_lbl.pack(anchor="w", padx=12, pady=(2, 6))

        else:  # delete
            self._delete_start_btn = ctk.CTkButton(
                row, text=theme.ICON_START + _at("btn_start", self._lang),
                command=self._start_delete,
                width=120, font=theme.BUTTON_FONT,
                fg_color=theme.START_FG, hover_color=theme.START_HOVER)
            self._delete_start_btn.pack(side="left", padx=(0, 8))

            self._delete_stop_btn = ctk.CTkButton(
                row, text=theme.ICON_STOP + _at("btn_stop", self._lang),
                command=self._stop_auto,
                fg_color=theme.STOP_FG, hover_color=theme.STOP_HOVER,
                width=100, font=theme.BUTTON_FONT, state="disabled")
            self._delete_stop_btn.pack(side="left")

            self._delete_shortcut_lbl = ctk.CTkLabel(
                parent,
                text=_at("shortcut_toggle", self._lang,
                         key=self._toggle_key.upper()),
                font=theme.HINT_FONT,
                text_color=("gray50", "gray60"))
            self._delete_shortcut_lbl.pack(anchor="w", padx=12, pady=(2, 6))

    # ── Tab switching ─────────────────────────────────────────

    def _switch_tab(self, tab: str):
        if self._current_tab == tab:
            return
        self._current_tab = tab
        self._race_frame.pack_forget()
        self._mastery_frame.pack_forget()
        self._buy_frame.pack_forget()
        self._delete_frame.pack_forget()

        active   = ("gray75", "gray35")
        inactive = ("gray85", "gray20")
        self._race_tab_btn.configure(   fg_color=active if tab == "race"    else inactive)
        self._mastery_tab_btn.configure(fg_color=active if tab == "mastery" else inactive)
        self._buy_tab_btn.configure(    fg_color=active if tab == "buy"     else inactive)
        self._delete_tab_btn.configure( fg_color=active if tab == "delete"  else inactive)

        if tab == "race":
            self._race_frame.pack(fill="both", expand=True, padx=4, pady=4)
            self._active_log = self._race_log
            self._active_setup_panel = self._race_setup
        elif tab == "mastery":
            self._mastery_frame.pack(fill="both", expand=True, padx=4, pady=4)
            self._active_log = self._mastery_log
            self._active_setup_panel = self._mastery_setup
        elif tab == "buy":
            self._buy_frame.pack(fill="both", expand=True, padx=4, pady=4)
            self._active_log = self._buy_log
            self._active_setup_panel = None
        else:
            self._delete_frame.pack(fill="both", expand=True, padx=4, pady=4)
            self._active_log = self._delete_log
            self._active_setup_panel = None

    # ── Automation control ────────────────────────────────────

    def _start_race(self):
        if self._auto_thread and self._auto_thread.is_alive():
            return
        self._stop_event.clear()
        self._set_status(_at("status_starting_race", self._lang))
        self._race_start_btn.configure(state="disabled")
        self._race_stop_btn.configure(state="normal")
        self._race_log.clear()

        cfg = self._cfg   # reference so monitor changes are picked up

        def _race_safe():
            log_cb = self._race_log.log
            try:
                from race import run as race_run
                lang = cfg.get('lang', 'en')
                log_cb(_at('startup_switch_to_game', lang))
                import time as _t
                for i in range(5, 0, -1):
                    if self._stop_event.is_set(): return
                    if not self._is_game_focused():
                        log_cb(_at('startup_game_not_focused', lang))
                    else:
                        log_cb(_at('startup_game_focused', lang))
                    log_cb(_at('startup_countdown', lang, i=i))
                    self._set_status(_at('startup_countdown', lang, i=i))
                    _t.sleep(1)
                if self._stop_event.is_set(): return
                log_cb(_at('startup_running', lang))
                race_run(cfg, self._stop_event,
                         self._race_log.log, self._set_status,
                         warn_cb=self._race_log.log_warning,
                         section_cb=self._race_log.log_section)
            except Exception as e:
                import traceback
                self._race_log.log(f'ERROR: {e}')
                self._race_log.log(traceback.format_exc())
                self._set_status(f'Error: {e}')

        self._auto_thread = threading.Thread(
            target=_race_safe, daemon=True)
        self._auto_thread.start()
        self._poll_thread()

    def _start_mastery(self):
        if self._auto_thread and self._auto_thread.is_alive():
            return
        self._stop_event.clear()
        self._set_status(_at("status_starting_mastery", self._lang))
        self._mastery_start_btn.configure(state="disabled")
        self._mastery_stop_btn.configure(state="normal")
        self._mastery_log.clear()

        cfg = self._cfg   # reference so monitor changes are picked up

        def _mastery_safe():
            log_cb = self._mastery_log.log
            try:
                from mastery import run as mastery_run
                lang = cfg.get('lang', 'en')
                log_cb(_at('startup_switch_to_game', lang))
                import time as _t
                for i in range(5, 0, -1):
                    if self._stop_event.is_set(): return
                    if not self._is_game_focused():
                        log_cb(_at('startup_game_not_focused', lang))
                    else:
                        log_cb(_at('startup_game_focused', lang))
                    log_cb(_at('startup_countdown', lang, i=i))
                    self._set_status(_at('startup_countdown', lang, i=i))
                    _t.sleep(1)
                if self._stop_event.is_set(): return
                log_cb(_at('startup_running', lang))
                try:
                    max_cars = int(self._mastery_count_var.get())
                except ValueError:
                    max_cars = 0
                mastery_run(cfg, self._stop_event,
                            self._mastery_log.log, self._set_status,
                            max_cars=max_cars,
                            warn_cb=self._mastery_log.log_warning,
                            section_cb=self._mastery_log.log_section)
            except Exception as e:
                import traceback
                self._mastery_log.log(f'ERROR: {e}')
                self._mastery_log.log(traceback.format_exc())
                self._set_status(f'Error: {e}')

        self._auto_thread = threading.Thread(
            target=_mastery_safe, daemon=True)
        self._auto_thread.start()
        self._poll_thread()

    def _start_buy(self):
        if self._auto_thread and self._auto_thread.is_alive():
            return
        self._stop_event.clear()
        self._set_status(_at("status_starting_buy", self._lang))
        self._buy_start_btn.configure(state="disabled")
        self._buy_stop_btn.configure(state="normal")
        self._buy_log.clear()

        def _buy_safe():
            log_cb = self._buy_log.log
            lang = self._cfg.get('lang', 'en')
            try:
                import time as _t
                import keyboard
                log_cb(_at('startup_switch_to_game', lang))
                for i in range(5, 0, -1):
                    if self._stop_event.is_set(): return
                    log_cb(_at('startup_countdown', lang, i=i))
                    self._set_status(_at('startup_countdown', lang, i=i))
                    _t.sleep(1)
                if self._stop_event.is_set(): return
                log_cb(_at('buy_running', lang))
                try:
                    max_buy = int(self._buy_count_var.get())
                except ValueError:
                    max_buy = 0
                buy_kw = self._cfg.get('buy_post_key_wait', 0.5)
                loop = 0
                while not self._stop_event.is_set():
                    loop += 1
                    log_cb(f"-- {_at('buy_loop', lang)} #{loop}" +
                           (f" / {max_buy}" if max_buy > 0 else "") + " --")
                    for key in ['space', 'down', 'enter', 'enter', 'enter']:
                        if self._stop_event.is_set(): break
                        keyboard.press_and_release(key)
                        log_cb(_at('log_buy_key', lang, key=key.upper()))
                        _t.sleep(buy_kw)
                    if max_buy > 0 and loop >= max_buy:
                        log_cb(_at('log_buy_limit_reached', lang, n=max_buy))
                        break
            except Exception as e:
                import traceback
                log_cb(f'ERROR: {e}')
                log_cb(traceback.format_exc())
                self._set_status(f'Error: {e}')

        self._auto_thread = threading.Thread(
            target=_buy_safe, daemon=True)
        self._auto_thread.start()
        self._poll_thread()

    def _start_delete(self):
        if self._auto_thread and self._auto_thread.is_alive():
            return
        self._stop_event.clear()
        self._set_status(_at("status_starting_delete", self._lang))
        self._delete_start_btn.configure(state="disabled")
        self._delete_stop_btn.configure(state="normal")
        self._delete_log.clear()

        def _delete_safe():
            log_cb = self._delete_log.log
            lang = self._cfg.get('lang', 'en')
            try:
                import time as _t
                log_cb(_at('startup_switch_to_game', lang))
                for i in range(5, 0, -1):
                    if self._stop_event.is_set(): return
                    log_cb(_at('startup_countdown', lang, i=i))
                    self._set_status(_at('startup_countdown', lang, i=i))
                    _t.sleep(1)
                if self._stop_event.is_set(): return
                import config as _cfg_mod
                from delete_cars import run as delete_run
                try:
                    max_cars = int(self._delete_count_var.get())
                except ValueError:
                    max_cars = 0
                delete_run(
                    cfg=_cfg_mod.load(),
                    stop_event=self._stop_event,
                    log_cb=log_cb,
                    status_cb=self._set_status,
                    max_cars=max_cars,
                )
            except Exception as e:
                import traceback
                log_cb(f'ERROR: {e}')
                log_cb(traceback.format_exc())
                self._set_status(f'Error: {e}')

        self._auto_thread = threading.Thread(
            target=_delete_safe, daemon=True)
        self._auto_thread.start()
        self._poll_thread()

    def _poll_example_queue(self):
        """Poll capture.py example queue and manage CTkToplevel on main thread."""
        try:
            from capture import _example_queue
            while True:
                action, key, img_path = _example_queue.get_nowait()
                if action == 'show' and img_path:
                    self._show_example_win(key, img_path)
                elif action == 'close':
                    self._close_example_win()
        except Exception:
            pass
        self.after(100, self._poll_example_queue)

    def _show_example_win(self, key, img_path):
        """Open a CTkToplevel showing the example image, scaled to fit
        the user's screen so it doesn't overflow on small displays."""
        self._close_example_win()   # close any existing
        try:
            from PIL import Image as _PIL
            import customtkinter as _ctk

            img = _PIL.open(img_path)
            w, h = img.size

            # Constrain to ~80% of the screen, preserving aspect ratio.
            # 80 px of vertical headroom is reserved for the caption + title bar.
            CAPTION_RESERVED = 80
            max_w = int(self.winfo_screenwidth()  * 0.80)
            max_h = int(self.winfo_screenheight() * 0.80) - CAPTION_RESERVED
            scale = min(max_w / w, max_h / h, 1.0)
            if scale < 1.0:
                w = max(1, int(w * scale))
                h = max(1, int(h * scale))
                # Resampling.LANCZOS in Pillow 10+, LANCZOS at top level pre-10
                resample = getattr(getattr(_PIL, 'Resampling', _PIL),
                                   'LANCZOS', 1)
                img = img.resize((w, h), resample)

            win = _ctk.CTkToplevel(self)
            win.title(f'Example: {key}')
            win.geometry(f'{w}x{h + CAPTION_RESERVED}')
            win.resizable(False, False)
            win.after(200, lambda: win.attributes('-topmost', False))

            # Closing the example window cancels the capture session
            def _on_example_close():
                self._close_example_win()
                active = getattr(self, '_active_setup_panel', None)
                if active and hasattr(active, '_stop_session'):
                    active._stop_session()

            win.protocol('WM_DELETE_WINDOW', _on_example_close)

            ctk_img = _ctk.CTkImage(light_image=img, dark_image=img,
                                    size=(w, h))
            _ctk.CTkLabel(win, image=ctk_img, text='').pack()
            _ctk.CTkLabel(
                win,
                text=_at('capture_instruction', self._lang),
                font=('Segoe UI', 16, 'bold'),
                text_color='#ff3333',
                wraplength=max(200, w - 20),
                justify='center'
            ).pack(pady=10)
            self._example_win = win
        except Exception as e:
            print(f'Example window error: {e}')

    def _close_example_win(self):
        """Close the example window if open."""
        if self._example_win is not None:
            try:
                self._example_win.destroy()
            except Exception:
                pass
            self._example_win = None

    def _is_game_focused(self) -> bool:
        """Check if Forza Horizon 6 is the active foreground window."""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            return "Forza Horizon 6" in buf.value
        except Exception:
            return True   # assume focused if check fails

    def _toggle_auto(self):
        """Toggle key: start if stopped, stop if running."""
        if self._auto_thread and self._auto_thread.is_alive():
            self._stop_auto()
        else:
            if self._current_tab == 'race':
                self._start_race()
            elif self._current_tab == 'mastery':
                self._start_mastery()
            elif self._current_tab == 'buy':
                self._start_buy()
            else:
                self._start_delete()

    def _stop_auto(self):
        self._stop_event.set()
        self._set_status(_at("status_stopping", self._lang))

    def _poll_thread(self):
        """Check if automation thread has finished and re-enable buttons."""
        if self._auto_thread and self._auto_thread.is_alive():
            self.after(300, self._poll_thread)
        else:
            # Re-register the toggle hotkey (automation threads may have
            # cleared keyboard hooks internally — always restore it here)
            try:
                import keyboard
                keyboard.remove_hotkey(self._toggle_key)
            except Exception:
                pass
            try:
                import keyboard
                keyboard.add_hotkey(self._toggle_key, self._toggle_auto)
            except Exception:
                pass
            self._race_start_btn.configure(state="normal")
            self._race_stop_btn.configure(state="disabled")
            self._mastery_start_btn.configure(state="normal")
            self._mastery_stop_btn.configure(state="disabled")
            self._buy_start_btn.configure(state="normal")
            self._buy_stop_btn.configure(state="disabled")
            self._delete_start_btn.configure(state="normal")
            self._delete_stop_btn.configure(state="disabled")

    # ── Helpers ───────────────────────────────────────────────

    def _log(self, msg: str):
        if hasattr(self, '_active_log'):
            self._active_log.log(msg)

    def _set_status(self, msg: str):
        self.after(0, lambda: self._status_var.set(f"  {msg}"))

    def _build_key_bindings(self, parent):
        """Add toggle key and capture key binding rows to a settings frame."""
        for cfg_key, label_key in [
            ('toggle_key',  'setting_toggle_key'),
            ('capture_key', 'setting_capture_key'),
        ]:
            row = ctk.CTkFrame(parent, fg_color='transparent')
            row.pack(fill='x', padx=12, pady=4)
            ctk.CTkLabel(row,
                         text=_at(label_key, self._lang),
                         width=190, anchor='w').pack(side='left')
            btn = ctk.CTkButton(
                row,
                text=self._cfg.get(cfg_key, 'f9').upper(),
                width=120,
                command=lambda k=cfg_key, b=None: self._start_key_bind(k))
            btn.pack(side='left', padx=8)
            # Store button ref for updating text
            setattr(self, f'_keybtn_{cfg_key}', btn)

    def _start_key_bind(self, cfg_key):
        """Start listening for a key press to rebind."""
        if self._binding_key is not None:
            return   # already binding
        self._binding_key = cfg_key
        btn = getattr(self, f'_keybtn_{cfg_key}', None)
        if btn:
            btn.configure(text=_at('shortcut_press_any_key', self._lang),
                          fg_color='#d97706')
        import keyboard
        keyboard.hook(self._on_key_bind_press)

    def _on_key_bind_press(self, event):
        """Called when a key is pressed during rebind."""
        if event.event_type != 'down':
            return
        import keyboard
        keyboard.unhook(self._on_key_bind_press)
        key_name = event.name.lower()
        cfg_key  = self._binding_key
        self._binding_key = None
        if key_name == 'escape':
            # Cancelled
            btn = getattr(self, f'_keybtn_{cfg_key}', None)
            if btn:
                btn.configure(
                    text=self._cfg.get(cfg_key, '').upper(),
                    fg_color=('gray75', 'gray25'))
            return
        # Save new key
        self._cfg[cfg_key] = key_name
        save(self._cfg)
        if cfg_key == 'toggle_key':
            self._toggle_key = key_name
            self._update_shortcut_hints()
        elif cfg_key == 'capture_key':
            self._capture_key = key_name
        btn = getattr(self, f'_keybtn_{cfg_key}', None)
        if btn:
            self.after(0, lambda: btn.configure(
                text=key_name.upper(),
                fg_color=('gray75', 'gray25')))

    def _update_shortcut_hints(self):
        """Refresh shortcut hint labels after key change."""
        txt = _at('shortcut_toggle', self._lang, key=self._toggle_key.upper())
        for lbl in [getattr(self, '_race_shortcut_lbl', None),
                    getattr(self, '_mastery_shortcut_lbl', None)]:
            if lbl:
                self.after(0, lambda l=lbl, t=txt: l.configure(text=t))

    def _open_settings(self):
        """Show settings as an inline panel inside the main window."""
        if not hasattr(self, '_settings_frame'):
            self._build_settings_panel()
        # Hide topbar, tab bar and current tab content
        self._topbar.pack_forget()
        self._tab_frame.pack_forget()
        self._race_frame.pack_forget()
        self._mastery_frame.pack_forget()
        self._buy_frame.pack_forget()
        self._delete_frame.pack_forget()
        self._settings_frame.pack(fill='both', expand=True)
        self._in_settings = True

    def _close_settings(self):
        """Hide settings and restore current tab."""
        if hasattr(self, '_settings_frame'):
            self._settings_frame.pack_forget()
        self._in_settings = False
        # Restore topbar and tab bar
        self._topbar.pack(fill='x', padx=12, pady=(10, 4))
        self._tab_frame.pack(fill='x', padx=12, pady=(0, 4))
        # Re-show whatever tab was active
        saved = self._current_tab
        self._current_tab = None
        self._switch_tab(saved)

    def _build_settings_panel(self):
        """Build the inline settings panel once."""
        self._settings_frame = ctk.CTkFrame(self, fg_color='transparent')

        # Header with back button
        header = ctk.CTkFrame(self._settings_frame, fg_color='transparent')
        header.pack(fill='x', padx=8, pady=(6, 0))
        ctk.CTkButton(
            header, text='← ' + _at('settings_back', self._lang),
            width=90, height=28,
            fg_color='transparent',
            border_width=1,
            font=('Segoe UI', 12),
            command=self._close_settings
        ).pack(side='left')
        ctk.CTkLabel(
            header,
            text=_at('settings_window_title', self._lang),
            font=('Segoe UI', 14, 'bold')
        ).pack(side='left', padx=12)

        scroll = ctk.CTkScrollableFrame(self._settings_frame, fg_color='transparent')
        scroll.pack(fill='both', expand=True, padx=12, pady=8)

        def section(label_key):
            ctk.CTkLabel(scroll,
                         text=_at(label_key, self._lang),
                         font=('Segoe UI', 13, 'bold'),
                         anchor='w').pack(fill='x', pady=(12, 4))
            ctk.CTkFrame(scroll, height=1,
                         fg_color=('gray70', 'gray40')).pack(fill='x')

        # ── Appearance ────────────────────────────────────
        section('settings_appearance_section')
        _app_row = ctk.CTkFrame(scroll, fg_color='transparent')
        _app_row.pack(fill='x', padx=12, pady=4)
        ctk.CTkLabel(_app_row, text=_at('label_theme', self._lang),
                     width=160, anchor='w').pack(side='left')
        self._theme_var = ctk.StringVar(value=self._cfg.get('theme', 'system').title())
        ctk.CTkOptionMenu(
            _app_row, variable=self._theme_var,
            values=[_at('theme_system', self._lang),
                    _at('theme_light',  self._lang),
                    _at('theme_dark',   self._lang)],
            command=self._on_theme_change,
            width=160).pack(side='left', padx=8)

        _lang_row = ctk.CTkFrame(scroll, fg_color='transparent')
        _lang_row.pack(fill='x', padx=12, pady=4)
        ctk.CTkLabel(_lang_row, text=_at('label_language', self._lang),
                     width=160, anchor='w').pack(side='left')
        _lang_map = {'en': 'English', 'zh-tw': '繁體中文', 'zh-cn': '简体中文'}
        self._lang_var = ctk.StringVar(
            value=_lang_map.get(self._cfg.get('lang', 'en'), 'English'))
        self._lang_menu = ctk.CTkOptionMenu(
            _lang_row, variable=self._lang_var,
            values=list(_lang_map.values()),
            command=self._on_lang_change,
            width=160)
        self._lang_menu.pack(side='left', padx=8)

        # ── Accent color picker (inline accordion) ─────────────
        self._build_accent_picker(scroll)

        # ── Shortcuts ─────────────────────────────────────
        section('settings_shortcuts_section')
        self._build_key_bindings(scroll)

        # ── Race settings ─────────────────────────────────
        section('settings_race_section')
        self._build_settings_fields(
            scroll,
            fields=[
                (_at('setting_race_check_interval', self._lang), 'race_check_interval', 0.1, 2.0, 0.1, 'tip_race_check_interval'),
                (_at('setting_race_post_key_wait',  self._lang), 'race_post_key_wait',  0.5, 3.0, 0.1, 'tip_race_post_key_wait'),
            ])

        # ── Mastery settings ──────────────────────────────
        section('settings_mastery_section')
        self._build_settings_fields(
            scroll,
            fields=[
                (_at('setting_mastery_check_interval',  self._lang), 'mastery_check_interval',  0.3, 2.0, 0.1, 'tip_mastery_check_interval'),
                (_at('setting_mastery_post_click_wait', self._lang), 'mastery_post_click_wait', 0.5, 2.0, 0.1, 'tip_mastery_post_click_wait'),
                (_at('setting_mastery_post_key_wait',   self._lang), 'mastery_post_key_wait',   0.8, 3.0, 0.1, 'tip_mastery_post_key_wait'),
                (_at('setting_mastery_node_click_wait', self._lang), 'mastery_node_click_wait', 0.7, 2.0, 0.1, 'tip_mastery_node_click_wait'),
            ])

        section('settings_buy_section')
        self._build_settings_fields(
            scroll,
            fields=[
                (_at('setting_buy_post_key_wait', self._lang), 'buy_post_key_wait', 0.4, 3.0, 0.1, 'tip_buy_post_key_wait'),
            ])

        section('settings_delete_section')
        self._build_settings_fields(
            scroll,
            fields=[
                (_at('setting_delete_post_key_wait', self._lang), 'delete_post_key_wait', 0.2, 3.0, 0.1, 'tip_delete_post_key_wait'),
            ])

    def _on_monitor_change(self, val: str):
        try:
            self._cfg['monitor_index'] = int(val.split('—')[0].strip())
        except Exception:
            self._cfg['monitor_index'] = 1
        save(self._cfg)
        for panel in [getattr(self, '_race_setup', None),
                      getattr(self, '_mastery_setup', None)]:
            if panel:
                panel._monitor_index = self._cfg['monitor_index']

    def _on_setting_change(self, key: str, var):
        self._cfg[key] = round(var.get(), 4)
        save(self._cfg)

    def _on_mastery_start_row_change(self, val: str):
        try:
            self._cfg["mastery_start_loop"] = int(val)
        except ValueError:
            self._cfg["mastery_start_loop"] = 1
        save(self._cfg)

    def _on_theme_change(self, val: str):
        # Map display label (any language) back to ctk English value
        theme_map = {
            _at('theme_system', self._lang): 'system',
            _at('theme_light',  self._lang): 'light',
            _at('theme_dark',   self._lang): 'dark',
            # Fallback English
            'System': 'system', 'Light': 'light', 'Dark': 'dark',
        }
        mode = theme_map.get(val, 'system')
        self._cfg["theme"] = mode
        save(self._cfg)
        ctk.set_appearance_mode(mode)

    # ── Accent picker (always-visible swatch grid) ────────────

    def _build_accent_picker(self, parent):
        """Inserts a label row + a 4×2 grid of accent color swatches.
        The currently selected one is marked with a contrasting border."""
        # Label row
        label_row = ctk.CTkFrame(parent, fg_color='transparent')
        label_row.pack(fill='x', padx=12, pady=(4, 2))
        ctk.CTkLabel(label_row,
                     text=_at('label_accent_color', self._lang),
                     width=160, anchor='w').pack(side='left')

        # Grid row — sits directly below the label, always expanded
        grid = ctk.CTkFrame(parent, fg_color=('gray95', 'gray16'),
                            corner_radius=8)
        grid.pack(fill='x', padx=12, pady=(0, 4))
        pad = ctk.CTkFrame(grid, fg_color='transparent')
        pad.pack(fill='both', expand=True, padx=8, pady=8)
        for i in range(4):
            pad.columnconfigure(i, weight=1)

        current_name, _, _ = theme.get_accent(self._cfg)
        self._accent_buttons: dict[str, ctk.CTkButton] = {}

        for i, (sw_name, (sw_fg, sw_hover)) in enumerate(
                theme.ACCENT_PRESETS.items()):
            r, c = divmod(i, 4)
            selected = (sw_name == current_name)
            btn = ctk.CTkButton(
                pad, text=sw_name, width=90, height=30,
                font=theme.HINT_FONT,
                fg_color=sw_fg, hover_color=sw_hover,
                border_width=2 if selected else 0,
                border_color=('white', 'white'),
                command=lambda n=sw_name, f=sw_fg, h=sw_hover:
                    self._on_accent_pick(n, f, h),
            )
            btn.grid(row=r, column=c, padx=4, pady=4, sticky='ew')
            self._accent_buttons[sw_name] = btn

    def _on_accent_pick(self, name: str, fg: str, hover: str):
        """Persist new accent, update the selection border, and apply the
        accent live to every existing slider/segmented button/switch in the
        running app — no restart required."""
        self._cfg['accent_color'] = name
        save(self._cfg)
        for btn_name, btn in self._accent_buttons.items():
            btn.configure(border_width=2 if btn_name == name else 0)
        theme.apply_accent_to_tree(self, self._cfg)

    def _on_lang_change(self, val: str):
        if self._restarting:
            return   # already restarting, ignore
        lang_map = {"English": "en", "繁體中文": "zh-tw", "简体中文": "zh-cn"}
        new_lang = lang_map.get(val, "en")
        if new_lang == self._cfg.get("lang", "en"):
            return   # no change
        self._restarting = True
        # Disable immediately to prevent double-trigger
        if hasattr(self, '_lang_menu'):
            self._lang_menu.configure(state="disabled")
        self._cfg["lang"] = new_lang
        self._lang = new_lang
        save(self._cfg)
        self._restart_app()

    def _restart_app(self):
        """Save config, relaunch the app, close this instance."""
        if not self._restarting:
            return
        import subprocess
        import os
        cwd = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) \
              else os.path.dirname(os.path.abspath(sys.argv[0]))
        if getattr(sys, 'frozen', False):
            subprocess.Popen([sys.executable], cwd=cwd)
        else:
            subprocess.Popen([sys.executable] + sys.argv, cwd=cwd)
        self.after(200, self.destroy)  # slight delay so config flush completes

    def _on_close(self):
        self._stop_event.set()
        self.destroy()
