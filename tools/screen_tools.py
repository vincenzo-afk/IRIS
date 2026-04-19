"""
IRIS — Screen Tools
====================
High-level tools that combine vision + automation for the agent.
"""

import logging
from typing import Optional, Tuple
from PIL import Image

from core.vision import (
    capture_screenshot,
    analyze_screen,
    read_text_on_screen,
    find_element,
    image_to_base64,
    save_screenshot,
)

logger = logging.getLogger(__name__)


def screenshot_and_describe(context: str = "") -> Tuple[str, Image.Image]:
    """
    Capture screen + get Gemini description.
    Returns (description, image).
    """
    img = capture_screenshot()
    desc = analyze_screen(img, context=context)
    return desc, img


def ocr_screen() -> str:
    """Extract all text from the current screen."""
    return read_text_on_screen()


def locate_element(description: str) -> str:
    """
    Find a UI element described in natural language.
    Returns positional description string.
    """
    return find_element(description)


def save_debug_screenshot(name: str = "debug.jpg") -> str:
    """Save a named debug screenshot and return the path."""
    img = capture_screenshot()
    path = save_screenshot(img, filename=name)
    logger.info("Debug screenshot saved: %s", path)
    return path
