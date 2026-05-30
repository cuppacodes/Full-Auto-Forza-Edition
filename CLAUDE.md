# Full Auto Forza Edition (FAFE) — Project Summary

## What is this?
A Windows desktop automation tool for Forza Horizon 6. Built with Python + CustomTkinter. Uses a hybrid OpenCV + optional OCR detection pipeline to identify game screens and simulate keyboard/mouse input.

## File Structure
```
New APP/
├── forza_app.py          # Entry point
├── main_window.py        # Main UI window (CTk), all tabs, settings panel
├── setup_panel.py        # Collapsible Setup & Templates panel with threshold sliders
├── capture.py            # Screenshot capture, region selection, CaptureSession, NodeSession
├── detector.py           # ScreenDetector — ROI + multi-scale + edge + optional OCR matching
├── race.py               # Race Auto-Grind automation logic
├── mastery.py            # Auto Unlock 22B Mastery automation logic
├── delete_cars.py        # Delete Used Cars automation logic
├── log_widget.py         # Thread-safe log widget with colored warning support
├── theme.py              # Design tokens — fonts, spacing, semantic colors, accent presets
├── app_lang.py           # All UI strings in zh-tw / zh-cn / en
├── config.py             # Config load/save, path helpers
├── updater.py            # GitHub release auto-updater
├── version.py            # VERSION = "1.3.3"
├── build_app.bat         # PyInstaller build script
├── FAFE_icon.ico         # App icon (exe icon + runtime window/taskbar icon)
├── assets/               # Support panel images: support_jkopay.png, discord_logo.png, paypal_logo.png (see assets/README.txt)
├── templates/            # Template images (race/, mastery_full/, each with 1080p/1440p/2160p/custom)
└── index.html            # GitHub Pages intro/tutorial page (trilingual)
```

## Architecture

### UI (main_window.py)
- 4 tabs: Race Auto / Auto Unlock 22B / Auto Buy 22B-STi / Delete Used Cars
- Settings is inline (not popup) — ⚙ hides topbar+tabs and shows settings panel, ← Back restores
- Topbar: app title, monitor picker, ⚙ button
- **Bottom-right overlay**: a frame placed at `se` holding a **Discord** button (official-logo icon, opens the invite link) left of the **☕ Support Me** button. Support Me no longer opens PayPal directly — it opens an **inline Support panel** (`_open_support`/`_close_support`/`_build_support_panel`, mirrors the settings inline pattern: pack_forget topbar+tabs, ← Back to restore). The panel offers two tip methods: a **街口支付 (JKOPAY) QR** image (260×260) and a **PayPal** button sized to the QR width (260). Discord/PayPal button icons use official-logo PNGs from `assets/`; images load via `_load_ctk_image` (PIL→CTkImage) resolved by `_resource_path` (dev + frozen `--onedir`/`_MEIPASS`), with graceful text/placeholder fallback if a file is missing. Assets bundled via `--add-data "assets;assets"`. See `assets/README.txt` for required files: `support_jkopay.png`, `discord_logo.png`, `paypal_logo.png`.
- Each tab has: description label, optional count input (0=unlimited), Start/Stop buttons, log widget
- Auto Unlock 22B tab also has a start-row selector (CTkSegmentedButton, values 1/2/3) between count and run controls; saved as `mastery_start_loop` in config
- Language: zh-tw (default), zh-cn, en — switching triggers app restart
- Theme: system/light/dark
- **App icon**: `FAFE_icon.ico` is both the exe icon (PyInstaller `--icon`) and the runtime window/taskbar icon. `--icon` only covers the exe; the window icon is set by `MainWindow._set_window_icon()` via `iconbitmap`. CustomTkinter applies its own default icon ~200ms after init, so we re-assert ours on a `self.after(300, …)` delay or it gets overridden. `_icon_path()` finds the `.ico` in both dev (next to source) and frozen `--onedir` (`sys._MEIPASS` / next to exe); the icon is bundled via `--add-data "FAFE_icon.ico;."` so it exists at runtime.
- **UI scale** (Settings → Appearance, `ui_scale` config): `Auto` / `100%`–`250%`. Drives `ctk.set_widget_scaling` + `set_window_scaling` from a single factor resolved by `config.resolve_ui_scale` (Auto = `get_scale_factor()` = screen_height/1080, clamped 0.8–2.5). `MainWindow._apply_scaling()` runs **before `super().__init__()`** (before the Tk root exists): it marks the process DPI-aware (crisp text) and calls `ctk.deactivate_automatic_dpi_awareness()` so scaling is driven only by our factor, not stacked on CTk's per-monitor DPI — so a given % means the same size regardless of the user's Windows display-scaling. Changing it applies live (`_on_scale_change` re-sets scaling + re-applies base geometry `900x650` so the window refits).

