"""
urmacro — Windows macro input API
pip install urmacropkg

Usage:
    from urmacro import press, smooth_move, left_click, check_pixel_color
    from urmacro import *
"""

from ._input_api import (
    # Fenêtres
    find_window,
    focus_window,
    # Souris — clics
    left_click,
    release_left_click,
    right_click,
    release_right_click,
    move,
    # Souris — SendInput
    send_input_move,
    send_input_delta,
    smooth_move,
    # Clavier
    press,
    release,
    release_all,
    write,
    # Pixel & écran
    get_pixel_color,
    check_pixel_color,
    get_cursor_pos,
    get_screen_size,
    screenshot_region,
    read_text,
    find_color,
    find_color_bounds,
    get_zone_center,
)

from ._utils import sleep_interruptible

__all__ = [
    "find_window",
    "focus_window",
    "left_click",
    "release_left_click",
    "right_click",
    "release_right_click",
    "move",
    "send_input_move",
    "send_input_delta",
    "smooth_move",
    "press",
    "release",
    "release_all",
    "write",
    "get_pixel_color",
    "check_pixel_color",
    "get_cursor_pos",
    "get_screen_size",
    "screenshot_region",
    "read_text",
    "find_color",
    "find_color_bounds",
    "get_zone_center",
    "sleep_interruptible",
]
