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
from app_lang import t as _at
from config import (load, save, EXAMPLES_DIR,
                    get_race_templates, get_mastery_templates, get_nodes_file)
from log_widget import LogWidget
from setup_panel import SetupPanel


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

    # ── Window setup ──────────────────────────────────────────

    def _apply_theme(self):
        theme = self._cfg.get("theme", "system")
        if theme == "system":
            ctk.set_appearance_mode("system")
        else:
            ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

    def _setup_window(self):
        self.title("Forza Auto — Race & Mastery")
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

        # Content frames
        self._race_frame    = self._build_race_tab()
        self._mastery_frame = self._build_mastery_tab()

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

    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(10, 4))

        # App title
        ctk.CTkLabel(
            bar, text=_at("app_title", self._lang),
            font=("Arial", 18, "bold")).pack(side="left")

        # Monitor picker (left side of topbar)
        mon_left_frame = ctk.CTkFrame(bar, fg_color="transparent")
        mon_left_frame.pack(side="left", padx=(16, 0))
        ctk.CTkLabel(mon_left_frame,
                     text=_at('label_monitor', self._lang),
                     font=('Segoe UI', 12)).pack(side='left')
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


        ctk.CTkButton(
            right, text="⚙", width=36,
            font=("Segoe UI", 16),
            command=self._open_settings,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=("gray20", "gray90")
        ).pack(side="left", padx=(8, 0))

    def _build_race_tab(self) -> ctk.CTkFrame:
        frame = ctk.CTkScrollableFrame(self, fg_color="transparent")

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
            var = ctk.DoubleVar(value=self._cfg.get(key, 0))
            val_lbl = ctk.CTkLabel(row, text=f"{var.get():.2f}",
                                   width=46, anchor="e",
                                   font=("Segoe UI", 12))
            # Update label while dragging
            var.trace_add("write",
                          lambda *a, vl=val_lbl, va=var:
                          vl.configure(text=f"{va.get():.2f}"))
            slider = ctk.CTkSlider(
                row, variable=var,
                from_=lo, to=hi)
            # Save only on mouse release
            slider.bind('<ButtonRelease-1>',
                        lambda e, k=key, va=var: self._on_setting_change(k, va))
            slider.pack(side="left", fill="x", expand=True, padx=4)
            val_lbl.pack(side="right", padx=(4, 0))

    def _build_run_controls(self, parent, mode: str):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(4, 0))

        if mode == "race":
            self._race_start_btn = ctk.CTkButton(
                row, text=_at("btn_start", self._lang),
                command=self._start_race,
                width=120, font=("Arial", 13, "bold"))
            self._race_start_btn.pack(side="left", padx=(0, 8))

            self._race_stop_btn = ctk.CTkButton(
                row, text=_at("btn_stop", self._lang),
                command=self._stop_auto,
                fg_color="#dc2626", hover_color="#b91c1c",
                width=100, state="disabled")
            self._race_stop_btn.pack(side="left")

            self._race_shortcut_lbl = ctk.CTkLabel(
                parent,
                text=_at("shortcut_toggle", self._lang,
                         key=self._toggle_key.upper()),
                font=("Arial", 11),
                text_color=("gray50", "gray60"))
            self._race_shortcut_lbl.pack(anchor="w", padx=12, pady=(2, 6))

        else:
            self._mastery_start_btn = ctk.CTkButton(
                row, text=_at("btn_start", self._lang),
                command=self._start_mastery,
                width=120, font=("Arial", 13, "bold"))
            self._mastery_start_btn.pack(side="left", padx=(0, 8))

            self._mastery_stop_btn = ctk.CTkButton(
                row, text=_at("btn_stop", self._lang),
                command=self._stop_auto,
                fg_color="#dc2626", hover_color="#b91c1c",
                width=100, state="disabled")
            self._mastery_stop_btn.pack(side="left")

            self._mastery_shortcut_lbl = ctk.CTkLabel(
                parent,
                text=_at("shortcut_toggle", self._lang,
                         key=self._toggle_key.upper()),
                font=("Arial", 11),
                text_color=("gray50", "gray60"))
            self._mastery_shortcut_lbl.pack(anchor="w", padx=12, pady=(2, 6))

    # ── Tab switching ─────────────────────────────────────────

    def _switch_tab(self, tab: str):
        if self._current_tab == tab:
            return
        self._current_tab = tab
        self._race_frame.pack_forget()
        self._mastery_frame.pack_forget()

        if tab == "race":
            self._race_frame.pack(fill="both", expand=True,
                                  padx=4, pady=4)
            self._race_tab_btn.configure(fg_color=("gray75", "gray35"))
            self._mastery_tab_btn.configure(fg_color=("gray85", "gray20"))
            self._active_log = self._race_log
        else:
            self._mastery_frame.pack(fill="both", expand=True,
                                     padx=4, pady=4)
            self._mastery_tab_btn.configure(fg_color=("gray75", "gray35"))
            self._race_tab_btn.configure(fg_color=("gray85", "gray20"))
            self._active_log = self._mastery_log

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
                         self._race_log.log, self._set_status)
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
                mastery_run(cfg, self._stop_event,
                            self._mastery_log.log, self._set_status)
            except Exception as e:
                import traceback
                self._mastery_log.log(f'ERROR: {e}')
                self._mastery_log.log(traceback.format_exc())
                self._set_status(f'Error: {e}')

        self._auto_thread = threading.Thread(
            target=_mastery_safe, daemon=True)
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
        """Open a CTkToplevel showing the example image."""
        self._close_example_win()   # close any existing
        try:
            from PIL import Image as _PIL
            import customtkinter as _ctk
            img = _PIL.open(img_path)
            # Scale to max 960x540
            img.thumbnail((960, 540), _PIL.LANCZOS)
            w, h = img.size
            win = _ctk.CTkToplevel(self)
            win.title(f'Example: {key}')
            win.geometry(f'{w}x{h+40}')
            win.resizable(False, False)
            win.attributes('-topmost', True)
            ctk_img = _ctk.CTkImage(light_image=img, dark_image=img,
                                    size=(w, h))
            _ctk.CTkLabel(win, image=ctk_img, text='').pack()
            _ctk.CTkLabel(
                win,
                text=f'Press {self._capture_key.upper()} to capture',
                font=('Segoe UI', 12),
                text_color=('gray40', 'gray70')
            ).pack(pady=6)
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
            else:
                self._start_mastery()

    def _stop_auto(self):
        self._stop_event.set()
        self._set_status(_at("status_stopping", self._lang))

    def _poll_thread(self):
        """Check if automation thread has finished and re-enable buttons."""
        if self._auto_thread and self._auto_thread.is_alive():
            self.after(300, self._poll_thread)
        else:
            import keyboard
            try:
                keyboard.unhook_all_hotkeys()
            except Exception:
                pass
            self._race_start_btn.configure(state="normal")
            self._race_stop_btn.configure(state="disabled")
            self._mastery_start_btn.configure(state="normal")
            self._mastery_stop_btn.configure(state="disabled")

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
        """Open settings in a popup window."""
        if hasattr(self, '_settings_win') and self._settings_win.winfo_exists():
            self._settings_win.focus()
            return

        win = ctk.CTkToplevel(self)
        win.title(_at('settings_window_title', self._lang))
        win.geometry('480x520')
        win.resizable(False, False)
        win.attributes('-topmost', True)
        win.after(100, lambda: win.attributes('-topmost', False))
        self._settings_win = win

        scroll = ctk.CTkScrollableFrame(win, fg_color='transparent')
        scroll.pack(fill='both', expand=True, padx=12, pady=12)

        def section(label_key):
            ctk.CTkLabel(scroll,
                         text=_at(label_key, self._lang),
                         font=('Segoe UI', 13, 'bold'),
                         anchor='w').pack(fill='x', pady=(12, 4))
            ctk.CTkFrame(scroll, height=1,
                         fg_color=('gray70', 'gray40')).pack(fill='x')

        # ── Appearance ────────────────────────────────────
        section('settings_appearance_section')
        # Theme
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
        # Language
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
                (_at('setting_mastery_post_click_wait', self._lang), 'mastery_post_click_wait', 0.1, 2.0, 0.1, 'tip_mastery_post_click_wait'),
                (_at('setting_mastery_post_key_wait',   self._lang), 'mastery_post_key_wait',   0.5, 3.0, 0.1, 'tip_mastery_post_key_wait'),
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

    def _on_theme_change(self, val: str):
        # Map display label (any language) back to ctk English value
        theme_map = {
            _at('theme_system', self._lang): 'system',
            _at('theme_light',  self._lang): 'light',
            _at('theme_dark',   self._lang): 'dark',
            # Fallback English
            'System': 'system', 'Light': 'light', 'Dark': 'dark',
        }
        theme = theme_map.get(val, 'system')
        self._cfg["theme"] = theme
        save(self._cfg)
        ctk.set_appearance_mode(theme)

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
