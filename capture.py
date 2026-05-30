# ============================================================
#  capture.py — Screenshot capture, template management,
#               node position recording
# ============================================================

import cv2
import numpy as np
import json
import os
import threading
import time
import ctypes
import mss

import config


# ── IME / input-language helper ───────────────────────────────

def force_english_ime() -> bool:
    """Switch the foreground (game) window's input language to English (US).

    A Traditional Chinese IME in native mode consumes keystrokes for
    composition *before* the game's input read — even injected scancodes — so
    scancode injection alone isn't enough on every setup. Taking the IME out of
    native mode is the only reliable fix: we ask the foreground window to switch
    its active input language to English (US), which removes the IME from the
    input chain for that window.

    Best-effort and non-fatal; returns True if the switch request was posted.
    Call after the game has focus (i.e. at the start of a run).
    """
    try:
        u32 = ctypes.windll.user32
        u32.LoadKeyboardLayoutW.restype  = ctypes.c_void_p
        u32.LoadKeyboardLayoutW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
        u32.GetForegroundWindow.restype  = ctypes.c_void_p
        u32.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                     ctypes.c_void_p, ctypes.c_void_p]

        KLF_ACTIVATE = 0x00000001
        WM_INPUTLANGCHANGEREQUEST = 0x0050
        # c_void_p so the 64-bit HKL handle isn't truncated when passed as
        # lParam (the #1 silent-failure trap for this call).
        hkl = u32.LoadKeyboardLayoutW("00000409", KLF_ACTIVATE)  # en-US
        if not hkl:
            return False
        hwnd = u32.GetForegroundWindow()
        if not hwnd:
            return False
        u32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, hkl)
        return True
    except Exception:
        return False


# ── mss screen capture ───────────────────────────────────────

# An mss instance is bound to the thread that created it, so we keep one
# per thread and reuse it across captures. Rebuilding mss.MSS() on every
# frame (the detection loop grabs ~2×/sec, indefinitely) leaks GDI
# device-contexts/bitmaps on Windows and eventually makes grab() return
# black frames — which is why long runs grew more failure-prone.
_tls = threading.local()


def _get_sct():
    """Return this thread's reusable mss instance, creating it on first use."""
    sct = getattr(_tls, "sct", None)
    if sct is None:
        sct = _tls.sct = mss.mss()
    return sct


def grab_frame(monitor_index: int) -> np.ndarray:
    """Capture game monitor via mss. Returns BGR frame."""
    sct = _get_sct()
    try:
        monitors = sct.monitors
        if monitor_index >= len(monitors):
            raise RuntimeError(
                f"Monitor {monitor_index} not found. "
                f"Only {len(monitors)-1} monitor(s) available.")
        shot = sct.grab(monitors[monitor_index])
    except RuntimeError:
        raise
    except Exception:
        # mss can fail transiently (e.g. display/DC reset). Rebuild once.
        try:
            sct.close()
        except Exception:
            pass
        _tls.sct = None
        sct = _get_sct()
        monitors = sct.monitors
        if monitor_index >= len(monitors):
            raise RuntimeError(
                f"Monitor {monitor_index} not found. "
                f"Only {len(monitors)-1} monitor(s) available.")
        shot = sct.grab(monitors[monitor_index])
    if shot is None:
        raise RuntimeError(
            f"Monitor {monitor_index} returned no image. "
            f"Check if the monitor is active.")
    return cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)


def list_monitors() -> list:
    with mss.MSS() as sct:
        return [
            {"index": i, "width": m["width"], "height": m["height"],
             "left": m["left"], "top": m["top"]}
            for i, m in enumerate(sct.monitors[1:], start=1)
        ]


def get_monitor_dims(monitor_index: int):
    with mss.MSS() as sct:
        monitors = sct.monitors
        if monitor_index >= len(monitors) or monitor_index < 1:
            # Fall back to primary monitor
            monitor_index = next(
                (i for i, m in enumerate(monitors[1:], 1)
                 if m['left'] == 0 and m['top'] == 0), 1)
        m = monitors[monitor_index]
        return m["width"], m["height"], m["left"], m["top"]


# ── Template save / load ──────────────────────────────────────

def save_template(folder: str, key: str, crop: np.ndarray,
                  screen_w: int, screen_h: int):
    """Save a BGR crop and its resolution metadata."""
    os.makedirs(folder, exist_ok=True)
    img_path  = os.path.join(folder, f"{key}.png")
    meta_path = os.path.join(folder, f"{key}.json")
    success, buf = cv2.imencode('.png', crop)
    if success:
        with open(img_path, 'wb') as f:
            f.write(buf.tobytes())
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"screen_width": screen_w, "screen_height": screen_h}, f)