### Detection (detector.py)
- `ScreenDetector.detect(frame, key, template, threshold)` returns a `MatchResult` dataclass
- ROI-first: each template key has a configured search region (see `DEFAULT_ROIS`); full-screen fallback applies a 0.94 score penalty
- **Ultrawide / non-16:9 ROIs**: `DEFAULT_ROIS` are tuned on 16:9. Template *sizes* are height-scaled so vertical layout is invariant across same-height screens, but the *horizontal fraction* of a UI element shifts on ultrawide (the game anchors UI to screen edges / a centred safe area, not stretching it across the extra width) — a tight horizontal ROI then misses the element. `_roi_for_frame(roi, w, h)` fixes this without per-element anchor guessing: it keeps the accurate axis and searches the full extent of the distorted one — **wider than 16:9 → full width, keep the vertical band**; **taller than 16:9 → full height, keep the horizontal band**; 16:9 (within `detector_roi_aspect_tol`, default ±0.05) is untouched. ROI-first stays a speed win (a band is far cheaper than the full frame, and OCR stays scoped to the band) with the full-screen fallback still backing it up. Toggle off via `detector_roi_aspect_fix=false`. Mastery node *click* positions are corrected separately in `load_nodes` (see Capture).
- **Text template fast path**: `TEXT_TEMPLATES = frozenset(DEFAULT_ROIS.keys())` — all 11 keys. Text templates skip the Canny edge channel and use only 3 scales (`detector_text_scales`, default `[0.95, 1.00, 1.05]`), reducing matchTemplate calls from 14 to 3 (~4–5× faster). Non-text templates keep the full 7-scale + edge pipeline.
- Full pipeline scales: `[0.86, 0.92, 0.97, 1.00, 1.03, 1.08, 1.14]`
- Hybrid score (non-text): `0.62 × grayscale(equalizeHist) + 0.28 × Canny edges + up to 0.10 OCR bonus`
- Text score: `grayscale(equalizeHist)` only (edge channel skipped)
- **Default mode** (`detector_ocr_primary: true`, default): For text templates with OCR hints, OCR is a first-class confirmation signal rather than a +0.10 bonus. Pixel template matching of game UI text is fragile across hardware (GPU AA, font hinting, HDR, game settings all change pixels) — text content is what's actually invariant. Logic: if `image_score >= detector_ocr_skip_above` (default 0.75), skip OCR fast path; else run OCR; if hint matched, promote score to `max(image_score, detector_ocr_confirm_score)` (default 0.85). To prevent the per-key OCR cooldown from breaking the stability filter, an OCR confirmation is **cached** per key for the cooldown duration and applied to subsequent frames without re-running OCR (gated by `detector_ocr_cache_pixel_min`, default 0.15, to guard against the screen changing during cooldown). Uses tight 3-scale (`detector_text_scales`) gray-only matching with ROI-first + 0.94-penalty full-screen fallback.
- **Custom mode** (`detector_ocr_primary: false`, toggle in topbar): For users with custom-captured templates that differ from the defaults (different language, non-text content like icons, different in-game UI position, captured at non-standard scale). Custom mode bypasses every Default-mode assumption: (1) **OCR fully disabled** — no first-class confirmation, no +0.10 bonus, no OCR_HINTS lookup; (2) **Full 7-scale `detector_scales` range** used for all templates, not the tight 3-scale text path — handles templates captured at non-standard scales; (3) **Canny edge channel** only for non-text templates (`0.62 × gray + 0.28 × edges`); text templates (all current keys) run **gray-only** even in Custom mode, because text edges are noisy anti-aliasing and the gray channel matches text more reliably — this ~halves Custom's matchTemplate count (e.g. full-screen 4K ~3050ms → ~1150ms) with no accuracy cost on text. `detector_force_edges: true` restores the edge channel for all templates if a custom non-text/structural template needs it; (4) **No 0.94 full-screen penalty** — user's custom template may not appear at the DEFAULT_ROI position, so the full-screen result is treated as the genuine answer. ROI is still tried first for speed, but the fallback is unpenalised.
- **Full-screen fallback gating**: the ROI-miss full-screen search is the single most expensive per-check op (~85% of wait-state CPU; ~525ms gray / ~3s Custom at 4K). On the stable (`wait_for`) path, `_should_run_full(key, roi_score)` skips it when the ROI score is clearly cold (`roi_score < detector_full_gate_score`, default 0.40), running it only when the ROI hints the element may have drifted (score ≥ gate) or on a periodic safety sweep (every `detector_full_sweep_every` gated checks, default 4) so drift outside the ROI is still caught within a bounded number of checks. **Single-shot `detect(stable=False)` (click ops) always runs the full fallback** — gating never causes a one-off click to miss. Conservative by design: it only skips when the ROI is cold, never trading detection for speed. Measured ~3× less wait-state CPU in Default mode (468→153ms avg). Set `detector_full_sweep_every <= 1` to disable.
- **OCR pre-warming**: `OptionalOCR._ensure_loaded()` is kicked off in a background thread when `ScreenDetector` is constructed, so the first detection call doesn't eat the 1–2s onnxruntime model-load cost.
- **OCR cooldown**: `detector_ocr_cooldown` (default 1.0s) — minimum gap between actual OCR calls per template key. Prevents CPU spikes during long failed-detection streaks. Under OCR-primary, the confirmation cache uses this same duration.
- **Warning log surfaces OCR text**: when detection stalls for 3s, the warning includes `OCR: 'xxx'` showing what OCR read in the borderline zone — critical for diagnosing why a template isn't matching on a given user's machine.
- Soft threshold: actual cutoff is `max(0.45, threshold * 0.92)` — user's slider is a target, not a hard wall
- Stability filter: requires N consecutive frames (default 2) above the soft threshold; `stable=False` flag bypasses this for single-shot click ops
- Optional OCR: lazy-loads `rapidocr_onnxruntime` → `rapidocr` → `pytesseract`. Hint words in `OCR_HINTS` are multilingual (en/zh-tw/zh-cn). If no OCR backend is installed, detection still works
- `ScreenDetector.wait_for(frame_cb, key, template, threshold, stop_cb, interval, timeout, on_warn)` is the loop used by race.py / mastery.py; default `timeout=float('inf')`

