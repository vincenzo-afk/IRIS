"""
IRIS — Cursor Overlay Widget (Tkinter)
=========================================
A floating, always-on-top, transparent window that follows the cursor.
Used as the base for TEACH mode annotations and status display.
"""

import threading
import logging
import queue
from typing import Optional

import tkinter as tk
from pynput.mouse import Listener as MouseListener

from config import (
    OVERLAY_WIDTH,
    OVERLAY_HEIGHT,
    OVERLAY_OFFSET_X,
    OVERLAY_OFFSET_Y,
    OVERLAY_BG,
    OVERLAY_FG,
    OVERLAY_FONT,
    OVERLAY_ALPHA,
)

logger = logging.getLogger(__name__)


class CursorWidget:
    """
    Floating tkinter window that:
      - Tracks the real cursor position via pynput
      - Shows a message bubble near the cursor
      - Hides itself when no message is queued
    """

    def __init__(self):
        self._root: Optional[tk.Tk] = None
        self._label: Optional[tk.Label] = None
        self._running = False
        self._msg_queue: queue.Queue = queue.Queue()
        self._cursor_x = 0
        self._cursor_y = 0
        self._mouse_listener: Optional[MouseListener] = None
        self._thread: Optional[threading.Thread] = None
        self._auto_hide_job = None

    # ── Public API ──────────────────────────────────────────────

    def start(self):
        """Launch the widget in a separate thread (Tk must live in its own thread)."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_tk, daemon=True)
        self._thread.start()

        # Start cursor tracking via pynput
        self._mouse_listener = MouseListener(on_move=self._on_mouse_move)
        self._mouse_listener.start()
        logger.info("CursorWidget started")

    def stop(self):
        self._running = False
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._root:
            self._root.after(0, self._root.destroy)
        logger.info("CursorWidget stopped")

    def show_message(self, text: str, duration_ms: int = 4000):
        """
        Display a message bubble near the cursor.
        Thread-safe: can be called from any thread.
        """
        self._msg_queue.put((text, duration_ms))

    def hide(self):
        """Hide the overlay window without stopping it."""
        if self._root:
            self._root.after(0, self._root.withdraw)

    # ── Tkinter thread ──────────────────────────────────────────

    def _run_tk(self):
        self._root = tk.Tk()
        root = self._root

        root.overrideredirect(True)           # No window decorations
        root.attributes("-topmost", True)     # Always on top
        root.attributes("-alpha", OVERLAY_ALPHA)
        root.configure(bg=OVERLAY_BG)
        root.withdraw()                       # Start hidden

        # Try platform-specific transparency
        try:
            root.wm_attributes("-transparentcolor", OVERLAY_BG)
        except Exception:
            pass  # Not supported on all platforms

        self._label = tk.Label(
            root,
            text="",
            bg=OVERLAY_BG,
            fg=OVERLAY_FG,
            font=OVERLAY_FONT,
            wraplength=OVERLAY_WIDTH - 20,
            justify="left",
            padx=10,
            pady=8,
        )
        self._label.pack(fill="both", expand=True)

        # Poll for messages every 100ms
        root.after(100, self._poll_messages)
        root.mainloop()

    def _poll_messages(self):
        try:
            while not self._msg_queue.empty():
                text, duration = self._msg_queue.get_nowait()
                self._display(text, duration)
        except Exception:
            pass
        if self._running and self._root:
            self._root.after(100, self._poll_messages)

    def _display(self, text: str, duration_ms: int):
        if not self._root or not self._label:
            return

        self._label.config(text=text)

        # Position near cursor with offset
        x = self._cursor_x + OVERLAY_OFFSET_X
        y = self._cursor_y + OVERLAY_OFFSET_Y

        # Clamp to screen bounds
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        if x + OVERLAY_WIDTH > screen_w:
            x = self._cursor_x - OVERLAY_WIDTH - 10
        if y + OVERLAY_HEIGHT > screen_h:
            y = self._cursor_y - OVERLAY_HEIGHT - 10

        self._root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+{x}+{y}")
        self._root.deiconify()

        # Auto-hide after duration
        if self._auto_hide_job:
            self._root.after_cancel(self._auto_hide_job)
        self._auto_hide_job = self._root.after(duration_ms, self._root.withdraw)

    def _on_mouse_move(self, x, y):
        self._cursor_x = x
        self._cursor_y = y
        # Move visible window if shown
        if self._root:
            self._root.after(0, self._follow_cursor)

    def _follow_cursor(self):
        if not self._root:
            return
        if self._root.state() == "withdrawn":
            return  # don't move if hidden

        x = self._cursor_x + OVERLAY_OFFSET_X
        y = self._cursor_y + OVERLAY_OFFSET_Y
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        if x + OVERLAY_WIDTH > screen_w:
            x = self._cursor_x - OVERLAY_WIDTH - 10
        if y + OVERLAY_HEIGHT > screen_h:
            y = self._cursor_y - OVERLAY_HEIGHT - 10

        self._root.geometry(f"+{x}+{y}")
