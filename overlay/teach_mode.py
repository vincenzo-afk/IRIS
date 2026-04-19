"""
IRIS — TEACH Mode
==================
When active, listens to the cursor position, grabs a small region
around the cursor, and asks Gemini to explain what the user is hovering over.
Shows the explanation via the CursorWidget overlay.
"""

import threading
import time
import logging
from typing import Optional

from PIL import Image

from core.vision import capture_screenshot, analyze_screen
from overlay.cursor_widget import CursorWidget
from core.automation import CursorTracker
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_VISION_MODEL
from core.vision import image_to_base64

logger = logging.getLogger(__name__)
genai.configure(api_key=GEMINI_API_KEY)

_model = genai.GenerativeModel(GEMINI_VISION_MODEL)

HOVER_REGION_SIZE = 200       # px around cursor to crop
HOVER_DEBOUNCE_SEC = 1.5      # Wait before triggering explanation
MIN_MOVE_THRESHOLD = 40       # Minimum pixel movement before re-triggering


class TeachMode:
    """
    TEACH mode manager.
    Polls cursor position; when cursor settles, asks Gemini to explain the UI element.
    """

    def __init__(self, widget: CursorWidget):
        self.widget = widget
        self.tracker = CursorTracker()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_x = 0
        self._last_y = 0
        self._settled_since = 0.0

    def start(self):
        if self._running:
            return
        self._running = True
        self.tracker.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("TeachMode started")

    def stop(self):
        self._running = False
        self.tracker.stop()
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("TeachMode stopped")

    def _loop(self):
        while self._running:
            cx, cy = self.tracker.position

            # Detect movement
            moved = abs(cx - self._last_x) + abs(cy - self._last_y)

            if moved > MIN_MOVE_THRESHOLD:
                # Cursor is moving — reset timer
                self._last_x = cx
                self._last_y = cy
                self._settled_since = time.time()
            else:
                # Cursor is settled — check if long enough
                settled_duration = time.time() - self._settled_since
                if settled_duration >= HOVER_DEBOUNCE_SEC and self._settled_since > 0:
                    self._settled_since = 0.0   # Don't re-trigger immediately
                    self._explain_hover(cx, cy)

            time.sleep(0.2)

    def _explain_hover(self, x: int, y: int):
        """Capture a region around (x, y) and ask Gemini to explain it."""
        try:
            img = capture_screenshot()
            region = self._crop_region(img, x, y)
            b64 = image_to_base64(region)

            prompt = (
                "The user is hovering their cursor over a part of the screen. "
                "Explain what this UI element is, what it does, and how to use it. "
                "Be concise (2-3 sentences max). "
                "If it's code, explain the logic. "
                "If it's unknown or just background, say 'Nothing notable here.'"
            )

            response = _model.generate_content(
                [prompt, {"mime_type": "image/jpeg", "data": b64}]
            )
            explanation = response.text.strip()

            if "nothing notable" not in explanation.lower():
                self.widget.show_message(f"💡 {explanation}", duration_ms=5000)
                logger.debug("Teach: %s", explanation[:80])

        except Exception as exc:
            logger.error("TeachMode explain error: %s", exc)

    @staticmethod
    def _crop_region(img: Image.Image, cx: int, cy: int, size: int = HOVER_REGION_SIZE) -> Image.Image:
        """Crop a square region around the cursor."""
        half = size // 2
        left = max(0, cx - half)
        top = max(0, cy - half)
        right = min(img.width, cx + half)
        bottom = min(img.height, cy + half)
        return img.crop((left, top, right, bottom))