### Automation modules (race.py, mastery.py, delete_cars.py)
- Each has a `run(cfg, stop_event, log_cb, status_cb, ...)` function
- Run in a daemon thread; `stop_event` signals shutdown
- **CJK IME / input handling — two-part design (all 4 scripts)**. A Traditional Chinese IME in native mode can consume keystrokes for composition *before the game reads them* (worst for Buy: Space=convert, Down=next candidate, Enter=confirm are exactly the IME candidate keys). History: v1.3.2 shipped scancode-*only* injection + an *unconditional* IME switch; both regressed users (held W not pressing on VK-path games; the forced switch clobbering users who'd already set English). v1.3.3 fixes both:
  - **(1) Dual key injection (`_send_vk`)**: sends **both** `wVk` (virtual key) **and** `wScan` (scancode via `MapVirtualKeyW`) in one event, **no** `KEYEVENTF_SCANCODE` flag. This feeds both the Windows message / VK path (`WM_KEYDOWN`/`GetAsyncKeyState`) *and* the DirectInput / Raw Input scancode path — strictly more compatible than VK-only (`wScan=0` → DirectInput gets scancode 0) or scancode-only (`wVk=0` → regresses VK-path games, notably the held `W`). Coverage: race.py + mastery.py have their own `_send_vk`; **delete_cars.py** has the extended-aware version and exposes `key_press` (public alias) the Buy worker imports. **Extended keys** (`_EXTENDED_VKS`: arrows, PgUp/PgDn/Home/End, Ins/Del, R-Ctrl/Alt) set `KEYEVENTF_EXTENDEDKEY` or they collide with the numpad block (Down `0x50` == numpad-2); delete_cars's `down` relies on this. Mastery's WASD nav uses `pydirectinput` (scancode), unchanged.
  - **(2) `capture.force_english_ime()` — conditional, non-destructive**: at run start it checks the foreground window's current input language via `GetKeyboardLayout(GetWindowThreadProcessId(hwnd))`; **if already English (LANGID primary `0x09`) it does nothing** and returns — never disturbing a user who manages their IME manually. Only when a non-English layout is active does it `LoadKeyboardLayoutW("00000409")` + `PostMessageW(WM_INPUTLANGCHANGEREQUEST)` (HKL as `c_void_p` so the 64-bit handle isn't truncated). Gated by config `auto_english_ime` (default true) at each call site — set false to skip entirely (for setups where "English" is a CJK IME in alphanumeric mode, which still reports a Chinese LANGID). Best-effort/non-fatal.
  - Mouse input is unaffected (IME is keyboard-only).
