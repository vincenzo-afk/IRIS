"""
IRIS — Input Tools
===================
Named wrappers around core.automation for use by the agent.
"""

from core.automation import (
    click,
    double_click,
    right_click,
    drag,
    scroll,
    type_text,
    type_text_raw,
    press_key,
    hotkey,
    paste_text,
    copy_selection,
    get_clipboard,
    set_clipboard,
    move_mouse,
    get_mouse_position,
)

__all__ = [
    "click",
    "double_click",
    "right_click",
    "drag",
    "scroll",
    "type_text",
    "type_text_raw",
    "press_key",
    "hotkey",
    "paste_text",
    "copy_selection",
    "get_clipboard",
    "set_clipboard",
    "move_mouse",
    "get_mouse_position",
]