def load_template(folder: str, key: str,
                  current_w: int, current_h: int,
                  grayscale: bool = True) -> tuple:
    """
    Load a template and rescale it to current resolution.
    Returns (img, scale) or raises FileNotFoundError.
    """
    img_path  = os.path.join(folder, f"{key}.png")
    meta_path = os.path.join(folder, f"{key}.json")

    if not os.path.exists(img_path) or not os.path.exists(meta_path):
        raise FileNotFoundError(f"Template '{key}' not found in {folder}")

    flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
    with open(img_path, 'rb') as f:
        buf = np.frombuffer(f.read(), dtype=np.uint8)
    img = cv2.imdecode(buf, flag)

    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    # Scale by height only: game UIs are laid out relative to vertical
    # resolution, not an average of width and height.  Averaging breaks
    # on mixed aspect ratios (e.g. a 16:9 template used on a 21:9 screen):
    # the width ratio inflates the scale and the template ends up the wrong
    # size even though the actual UI element is pixel-identical in height.
    scale = current_h / meta["screen_height"]
    if abs(scale - 1.0) > 0.02:
        nw = max(1, int(img.shape[1] * scale))
        nh = max(1, int(img.shape[0] * scale))
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)

    return img, scale


def template_exists(folder: str, key: str) -> bool:
    return (os.path.exists(os.path.join(folder, f"{key}.png")) and
            os.path.exists(os.path.join(folder, f"{key}.json")))


# ── Node save / load ──────────────────────────────────────────

