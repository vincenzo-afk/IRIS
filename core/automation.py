"""
IRIS — Computer Automation Module
===================================
Mouse movement, clicks, scrolling, keyboard typing, hotkeys —
everything pyautogui and pynput can do.
All actions are logged for the agent's verification loop.
"""

import logging
import time
import platform
from typing import Optional, Tuple

import pyautogui
from pynput import mouse as pynput_mouse, keyboard as pynput_keyboard
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key, HotKey

from config import AGENT_STEP_DELAY

logger = logging.getLogger(__name__)

# ── Safety settings ────────────────────────────────────────────
pyautogui.FAILSAFE = True          # Move mouse to corner to abort
pyautogui.PAUSE = AGENT_STEP_DELAY  # Delay between every pyautogui call

_mouse = MouseController()
_kb = KeyboardController()


# ──────────────────────────────────────────────────────────────
# MOUSE ACTIONS
# ──────────────────────────────────────────────────────────────

def get_mouse_position() -> Tuple[int, int]:
    pos = pyautogui.position()
    return (pos.x, pos.y)


def move_mouse(x: int, y: int, duration: float = 0.3):
    """Smoothly move the mouse to absolute screen coordinates."""
    logger.info("Mouse → (%d, %d)", x, y)
    pyautogui.moveTo(x, y, duration=duration)


def click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left"):
    """Click at current or specified position."""
    if x is not None and y is not None:
        pyautogui.click(x, y, button=button)
        logger.info("Click %s @ (%d, %d)", button, x, y)
    else:
        pyautogui.click(button=button)
        logger.info("Click %s @ current position", button)


def double_click(x: int, y: int):
    pyautogui.doubleClick(x, y)
    logger.info("Double-click @ (%d, %d)", x, y)


def right_click(x: int, y: int):
    pyautogui.rightClick(x, y)
    logger.info("Right-click @ (%d, %d)", x, y)


def drag(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5):
    pyautogui.dragTo(x2, y2, duration=duration, mouseDownUp=True)
    logger.info("Drag (%d,%d) → (%d,%d)", x1, y1, x2, y2)


def scroll(x: int, y: int, clicks: int = 3, direction: str = "down"):
    """Scroll at position. direction: 'up' | 'down' | 'left' | 'right'."""
    pyautogui.moveTo(x, y)
    if direction in ("up", "down"):
        amount = clicks if direction == "up" else -clicks
        pyautogui.scroll(amount)
    elif direction in ("left", "right"):
        amount = clicks if direction == "right" else -clicks
        pyautogui.hscroll(amount)
    logger.info("Scroll %s x%d @ (%d, %d)", direction, clicks, x, y)


# ──────────────────────────────────────────────────────────────
# KEYBOARD ACTIONS
# ──────────────────────────────────────────────────────────────

def type_text(text: str, interval: float = 0.02):
    """Type text character by character (works in any focused field)."""
    pyautogui.typewrite(text, interval=interval)
    logger.info("Typed: %s…", text[:40])


def type_text_raw(text: str):
    """
    Type text using pynput (handles unicode, special chars, UTF-8).
    Slower but more compatible.
    """
    _kb.type(text)
    logger.info("Typed (raw): %s…", text[:40])


def press_key(key: str):
    """Press a single key by name (e.g. 'enter', 'tab', 'escape', 'f5')."""
    pyautogui.press(key)
    logger.info("Key: %s", key)


def hotkey(*keys: str):
    """Press a key combination (e.g. hotkey('ctrl', 'c'))."""
    pyautogui.hotkey(*keys)
    logger.info("Hotkey: %s", "+".join(keys))


def hold_and_press(hold: str, press: str):
    """Hold one key while pressing another."""
    with _kb.pressed(getattr(Key, hold, hold)):
        press_key(press)


# ──────────────────────────────────────────────────────────────
# CLIPBOARD
# ──────────────────────────────────────────────────────────────

def copy_selection() -> str:
    """Select all + copy and return clipboard contents."""
    hotkey("ctrl", "a")
    time.sleep(0.1)
    hotkey("ctrl", "c")
    time.sleep(0.2)
    return get_clipboard()


def get_clipboard() -> str:
    import subprocess
    if platform.system() == "Darwin":
        result = subprocess.run(["pbpaste"], capture_output=True, text=True)
        return result.stdout
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception:
        return ""


def set_clipboard(text: str):
    import subprocess
    if platform.system() == "Darwin":
        subprocess.run(["pbcopy"], input=text.encode())
        return
    try:
        import pyperclip
        pyperclip.copy(text)
    except Exception:
        pass


def paste_text(text: str):
    """Put text into clipboard then paste it — faster than typewrite for long text."""
    set_clipboard(text)
    time.sleep(0.1)
    hotkey("ctrl", "v")
    logger.info("Pasted %d chars", len(text))


# ──────────────────────────────────────────────────────────────
# CURSOR TRACKING (pynput listener)
# ──────────────────────────────────────────────────────────────

class CursorTracker:
    """Lightweight listener that tracks the real mouse position."""

    def __init__(self):
        self.x: int = 0
        self.y: int = 0
        self._listener: Optional[pynput_mouse.Listener] = None

    def start(self):
        self._listener = pynput_mouse.Listener(on_move=self._on_move)
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    def _on_move(self, x, y):
        self.x = x
        self.y = y

    @property
    def position(self) -> Tuple[int, int]:
        return (self.x, self.y)


# ──────────────────────────────────────────────────────────────
# SCREENSHOT VERIFICATION
# ──────────────────────────────────────────────────────────────

def wait_and_verify(seconds: float = 1.0):
    """
    Pause briefly so the OS can respond to the last action,
    then capture a fresh screenshot for the agent's verify step.
    """
    time.sleep(seconds)
    from core.vision import capture_screenshot, analyze_screen
    img = capture_screenshot()
    desc = analyze_screen(img)
    logger.info("[VERIFY] Screen state: %s…", desc[:120])
    return desc, img
