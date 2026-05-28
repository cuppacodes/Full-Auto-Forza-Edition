"""
Soft-scored screen detection for FAFE.

The detector keeps the existing screenshot templates but makes matching less
fragile by combining ROI-first search, multi-scale matching, contrast
normalization, edge matching, stability, and optional OCR evidence.
"""

from dataclasses import dataclass
from typing import Callable, Iterable, Optional
import os
import re
import time

import cv2
import numpy as np


Rect = tuple[float, float, float, float]
Point = tuple[int, int]


@dataclass
class MatchResult:
    matched: bool
    score: float
    confidence: float
    location: Point
    scale: float
    source: str
    ocr_text: str = ""


DEFAULT_ROIS: dict[str, Rect] = {
    # x, y, width, height ratios. These are intentionally generous; the
    # detector falls back to full-screen search with a small score penalty.
    "start_menu": (0.20, 0.15, 0.60, 0.70),
    "racing": (0.00, 0.55, 0.50, 0.45),   # ANNA prompt — bottom-left corner
    "restart_menu": (0.25, 0.20, 0.55, 0.65),
    "confirm": (0.20, 0.20, 0.65, 0.65),
    "mastery_ride_car": (0.00, 0.10, 0.55, 0.80),
    "mastery_esc_hint": (0.00, 0.00, 1.00, 0.35),
    "mastery_upgrade_item": (0.00, 0.10, 0.65, 0.80),
    "mastery_mastery_item": (0.00, 0.10, 0.65, 0.80),
    "mastery_anchor": (0.00, 0.00, 1.00, 0.45),
    "mastery_my_cars": (0.00, 0.10, 0.65, 0.80),
    "mastery_sort_recent": (0.00, 0.10, 0.80, 0.80),
}


OCR_HINTS: dict[str, tuple[str, ...]] = {
    "start_menu": ("start", "race", "開始", "開始賽事", "开始"),
    "racing": ("anna", "ANNA"),
    "restart_menu": ("restart", "重新開始", "重新开始", "重新"),
    "confirm": ("confirm", "yes", "確認", "确认", "是"),
    "mastery_ride_car": ("ride", "car", "駕駛", "驾驶"),
    "mastery_esc_hint": ("esc", "Esc", "ESC"),
    "mastery_upgrade_item": ("upgrade", "tuning", "升級", "升级"),
    "mastery_mastery_item": ("mastery", "熟練", "熟练"),
    "mastery_anchor": ("車輛熟練度", "车辆熟练度", "mastery", "熟練", "熟练"),
    "mastery_my_cars": ("my cars", "車庫", "车库"),
    "mastery_sort_recent": ("recent", "recently", "新增", "最近"),
}

# All template images capture text UI elements. Edge matching on text is
# noisy (anti-aliasing artifacts) and adds cost without reliability benefit,
# so these keys all use the fast grayscale-only, 3-scale path.
# Keys NOT listed here fall back to the full multi-scale + edge pipeline.
TEXT_TEMPLATES: frozenset[str] = frozenset(DEFAULT_ROIS.keys())


def _clip_roi(frame: np.ndarray, roi: Optional[Rect]) -> tuple[np.ndarray, int, int]:
    if roi is None:
        return frame, 0, 0
    h, w = frame.shape[:2]
    x = max(0, min(w - 1, int(roi[0] * w)))
    y = max(0, min(h - 1, int(roi[1] * h)))
    rw = max(1, min(w - x, int(roi[2] * w)))
    rh = max(1, min(h - y, int(roi[3] * h)))
    return frame[y:y + rh, x:x + rw], x, y