def save_nodes(nodes_file: str, nodes: list,
               screen_w: int, screen_h: int):
    data = {
        "screen_width":  screen_w,
        "screen_height": screen_h,
        "nodes": [{"x_ratio": round(x / screen_w, 6),
                   "y_ratio": round(y / screen_h, 6)}
                  for x, y in nodes]
    }
    os.makedirs(os.path.dirname(nodes_file), exist_ok=True)
    with open(nodes_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


_REF_ASPECT = 16.0 / 9.0


def _content_box(screen_w: int, screen_h: int, ref: float = _REF_ASPECT):
    """Pixel rect (x, y, w, h) of a centred `ref`-aspect UI area fit (contain)
    into the screen.  Forza anchors menu UI to a centred 16:9 box rather than
    stretching it, so on non-16:9 screens the box is pillarboxed (wide screen,
    bars left/right) or letterboxed (tall screen, bars top/bottom).  On a 16:9
    screen the box equals the full screen."""
    if screen_w / max(1, screen_h) >= ref:
        box_h = float(screen_h)
        box_w = screen_h * ref
    else:
        box_w = float(screen_w)
        box_h = screen_w / ref
    box_x = (screen_w - box_w) / 2.0
    box_y = (screen_h - box_h) / 2.0
    return box_x, box_y, box_w, box_h


def load_nodes(nodes_file: str, current_w: int, current_h: int,
               aspect_fix: bool = True) -> list:
    with open(nodes_file, encoding="utf-8") as f:
        data = json.load(f)
    nodes = data["nodes"]
    src_w = data.get("screen_width", current_w)
    src_h = data.get("screen_height", current_h)

    # Naive width/height scaling is only correct when the capture and current
    # screen share an aspect ratio.  When they differ (e.g. a 16:9 preset on a
    # 21:9 ultrawide), the UI is anchored to a centred 16:9 box, not stretched
    # across the extra width — so map each node through the source's content
    # box into the current screen's content box.  This reduces to naive
    # scaling when the aspects match (verified: 5120x2160 custom capture maps
    # to itself), so it's safe to apply unconditionally for same-aspect cases.
    if not aspect_fix or src_w <= 0 or src_h <= 0:
        return [(int(n["x_ratio"] * current_w),
                 int(n["y_ratio"] * current_h)) for n in nodes]

    sx, sy, sw, sh = _content_box(src_w, src_h)
    cx, cy, cw, ch = _content_box(current_w, current_h)
    out = []
    for n in nodes:
        # node pixel within the source's centred 16:9 box -> box fraction
        cfx = (n["x_ratio"] * src_w - sx) / sw
        cfy = (n["y_ratio"] * src_h - sy) / sh
        # map that fraction onto the current screen's centred 16:9 box
        out.append((int(round(cx + cfx * cw)),
                    int(round(cy + cfy * ch))))
    return out


def nodes_exist(nodes_file: str) -> bool:
    return os.path.exists(nodes_file)


# ── Example image window ────────────────────────────────────

import queue as _queue
_example_queue = _queue.Queue()
_example_win_ref = [None]   # holds the CTkToplevel


def show_example(key: str, examples_dir: str):
    """
    Show an example image in a tkinter Toplevel window.
    Called from the main thread via after().
    """
    img_path = os.path.join(examples_dir, f'{key}.png')
    if not os.path.exists(img_path):
        return
    # Store path for main thread to pick up
    _example_queue.put(('show', key, img_path))


def close_example():
    """Signal main thread to close the example window."""
    _example_queue.put(('close', None, None))


# ── Region selection (OpenCV drag window) ─────────────────────

def select_region(frame: np.ndarray, window_title: str):
    """
    Show frame in a window, let user drag-select a region.
    Returns (x, y, w, h) in original resolution, or None if cancelled.
    """
    display_scale = 1.0
    if frame.shape[0] > 860:
        display_scale = 860 / frame.shape[0]
        display = cv2.resize(frame, None,
                             fx=display_scale, fy=display_scale)
    else:
        display = frame.copy()

    dh, dw = display.shape[:2]

    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_title, dw, dh)
    cv2.setWindowProperty(window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Bring to foreground
    try:
        import ctypes
        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 3)   # SW_MAXIMIZE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except Exception:
        pass

    roi = cv2.selectROI(window_title, display,
                        showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()

    x, y, w, h = roi
    if w == 0 or h == 0:
        return None
    return (int(x / display_scale), int(y / display_scale),
            int(w / display_scale), int(h / display_scale))


# ── Caps Lock capture session ─────────────────────────────────

class CaptureSession:
    """
    Listens for Caps Lock keypresses in a background thread.
    On each press: grabs a frame, opens drag-select, calls callback.

    callback(crop, frame_w, frame_h) is called on successful capture.
    """

    def __init__(self, monitor_index: int, window_title: str,
                 callback, on_cancel=None, capture_key='caps lock',
                 template_key=None, examples_dir=None):
        self.monitor_index = monitor_index
        self.window_title  = window_title
        self.callback      = callback
        self.on_cancel     = on_cancel
        self.capture_key   = capture_key
        self.template_key  = template_key
        self.examples_dir  = examples_dir
        self._stop         = threading.Event()
        self._thread       = None

    def start(self):
        import keyboard
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        try:
            close_example()
        except Exception:
            pass

    def _run(self):
        import keyboard
        triggered  = threading.Event()
        _in_capture = threading.Lock()

        def _caps_pressed():
            # Only set if not already processing a capture
            if not self._stop.is_set() and not _in_capture.locked():
                triggered.set()

        # Show example image if available
        if self.template_key and self.examples_dir:
            show_example(self.template_key, self.examples_dir)

        # Use add_hotkey (same mechanism as the F9 global toggle) so the key
        # fires system-wide even when the game window has focus.
        # on_press_key can be focus-dependent in some Windows configurations.
        cap_hook = keyboard.add_hotkey(self.capture_key, _caps_pressed, suppress=False)

        # ESC cancels at any point during waiting.
        # If we're mid-capture (_in_capture held), the selectROI / waitKey
        # paths already handle cancellation — don't double-fire on_cancel.
        def _on_esc(e):
            self._stop.set()
            if not _in_capture.locked() and self.on_cancel:
                self.on_cancel()
        esc_hook = keyboard.on_press_key('esc', _on_esc, suppress=False)

        while not self._stop.is_set():
            if triggered.wait(timeout=0.1):
                triggered.clear()
                if self._stop.is_set():
                    break
                if not _in_capture.acquire(blocking=False):
                    continue
                try:
                    time.sleep(0.15)
                    triggered.clear()

                    frame = grab_frame(self.monitor_index)
                    h, w  = frame.shape[:2]

                    roi = select_region(frame, self.window_title)
                    if roi is None:
                        self._stop.set()
                        if self.on_cancel:
                            self.on_cancel()
                    else:
                        x, y, rw, rh = roi
                        crop = frame[y:y+rh, x:x+rw]

                        cv2.imshow("Preview — ENTER to save | ESC to cancel", crop)
                        # Bring preview to foreground
                        try:
                            import ctypes as _ct
                            _hw = _ct.windll.user32.FindWindowW(None, "Preview — ENTER to save | ESC to cancel")
                            if _hw:
                                _ct.windll.user32.ShowWindow(_hw, 9)
                                _ct.windll.user32.SetForegroundWindow(_hw)
                        except Exception:
                            pass
                        key = cv2.waitKey(0) & 0xFF
                        cv2.destroyAllWindows()

                        if key in (ord('y'), ord('Y'), 13):
                            # Stop listening before handing off — prevents the
                            # loop from picking up the next CAPS LOCK press
                            # while _advance_session() is still spinning up
                            # the new session, which broke multi-capture.
                            self._stop.set()
                            self.callback(crop, w, h)
                        else:
                            self._stop.set()
                            if self.on_cancel:
                                self.on_cancel()
                finally:
                    triggered.clear()
                    _in_capture.release()

        try:
            keyboard.remove_hotkey(cap_hook)
        except Exception:
            pass
        try:
            keyboard.unhook(esc_hook)
        except Exception:
            pass


# ── Node click session ────────────────────────────────────────

class NodeSession:
    """
    Shows a screenshot and collects 6 mouse clicks for node positions.
    callback(nodes, screen_w, screen_h) called when all 6 are confirmed.
    """

    def __init__(self, monitor_index: int, callback, on_cancel=None,
                 capture_key='caps lock'):
        self.monitor_index = monitor_index
        self.callback      = callback
        self.on_cancel     = on_cancel
        self.capture_key   = capture_key

    def start(self):
        self._stop = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self._stop.set()
        try:
            close_example()
        except Exception:
            pass

    def _run(self):
        import keyboard
        # Wait for Caps Lock (or ESC/stop to cancel)
        triggered  = threading.Event()
        cancelled  = threading.Event()

        def _cap_pressed():
            triggered.set()
        def _on_esc(e):
            cancelled.set()
            triggered.set()

        # Use add_hotkey for the same reason as CaptureSession — ensures the
        # key fires system-wide regardless of which window has focus.
        cap_hook = keyboard.add_hotkey(self.capture_key, _cap_pressed, suppress=False)
        esc_hook = keyboard.on_press_key('esc', _on_esc, suppress=False)

        # Poll so stop() can also interrupt the wait
        while not triggered.is_set() and not self._stop.is_set():
            triggered.wait(timeout=0.1)

        try:
            keyboard.remove_hotkey(cap_hook)
        except Exception:
            pass
        try:
            keyboard.unhook(esc_hook)
        except Exception:
            pass

        if cancelled.is_set() or self._stop.is_set():
            if self.on_cancel:
                self.on_cancel()
            return
        time.sleep(0.1)

        frame = grab_frame(self.monitor_index)
        h, w  = frame.shape[:2]

        scale = 1.0
        if frame.shape[0] > 860:
            scale   = 860 / frame.shape[0]
            display = cv2.resize(frame, None, fx=scale, fy=scale)
        else:
            display = frame.copy()

        clicks = []

        def on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN and len(clicks) < 6:
                clicks.append((int(x / scale), int(y / scale)))

        win = "Click 6 nodes in order | ESC to cancel"
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win, display.shape[1], display.shape[0])

        # Bring to foreground
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, win)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

        cv2.setMouseCallback(win, on_mouse)

        while len(clicks) < 6:
            img = display.copy()
            for i, (cx, cy) in enumerate(clicks):
                dx, dy = int(cx * scale), int(cy * scale)
                cv2.circle(img, (dx, dy), 14, (0, 255, 0), 3)
                cv2.putText(img, str(i+1), (dx-5, dy+5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(img, f"Click node {len(clicks)+1}/6",
                        (20, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.9, (0, 220, 255), 2)
            cv2.imshow(win, img)
            k = cv2.waitKey(16)
            if k == 27:
                cv2.destroyAllWindows()
                if self.on_cancel:
                    self.on_cancel()
                return

        # All 6 clicked — show final and ask Y/N
        img = display.copy()
        for i, (cx, cy) in enumerate(clicks):
            dx, dy = int(cx * scale), int(cy * scale)
            cv2.circle(img, (dx, dy), 14, (0, 255, 0), 3)
            cv2.putText(img, str(i+1), (dx-5, dy+5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(img, "All 6! Y=save  N=redo",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        cv2.imshow(win, img)
        key = cv2.waitKey(0) & 0xFF
        cv2.destroyAllWindows()

        if key in (ord('y'), ord('Y'), 13):
            self.callback(clicks, w, h)
        else:  # ESC or anything else cancels
            if self.on_cancel:
                self.on_cancel()
