"""
IRIS — System Tools
====================
Open apps, send notifications, manage the system.
Cross-platform (macOS / Windows / Linux).
"""

import logging
import os
import platform
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)
_SYSTEM = platform.system()


def open_app(app_name: str) -> str:
    """
    Open an application by name.
    Handles macOS (open -a), Windows (start), and Linux (subprocess).
    """
    logger.info("Opening app: %s", app_name)
    try:
        if _SYSTEM == "Darwin":
            # Try 'open -a AppName' first
            result = subprocess.run(
                ["open", "-a", app_name],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                # Fall back to Spotlight-style open
                subprocess.Popen(["open", app_name])
        elif _SYSTEM == "Windows":
            os.startfile(app_name)
        else:
            subprocess.Popen([app_name])

        return f"Opened '{app_name}' successfully"
    except Exception as exc:
        logger.error("open_app failed: %s", exc)
        return f"Failed to open '{app_name}': {exc}"


def get_clipboard() -> str:
    from core.automation import get_clipboard as _gc
    return _gc()


def set_clipboard(text: str):
    from core.automation import set_clipboard as _sc
    _sc(text)


def notify(title: str, message: str):
    """Send a desktop notification."""
    try:
        if _SYSTEM == "Darwin":
            script = (
                f'display notification "{message}" with title "{title}"'
            )
            subprocess.run(["osascript", "-e", script])
        elif _SYSTEM == "Windows":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0)
        else:
            subprocess.run(["notify-send", title, message])
        logger.info("Notification: [%s] %s", title, message)
    except Exception as exc:
        logger.error("notify failed: %s", exc)


def run_shell(command: str, timeout: int = 30) -> str:
    """
    Run a shell command and return combined stdout+stderr.
    CAUTION: Only call this when the user explicitly requests shell execution.
    """
    logger.warning("Shell command: %s", command)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as exc:
        return f"Shell error: {exc}"


def get_active_window_title() -> str:
    """Return the title of the currently focused window."""
    try:
        if _SYSTEM == "Darwin":
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=3
            )
            return result.stdout.strip()
        elif _SYSTEM == "Windows":
            import ctypes
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.GetWindowTextW(
                ctypes.windll.user32.GetForegroundWindow(), buf, 512
            )
            return buf.value
        else:
            result = subprocess.run(
                ["xdotool", "getactivewindow", "getwindowname"],
                capture_output=True, text=True, timeout=3
            )
            return result.stdout.strip()
    except Exception as exc:
        return f"Unknown ({exc})"
