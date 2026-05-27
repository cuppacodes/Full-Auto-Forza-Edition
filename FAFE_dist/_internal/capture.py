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
import mss

import config

# ── mss screen capture ───────────────────────────────────────

def grab_frame(monitor_index: int) -> np.ndarray:
    """Capture game monitor via mss. Returns BGR frame."""
    with mss.MSS() as sct:
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

    scale = ((current_w / meta["screen_width"]) +
             (current_h / meta["screen_height"])) / 2
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


def load_nodes(nodes_file: str, current_w: int, current_h: int) -> list:
    with open(nodes_file, encoding="utf-8") as f:
        data = json.load(f)
    return [(int(n["x_ratio"] * current_w),
             int(n["y_ratio"] * current_h))
            for n in data["nodes"]]


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

    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
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
            import keyboard
            close_example()
            keyboard.unhook_all()
        except Exception:
            pass

    def _run(self):
        import keyboard
        triggered  = threading.Event()
        _in_capture = threading.Lock()

        def _on_caps(e):
            # Only set if not already processing a capture
            if not self._stop.is_set() and not _in_capture.locked():
                triggered.set()

        # Show example image if available
        if self.template_key and self.examples_dir:
            show_example(self.template_key, self.examples_dir)

        keyboard.on_press_key(self.capture_key, _on_caps, suppress=False)

        while not self._stop.is_set():
            if triggered.wait(timeout=0.1):
                triggered.clear()
                if self._stop.is_set():
                    break
                if not _in_capture.acquire(blocking=False):
                    continue   # already in a capture, skip
                try:
                    time.sleep(0.15)   # debounce
                    triggered.clear()  # discard any bounces during debounce

                    frame = grab_frame(self.monitor_index)
                    h, w  = frame.shape[:2]

                    roi = select_region(frame, self.window_title)
                    if roi is None:
                        if self.on_cancel:
                            self.on_cancel()
                    else:
                        x, y, rw, rh = roi
                        crop = frame[y:y+rh, x:x+rw]

                        cv2.imshow("Preview — Y to save | N to redo", crop)
                        key = cv2.waitKey(0) & 0xFF
                        cv2.destroyAllWindows()

                        if key in (ord('y'), ord('Y'), 13):
                            self.callback(crop, w, h)
                        else:
                            if self.on_cancel:
                                self.on_cancel("redo")
                finally:
                    triggered.clear()  # clear any caps lock presses during capture
                    _in_capture.release()

        keyboard.unhook_all()


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
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        import keyboard
        # Wait for Caps Lock via event hook
        triggered = threading.Event()
        keyboard.on_press_key(self.capture_key,
                              lambda e: triggered.set(), suppress=False)
        triggered.wait()
        keyboard.unhook_all()
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
        else:
            if self.on_cancel:
                self.on_cancel("redo")
