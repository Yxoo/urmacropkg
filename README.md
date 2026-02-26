# urmacropkg

Windows macro input API — keyboard, mouse, window & pixel operations.

Uses `SendInput` / `win32` for **real input events** compatible with games (DirectInput, raw input, anti-cheat).

## Install

```bash
pip install urmacropkg
```

With OCR support (Windows native):
```bash
pip install urmacropkg[ocr]
```

## Usage

```python
from urmacro import *

# Keyboard
press('a')
press('ctrl', hold=True)
press('c')
release('ctrl')
write("hello world")

# Mouse
left_click()
smooth_move(960, 540, duration=0.5)
send_input_delta(100, 0)   # raw relative move (game cameras)

# Window
focus_window("Notepad")
focus_window("MyGame", full_scale=True)

# Pixel
color = get_pixel_color(100, 200)
if check_pixel_color(500, 300, r=255, g=0, b=0, tolerance=15):
    print("red pixel found")

pos = find_color(0, 0, 1920, 1080, r=0, g=255, b=0)

# Interruptible sleep (for macro loops)
def my_macro(get_active_status):
    while get_active_status():
        press('space')
        if not sleep_interruptible(1.0, get_active_status):
            return
```

## API Reference

### Keyboard

| Function | Description |
|----------|-------------|
| `press(key)` | Press and release a key (`'a'`, `'f1'`, `'enter'`, `'space'`, `'\\'`...) |
| `press(key, hold=True)` | Hold a key down |
| `release(key)` | Release a held key |
| `release_all()` | Release all held keys and mouse buttons |
| `write(text, delay=0.05)` | Type a string (Unicode, supports accents) |

### Mouse

| Function | Description |
|----------|-------------|
| `left_click()` / `right_click()` | Click |
| `left_click(hold=True)` | Hold mouse button |
| `release_left_click()` / `release_right_click()` | Release held button |
| `move(x, y)` | Instant cursor warp (cosmetic) |
| `send_input_move(x, y)` | Absolute move via SendInput (UI clicks) |
| `send_input_delta(dx, dy)` | Relative move via SendInput (game cameras) |
| `smooth_move(x, y, duration=0.4)` | Smooth Bezier move via SendInput |
| `smooth_move(dx, dy, relative=True)` | Smooth relative move |

### Window

| Function | Description |
|----------|-------------|
| `find_window(title, partial=True)` | Returns `(hwnd, title)` or `(None, None)` |
| `focus_window(title, partial=True, full_scale=False)` | Bring window to foreground |

### Pixel & Screen

| Function | Description |
|----------|-------------|
| `get_pixel_color(x, y)` | Returns `(R, G, B)` or `None` |
| `check_pixel_color(x, y, r, g, b, tolerance=10)` | Color match with tolerance |
| `find_color(x, y, w, h, r, g, b, tolerance=10)` | Find first pixel of color in region |
| `find_color_bounds(x, y, w, h, ref_x, ref_y)` | Bounding box of a color zone |
| `screenshot_region(x, y, w, h)` | PIL Image of a screen region |
| `read_text(x, y, w, h, lang='fr')` | OCR via Windows native API (requires `[ocr]`) |
| `get_cursor_pos()` | Returns `(x, y)` |
| `get_screen_size()` | Returns `(width, height)` |
| `get_zone_center(x1, y1, x2, y2)` | Returns `(cx, cy)` |

### Timing

| Function | Description |
|----------|-------------|
| `sleep_interruptible(seconds, get_active_status)` | Sleep that returns `False` if macro is stopped |

All pixel functions accept an optional `window_title` argument — coordinates are then relative to the window's client area.

## Requirements

- Windows 10/11
- Python 3.10+
- `pywin32`
- `Pillow`
- `winocr` (optional, for OCR)

## License

MIT