- race.py / mastery.py instantiate `ScreenDetector(cfg)` per run and call its `wait_for` / `detect`
- Per-template thresholds stored in config (keys like `thresh_start_menu`, `thresh_racing`, etc.)
- After 3s without detection: fires `warn_cb` with a red warning message that includes `best.source` and `best.score` for diagnostics
- wait_for() waits indefinitely (no timeout) until detected or stopped — **intentional design**, F9 is the recovery path

#### mastery.py — snake navigation
- `_nav_keys_for_loop(loop)` returns relative WASD keys for the infinite 3-column snake (col1 down, col2 up, col3 down, …)
- `start_loop = max(1, min(3, cfg.get("mastery_start_loop", 1)))` — which row the first car is on
- `loop_count` is initialised to `start_loop - 1`; a separate `car_num` counter starts at 0
- On the first car (`car_num == 1`) navigation is always skipped — user is already positioned there
- `max_cars` limit and log messages use `car_num` (1, 2, 3…), not `loop_count`

### Capture (capture.py)
- `CaptureSession`: listens for CAPS LOCK, opens fullscreen region selector, shows preview
- `NodeSession`: waits for CAPS LOCK, opens full screenshot for clicking 6 node positions
- ESC cancels at any stage — `_on_esc` also fires `on_cancel()` when not mid-capture (not just mid-capture)
- **Multi-capture fix**: `self._stop.set()` is called immediately before `self.callback()` in the success path, ensuring the old session's CAPS LOCK listener is torn down before the next session registers its own. This prevents duplicate listeners that previously broke the 2nd/3rd capture.
- Hooks are targeted (not unhook_all) to avoid killing the F9 toggle hotkey
- **Template rescaling**: `load_template` scales by height only (`scale = current_h / meta["screen_height"]`). Game UIs are laid out relative to vertical resolution; using an average of width+height was wrong for non-standard aspect ratios (e.g. 5K2K).
- **Node click rescaling (aspect-aware)**: `load_nodes(file, w, h, aspect_fix=True)` maps stored `x_ratio`/`y_ratio` through a **centred 16:9 content box** (`_content_box`, fit-contain) instead of naive `ratio × width`. Forza anchors menu UI to a centred 16:9 region (pillarboxed on ultrawide, letterboxed on tall screens), not stretched — so a 16:9 preset node at x_ratio 0.194 must land in that centred box on a 21:9 screen, not at 0.194×width. Verified against a real 5120×2160 capture: the 16:9 preset remaps to within 0–15px of the user's hand-captured nodes (well inside click tolerance), and same-aspect captures map to themselves (≤1px round-off). Reduces to naive scaling when capture & current aspect match, so 16:9 users are unaffected. Toggle via `nodes_aspect_fix` (config, default true). The model was confirmed empirically: 16:9 ratio 0.194 → predicted 0.271 → measured 0.2707 on 5K2K (centred-box, not naive=0.194 or left-anchored=0.145).
- **Frame capture reuse**: `grab_frame` uses a thread-local mss instance via `_get_sct()` (stored in `threading.local()` as `_tls.sct`), created lazily on first capture and reused for the life of the thread. Previously it built/destroyed `mss.MSS()` on every call — the detection loop grabs ~2×/sec indefinitely, so over a long run that leaked Windows GDI device-contexts/bitmaps until `grab()` returned black frames, which is why race/mastery grew more failure-prone the longer they ran. An mss instance is bound to its creating thread, hence thread-local rather than a global singleton. `grab_frame` has a one-time rebuild fallback: a non-`RuntimeError` exception (e.g. display/DC reset) closes the stale instance, recreates it once, and retries; `RuntimeError` (monitor-not-found / no-image) is re-raised. `list_monitors` / `get_monitor_dims` keep the one-shot `with mss.MSS()` — called rarely (startup) and possibly from the UI thread.

