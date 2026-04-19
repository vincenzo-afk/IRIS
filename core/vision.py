"""
IRIS — Screen Vision Module
============================
Captures the screen at regular intervals, encodes frames as base64 JPEG,
and calls Gemini Vision to generate a natural-language description of
what's currently on the screen.
"""

import io
import base64
import threading
import time
import logging
from typing import Optional, Callable

try:
    import mss
    import mss.tools
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

from PIL import Image, ImageGrab
import google.generativeai as genai

from config import (
    GEMINI_API_KEY,
    GEMINI_VISION_MODEL,
    CAPTURE_INTERVAL,
    CAPTURE_QUALITY,
    CAPTURE_MAX_WIDTH,
    CAPTURE_MAX_HEIGHT,
    SCREENSHOTS_DIR,
)

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)


# ──────────────────────────────────────────────────────────────
# LOW-LEVEL CAPTURE
# ──────────────────────────────────────────────────────────────

def capture_screenshot() -> Image.Image:
    """Grab the full screen and return a PIL Image."""
    if MSS_AVAILABLE:
        with mss.mss() as sct:
            monitor = sct.monitors[0]   # monitor 0 = all screens combined
            raw = sct.grab(monitor)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    else:
        img = ImageGrab.grab()

    # Resize if oversized (reduces token cost)
    if img.width > CAPTURE_MAX_WIDTH or img.height > CAPTURE_MAX_HEIGHT:
        img.thumbnail((CAPTURE_MAX_WIDTH, CAPTURE_MAX_HEIGHT), Image.LANCZOS)

    return img


def image_to_base64(img: Image.Image) -> str:
    """Compress PIL Image to JPEG and return as base64 string."""
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=CAPTURE_QUALITY)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def save_screenshot(img: Image.Image, filename: str = "latest.jpg") -> str:
    """Save screenshot to the screenshots directory."""
    import os
    path = os.path.join(SCREENSHOTS_DIR, filename)
    img.save(path, format="JPEG", quality=CAPTURE_QUALITY)
    return path


# ──────────────────────────────────────────────────────────────
# GEMINI VISION
# ──────────────────────────────────────────────────────────────

_vision_model = genai.GenerativeModel(GEMINI_VISION_MODEL)


def analyze_screen(
    img: Optional[Image.Image] = None,
    context: str = "",
) -> str:
    """
    Send a screenshot to Gemini Vision and return a description.

    Args:
        img: PIL Image to analyze. If None, captures a fresh screenshot.
        context: Optional extra context / user goal to guide the analysis.

    Returns:
        Natural-language description of the screen.
    """
    if img is None:
        img = capture_screenshot()

    b64 = image_to_base64(img)

    system_prompt = (
        "You are IRIS, an AI screen reader. "
        "Describe the current screen state in detail: "
        "active window, visible text, UI elements, any errors or alerts, "
        "open applications, and anything noteworthy. "
        "Be concise but thorough."
    )
    if context:
        system_prompt += f"\n\nUser goal context: {context}"

    response = _vision_model.generate_content(
        [
            system_prompt,
            {
                "mime_type": "image/jpeg",
                "data": b64,
            },
        ]
    )

    return response.text.strip()


def read_text_on_screen(img: Optional[Image.Image] = None) -> str:
    """Extract all readable text from the screen (OCR-like via Gemini)."""
    if img is None:
        img = capture_screenshot()

    b64 = image_to_base64(img)
    response = _vision_model.generate_content(
        [
            "Extract ALL visible text from this screenshot verbatim. "
            "Return only the text content, preserving layout where possible.",
            {"mime_type": "image/jpeg", "data": b64},
        ]
    )
    return response.text.strip()


def find_element(description: str, img: Optional[Image.Image] = None) -> str:
    """
    Ask Gemini to locate a UI element described in natural language.
    Returns the approximate location (e.g. 'top-left button', 'center of screen').
    """
    if img is None:
        img = capture_screenshot()

    b64 = image_to_base64(img)
    prompt = (
        f"Locate this UI element on the screen: '{description}'. "
        "Describe its position (e.g. top-left, center, coordinates if visible). "
        "If not found, say 'NOT FOUND'."
    )
    response = _vision_model.generate_content(
        [prompt, {"mime_type": "image/jpeg", "data": b64}]
    )
    return response.text.strip()


# ──────────────────────────────────────────────────────────────
# BACKGROUND WATCHER (WATCH MODE)
# ──────────────────────────────────────────────────────────────

class ScreenWatcher:
    """
    Runs a background thread that periodically captures the screen
    and calls a callback with the latest analysis.
    """

    def __init__(
        self,
        interval: float = CAPTURE_INTERVAL,
        on_update: Optional[Callable[[str, Image.Image], None]] = None,
    ):
        self.interval = interval
        self.on_update = on_update
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.latest_description: str = ""
        self.latest_image: Optional[Image.Image] = None

    def start(self):
        """Start the background watching loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("ScreenWatcher started (interval=%.1fs)", self.interval)

    def stop(self):
        """Stop the watcher."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("ScreenWatcher stopped")

    def _loop(self):
        while self._running:
            try:
                img = capture_screenshot()
                desc = analyze_screen(img)
                self.latest_description = desc
                self.latest_image = img
                if self.on_update:
                    self.on_update(desc, img)
                logger.debug("Screen updated: %s", desc[:80])
            except Exception as exc:
                logger.error("ScreenWatcher error: %s", exc)
            time.sleep(self.interval)

    def get_context(self) -> str:
        """Return the latest screen description (blocking if needed)."""
        if not self.latest_description:
            img = capture_screenshot()
            self.latest_description = analyze_screen(img)
            self.latest_image = img
        return self.latest_description