def _prepare_gray(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.equalizeHist(img)


def _prepare_edges(img: np.ndarray) -> np.ndarray:
    gray = _prepare_gray(img)
    return cv2.Canny(gray, 60, 160)


def _scaled_templates(template: np.ndarray, scales: Iterable[float]):
    th, tw = template.shape[:2]
    for scale in scales:
        nw = max(8, int(tw * scale))
        nh = max(8, int(th * scale))
        if nw == tw and nh == th:
            yield scale, template
        else:
            yield scale, cv2.resize(template, (nw, nh), interpolation=cv2.INTER_AREA)


def _best_template_match(screen: np.ndarray, template: np.ndarray,
                         scales: Iterable[float]) -> tuple[float, Point, float]:
    best_conf = -1.0
    best_loc = (0, 0)
    best_scale = 1.0
    sh, sw = screen.shape[:2]
    for scale, tpl in _scaled_templates(template, scales):
        th, tw = tpl.shape[:2]
        if th > sh or tw > sw:
            continue
        result = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
        _, conf, _, loc = cv2.minMaxLoc(result)
        if conf > best_conf:
            best_conf = float(conf)
            best_loc = (int(loc[0] + tw // 2), int(loc[1] + th // 2))
            best_scale = float(scale)
    return max(0.0, best_conf), best_loc, best_scale


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


class OptionalOCR:
    """Tiny lazy OCR facade.

    OCR is deliberately optional. RapidOCR is preferred because it can be
    bundled without a separate Tesseract executable. If no OCR backend is
    installed, detection still runs normally.
    """

    def __init__(self):
        self._loaded = False
        self._reader: Optional[Callable[[np.ndarray], str]] = None

    def available(self) -> bool:
        self._ensure_loaded()
        return self._reader is not None

    def read(self, img: np.ndarray) -> str:
        self._ensure_loaded()
        if self._reader is None:
            return ""
        try:
            return self._reader(img)
        except Exception:
            return ""

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True
        try:
            from rapidocr_onnxruntime import RapidOCR
            engine = RapidOCR()

            def _read(img):
                result, _ = engine(img)
                if not result:
                    return ""
                return " ".join(str(item[1]) for item in result if len(item) > 1)

            self._reader = _read
            return
        except Exception:
            pass
        try:
            from rapidocr import RapidOCR
            engine = RapidOCR()

            def _read(img):
                result = engine(img)
                items = getattr(result, "txts", None)
                if items is not None:
                    return " ".join(str(x) for x in items)
                if not result:
                    return ""
                return " ".join(str(item[1]) for item in result if len(item) > 1)

            self._reader = _read
            return
        except Exception:
            pass
        try:
            import pytesseract
            self._reader = lambda img: pytesseract.image_to_string(img)
        except Exception:
            self._reader = None


class ScreenDetector:
    # OCR can add at most this much to the score. Used to decide whether
    # running OCR could possibly flip the match decision.
    OCR_MAX_BONUS = 0.10

    def __init__(self, cfg: dict | None = None, debug_dir: str | None = None):
        self.cfg = cfg or {}
        self.debug_dir = debug_dir
        self._ocr = OptionalOCR()
        self._history: dict[str, list[float]] = {}
        self.scales = self.cfg.get(
            "detector_scales",
            [0.86, 0.92, 0.97, 1.00, 1.03, 1.08, 1.14],
        )
        # Reduced scale set for text-based templates: the game UI renders text
        # at a fixed size per resolution, so 3 nearby scales are sufficient.
        # Configurable via "detector_text_scales" in config.json.
        self._text_scales: list[float] = self.cfg.get(
            "detector_text_scales",
            [0.95, 1.00, 1.05],
        )
        self.stable_frames = int(self.cfg.get("detector_stable_frames", 2))
        # Multi-resolution pyramid: combine a full-res and half-res match score
        # to improve robustness across different GPUs/drivers/game settings.
        # Pixel-level rendering differences (AA, font hinting) vanish at 50%
        # resolution while UI layout remains clearly recognisable.
        # Disable via "detector_enable_pyramid": false in config.json to revert
        # to the original single-resolution behaviour.
        self._pyramid_enabled: bool = bool(
            self.cfg.get("detector_enable_pyramid", True))
        self._pyramid_full_weight: float = float(
            self.cfg.get("detector_pyramid_full_weight", 0.6))
        # Cache prepared (gray, edge) versions of each template numpy array —
        # full-res and half-res — so we don't redo equalizeHist + Canny +
        # resize on every frame. Keyed by id(template).
        self._template_cache: dict[
            int, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}

    def _prepared_template(
            self, template: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Returns (gray, edges, gray_half, edge_half), all cached."""
        cache_key = id(template)
        cached = self._template_cache.get(cache_key)
        if cached is None:
            gray = _prepare_gray(template)
            edges = _prepare_edges(template)
            gray_half = cv2.resize(gray,  None, fx=0.5, fy=0.5,
                                   interpolation=cv2.INTER_AREA)
            edge_half = cv2.resize(edges, None, fx=0.5, fy=0.5,
                                   interpolation=cv2.INTER_AREA)
            cached = (gray, edges, gray_half, edge_half)
            self._template_cache[cache_key] = cached
        return cached

    def detect(self, frame: np.ndarray, key: str, template: np.ndarray,
               threshold: float, stable: bool = True) -> MatchResult:
        roi = DEFAULT_ROIS.get(key)
        roi_result = self._detect_in_area(
            frame, key, template, threshold, roi, "roi", stable)
        if roi_result.matched:
            return roi_result

        full_result = self._detect_in_area(
            frame, key, template, threshold, None, "full", False)
        # Full-screen fallback is useful on unusual UI layouts, but slightly
        # discounted so normal ROI hits win.
        full_result.score *= 0.94
        full_result.matched = (
            self._stable_match(f"{key}:full", full_result.score, threshold)
            if stable else full_result.score >= max(0.45, threshold * 0.92)
        )
        return full_result

    def wait_for(self, frame_cb: Callable[[], np.ndarray], key: str,
                 template: np.ndarray, threshold: float,
                 stop_cb: Callable[[], bool], interval: float,
                 timeout: float = float("inf"),
                 on_warn: Callable[[MatchResult], None] | None = None) -> MatchResult:
        start = time.time()
        warned = False
        best = MatchResult(False, 0.0, 0.0, (0, 0), 1.0, "none")
        while time.time() - start < timeout:
            if stop_cb():
                return best
            result = self.detect(frame_cb(), key, template, threshold)
            if result.score > best.score:
                best = result
            if result.matched:
                return result
            if not warned and time.time() - start >= 3.0:
                warned = True
                if on_warn:
                    on_warn(best)
            time.sleep(interval)
        return best

    def _detect_in_area(self, frame: np.ndarray, key: str, template: np.ndarray,
                        threshold: float, roi: Optional[Rect],
                        source: str, stable: bool) -> MatchResult:
        area, off_x, off_y = _clip_roi(frame, roi)
        soft_threshold = max(0.45, threshold * 0.92)

        gray_area = _prepare_gray(area)
        gray_tpl, edge_tpl, gray_tpl_half, edge_tpl_half = \
            self._prepared_template(template)

        # Text-heavy templates (those with OCR hints) don't benefit from edge
        # matching — anti-aliasing makes text edges noisy — and the game UI is
        # rendered at a fixed scale, so 3 scale variants are sufficient.
        # This drops from 14 matchTemplate calls (7 scales × 2 channels) down
        # to 3, giving a ~4–5× speedup for the common path.
        is_text_template = key in TEXT_TEMPLATES
        if is_text_template:
            scales = self._text_scales
            gray_conf, gray_loc, gray_scale = _best_template_match(
                gray_area, gray_tpl, scales)
            full_score = gray_conf  # edge channel skipped for text
        else:
            gray_conf, gray_loc, gray_scale = _best_template_match(
                gray_area, gray_tpl, self.scales)
            edge_area = _prepare_edges(area)
            edge_conf, _, _ = _best_template_match(edge_area, edge_tpl, self.scales)
            full_score = (gray_conf * 0.62) + (edge_conf * 0.28)

        # ── Half-resolution pass ──────────────────────────────────────────────
        # Downscale both frame area and template to 50 % before matching.
        # Pixel-level rendering differences (GPU AA, font hinting, driver
        # variations) that cause cross-hardware score drops are averaged out
        # by the downscale while the UI layout remains clearly recognisable.
        # A single scale (1.0) is sufficient — both sides are halved equally.
        # Disable with "detector_enable_pyramid": false in config.json.
        if self._pyramid_enabled:
            gray_half = cv2.resize(gray_area, None, fx=0.5, fy=0.5,
                                   interpolation=cv2.INTER_AREA)
            if is_text_template:
                half_conf, _, _ = _best_template_match(
                    gray_half, gray_tpl_half, [1.0])
                half_score = half_conf
            else:
                edge_half = cv2.resize(edge_area, None, fx=0.5, fy=0.5,
                                       interpolation=cv2.INTER_AREA)
                hg, _, _ = _best_template_match(gray_half, gray_tpl_half, [1.0])
                he, _, _ = _best_template_match(edge_half, edge_tpl_half, [1.0])
                half_score = (hg * 0.62) + (he * 0.28)
            w = self._pyramid_full_weight
            image_score = full_score * w + half_score * (1.0 - w)
        else:
            image_score = full_score

        # OCR is the expensive step (~100-300ms per call). Only run it when
        # the image-only score is in the borderline zone where the OCR bonus
        # could actually change the match decision. Skip when we're already
        # clearly above, or clearly too far below to be saved by OCR.
        if image_score >= soft_threshold or image_score + self.OCR_MAX_BONUS < soft_threshold:
            ocr_bonus, ocr_text = 0.0, ""
        else:
            ocr_bonus, ocr_text = self._ocr_bonus(area, key)

        score = image_score + ocr_bonus
        loc = (gray_loc[0] + off_x, gray_loc[1] + off_y)
        matched = (score >= soft_threshold if not stable
                   else self._stable_match(f"{key}:{source}", score, threshold))
        return MatchResult(matched, score, gray_conf, loc, gray_scale, source,
                           ocr_text=ocr_text)

    def _ocr_bonus(self, area: np.ndarray, key: str) -> tuple[float, str]:
        hints = OCR_HINTS.get(key)
        if not hints or not self.cfg.get("detector_enable_ocr", True):
            return 0.0, ""
        text = self._ocr.read(area)
        if not text:
            return 0.0, ""
        norm = _normalize_text(text)
        if any(_normalize_text(hint) in norm for hint in hints):
            return 0.10, text.strip()
        return 0.0, text.strip()

    def _stable_match(self, key: str, score: float, threshold: float) -> bool:
        needed = max(1, self.stable_frames)
        hist = self._history.setdefault(key, [])
        hist.append(score)
        del hist[:-needed]
        if len(hist) < needed:
            return False
        soft_threshold = max(0.45, threshold * 0.92)
        return all(v >= soft_threshold for v in hist)

    def save_debug(self, frame: np.ndarray, key: str, result: MatchResult):
        if not self.debug_dir:
            return
        try:
            os.makedirs(self.debug_dir, exist_ok=True)
            stamp = int(time.time())
            path = os.path.join(
                self.debug_dir,
                f"{stamp}_{key}_{result.source}_{result.score:.2f}.png",
            )
            cv2.imwrite(path, frame)
        except Exception:
            pass