### Config (config.py)
- JSON file next to exe
- Keys include: lang, theme, toggle_key, capture_key, monitor_index, race_resolution, mastery_resolution, all thresh_* values, all *_wait values
- Mastery-specific timing keys: `mastery_check_interval` (min 0.3), `mastery_post_click_wait` (min 0.5), `mastery_post_key_wait` (min 0.8), `mastery_node_click_wait` (min 0.7)
- `mastery_start_loop` (int 1–3): which row the first car is on for Auto Unlock 22B
- `nodes_aspect_fix` (bool, default true): aspect-aware mastery node click remapping via the centred 16:9 content box (see Capture → Node click rescaling)
- `ui_scale` (str, default `"auto"`): UI scale factor — `"auto"` (resolution-derived) or a percentage like `"150%"`. Resolved by `config.resolve_ui_scale`; applied via CTk widget/window scaling (see UI → UI scale)
- `auto_english_ime` (bool, default true): at run start, switch the game window to English input **only if** a non-English layout is active (no-op when already English). Set false to never touch the IME — for users who manage it manually, esp. where "English" is a CJK IME in alphanumeric mode (still reports a Chinese LANGID, so the auto-skip wouldn't catch it). See Automation modules → CJK IME.
- Optional detector tuning keys: `detector_scales` (list of floats), `detector_text_scales` (list of floats), `detector_stable_frames` (int), `detector_enable_ocr` (bool), `detector_ocr_cooldown` (float seconds, default 1.0), `detector_ocr_primary` (bool, default **true** — OCR as first-class match signal; toggle via topbar Default/Custom segmented button), `detector_ocr_skip_above` (float, default 0.75), `detector_ocr_confirm_score` (float, default 0.85), `detector_ocr_cache_pixel_min` (float, default 0.15 — minimum pixel score for cached OCR confirmation to apply), `detector_full_gate_score` (float, default 0.40 — ROI score at/above which the full-screen fallback always runs), `detector_full_sweep_every` (int, default 4 — run the full-screen fallback every Nth gated check as a safety sweep; ≤1 disables gating), `detector_force_edges` (bool, default false — force Canny edge channel on for all templates incl. text), `detector_roi_aspect_fix` (bool, default true — expand ROIs along the distorted axis on non-16:9 screens), `detector_roi_aspect_tol` (float, default 0.05 — ± fraction of 16:9 treated as still-16:9)

### Log widget (log_widget.py)
- Thread-safe via queue
- `log(msg)` — normal text
- `log_warning(msg)` — red text (#ff4444) via tk.Text tag
- `log_section(msg)` — starts a new bounded loop section with `msg` as its header. Only the last `MAX_SECTIONS` (default 3) sections are retained; opening the 4th deletes the oldest from the top of both `self._lines` and the tk widget so the log doesn't grow unbounded across long runs. A blank separator line is inserted between sections (counts into the new section). Lines logged before the first `log_section` form an implicit "preamble" section (startup/template-load messages), trimmed once 3 loop sections exist.
- Section bookkeeping: `self._section_lens` tracks line count per live section (front = oldest). The hard `MAX_LINES` (1000) safety cap still applies and decrements `_section_lens` from the front to stay in sync. **Section headers must not contain embedded newlines** — the widget assumes one line per buffer entry, so a `\n` in a header would desync line accounting (this is why race.py's `-- Loop #N --` header dropped its leading `\n`).
- Wiring: `race.run` / `mastery.run` take an optional `section_cb` (falls back to `log_cb`); `main_window` passes `self._race_log.log_section` / `self._mastery_log.log_section`. Loop/car headers go through it. Buy/Delete tabs don't pass `section_cb`, so their logs are unsectioned (single growing preamble).

### Auto-updater (updater.py)
- Checks GitHub API on startup (2s delay)
- Downloads full zip, extracts to temp, bat replaces FAFE.exe + _internal/ + preset templates (1080p / 1440p / 2160p folders for both race and mastery_full, plus `templates/examples/`). Leaves `config.json` and `templates/.../custom/` folders untouched so user customisations persist across updates.
- Bat uses a retry loop on `copy /y` and gates `robocopy /PURGE` on _internal behind copy success — a locked FAFE.exe falls through to a `:fail` branch that relaunches the existing install instead of bricking it
- Template robocopy failures are non-fatal — the app is already updated before they run, so a missing/locked preset folder doesn't trigger the fail branch

## Key Design Decisions
- All UI strings go through `_at(key, lang, **kwargs)` in app_lang.py — never hardcode UI text
- Sliders save on mouse release only (not on drag)
- Slider minimums are set to the lowest safe values — going lower breaks automation because the game can't keep up
- Per-template threshold sliders in Setup panel (custom mode only shows retake buttons)
- Settings sliders clamp loaded values to slider range to handle stale config
- `keyboard.unhook_all()` is NEVER called — only targeted hook cleanup to preserve F9
- `wait_for` is intentionally infinite with no auto-retry — retrying detection without changing template/threshold yields the same result; user adjusts via sliders or recaptures
- All templates are text-based → `TEXT_TEMPLATES` covers all keys; never add a non-text template without also removing it from `TEXT_TEMPLATES` and verifying the edge channel improves accuracy

## GitHub
- Repo: https://github.com/Leoncrispybacon/Full-Auto-Forza-Edition
- Pages: https://leoncrispybacon.github.io/FAFE
- Latest release: v1.3.3

## Build
Run `build_app.bat` — produces `FAFE_dist/` with `FAFE.exe`, `_internal/`, `config.json`.
Release zip should contain the full `FAFE_dist/` contents.
The build bundles `rapidocr_onnxruntime` so OCR hints work out of the box; the ONNX models add ~50 MB to the dist.
