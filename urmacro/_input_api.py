"""
Input API — urmacro
Abstraction win32 + SendInput pour keyboard, souris et fenêtres.

Usage:
    from urmacro import press, smooth_move, left_click, check_pixel_color
"""

import time
import ctypes
import ctypes.wintypes
import win32gui
import win32con
import win32api

# DPI awareness : force Windows à retourner la résolution physique réelle
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()


# ============================================================================
# FENÊTRES
# ============================================================================

def find_window(title: str, partial: bool = True):
    """
    Trouve une fenêtre par son titre.

    Args:
        title:   Titre à rechercher.
        partial: Si True, cherche les fenêtres qui CONTIENNENT le titre.

    Returns:
        (hwnd, full_title) ou (None, None) si non trouvé.
    """
    if not partial:
        hwnd = win32gui.FindWindow(None, title)
        if hwnd == 0:
            return None, None
        return hwnd, win32gui.GetWindowText(hwnd)

    found_windows = []

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if title.lower() in window_title.lower():
                found_windows.append((hwnd, window_title))
        return True

    win32gui.EnumWindows(callback, None)

    if not found_windows:
        return None, None
    return found_windows[0][0], found_windows[0][1]


def focus_window(title: str, partial: bool = True, full_scale: bool = False) -> bool:
    """
    Met le focus sur une fenêtre.

    Args:
        title:      Titre de la fenêtre.
        partial:    Si True, cherche les fenêtres qui contiennent le titre.
        full_scale: Si True, maximise la fenêtre (équivalent au bouton □).

    Returns:
        True si succès, False sinon.
    """
    hwnd, found_title = find_window(title, partial)

    if not hwnd:
        return False

    try:
        import win32process

        fg_hwnd = win32gui.GetForegroundWindow()
        fg_tid = win32process.GetWindowThreadProcessId(fg_hwnd)[0]
        my_tid = ctypes.windll.kernel32.GetCurrentThreadId()

        if fg_tid and fg_tid != my_tid:
            ctypes.windll.user32.AttachThreadInput(my_tid, fg_tid, True)

        if full_scale:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        elif win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        win32gui.BringWindowToTop(hwnd)
        win32gui.SetForegroundWindow(hwnd)

        if fg_tid and fg_tid != my_tid:
            ctypes.windll.user32.AttachThreadInput(my_tid, fg_tid, False)

        time.sleep(0.1)
        return True
    except Exception as e:
        print(f"   focus_window error: {e}")
        return False


# ============================================================================
# SOURIS — CLICS
# ============================================================================

_left_click_held = False
_right_click_held = False


def left_click(hold: bool = False) -> None:
    """Clic gauche. hold=True pour maintenir le bouton enfoncé."""
    global _left_click_held
    if hold:
        if not _left_click_held:
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
            _left_click_held = True
    else:
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.01)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP


def release_left_click() -> None:
    """Relâche le clic gauche s'il est maintenu."""
    global _left_click_held
    if _left_click_held:
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        _left_click_held = False


def right_click(hold: bool = False) -> None:
    """Clic droit. hold=True pour maintenir le bouton enfoncé."""
    global _right_click_held
    if hold:
        if not _right_click_held:
            ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0)  # RIGHTDOWN
            _right_click_held = True
    else:
        ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0)
        time.sleep(0.01)
        ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0)  # RIGHTUP


def release_right_click() -> None:
    """Relâche le clic droit s'il est maintenu."""
    global _right_click_held
    if _right_click_held:
        ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0)
        _right_click_held = False


def move(x: int, y: int) -> None:
    """Déplace la souris instantanément via SetCursorPos (cosmétique)."""
    ctypes.windll.user32.SetCursorPos(x, y)


# ============================================================================
# SOURIS — SENDINPUT (vrais événements d'input)
# ============================================================================

def _mouse_send_input(dx: int, dy: int, flags: int) -> None:
    """Interne : envoie un événement souris via SendInput."""
    PUL = ctypes.POINTER(ctypes.c_ulong)

    class KeyBdInput(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                    ("dwExtraInfo", PUL)]

    class HardwareInput(ctypes.Structure):
        _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short),
                    ("wParamH", ctypes.c_ushort)]

    class MouseInput(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

    class Input_I(ctypes.Union):
        _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(dx, dy, 0, flags, 0, ctypes.pointer(extra))
    x_input = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x_input), ctypes.sizeof(x_input))


def send_input_move(x: int, y: int) -> None:
    """
    Déplace la souris via SendInput absolu (MOUSEEVENTF_ABSOLUTE).
    Génère un vrai événement vu par DirectInput / raw input.
    Idéal pour les clics UI. Pour les caméras de jeu → send_input_delta.
    """
    sw = ctypes.windll.user32.GetSystemMetrics(0)
    sh = ctypes.windll.user32.GetSystemMetrics(1)
    norm_x = int(x * 65535 / (sw - 1))
    norm_y = int(y * 65535 / (sh - 1))
    _mouse_send_input(norm_x, norm_y, 0x0001 | 0x8000)  # MOVE | ABSOLUTE


def send_input_delta(dx: int, dy: int) -> None:
    """
    Envoie un mouvement relatif via SendInput (sans ABSOLUTE).
    Vu comme un vrai delta par raw input / DirectInput / caméras de jeu.
    """
    _mouse_send_input(dx, dy, 0x0001)  # MOVE relatif


def smooth_move(x: int, y: int, duration: float = 0.4, relative: bool = False) -> None:
    """
    Déplace la souris de façon fluide (courbe de Bézier + easing sinusoïdal).
    Utilise SendInput — vrais événements d'input vus par les jeux.

    Args:
        x, y:     Position cible absolue, ou offset si relative=True.
        duration: Durée du mouvement en secondes (défaut : 0.4).
        relative: Si True, x/y sont ajoutés à la position courante.
    """
    import math
    import random

    point = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    start_x, start_y = point.x, point.y

    target_x = start_x + x if relative else x
    target_y = start_y + y if relative else y

    dx = target_x - start_x
    dy = target_y - start_y
    dist = math.sqrt(dx * dx + dy * dy)

    if dist < 2:
        if relative:
            send_input_delta(int(dx), int(dy))
        else:
            send_input_move(target_x, target_y)
        return

    deviation = 0.0 if relative else random.uniform(-0.15, 0.15) * dist
    if relative:
        mid_bx = x / 2
        mid_by = y / 2
    else:
        mid_bx = (start_x + target_x) / 2 + (-dy / dist) * deviation
        mid_by = (start_y + target_y) / 2 + (dx / dist) * deviation

    steps = max(15, int(duration * 120))

    if relative:
        prev_bx, prev_by = 0.0, 0.0
        acc_x, acc_y = 0.0, 0.0
        for i in range(1, steps + 1):
            t = i / steps
            eased = (1 - math.cos(t * math.pi)) / 2
            inv = 1 - eased
            bx = 2 * inv * eased * mid_bx + eased * eased * x
            by = 2 * inv * eased * mid_by + eased * eased * y
            acc_x += bx - prev_bx
            acc_y += by - prev_by
            prev_bx, prev_by = bx, by
            send_dx = int(acc_x)
            send_dy = int(acc_y)
            if send_dx != 0 or send_dy != 0:
                send_input_delta(send_dx, send_dy)
                acc_x -= send_dx
                acc_y -= send_dy
            time.sleep(duration / steps)
        send_dx = round(acc_x)
        send_dy = round(acc_y)
        if send_dx != 0 or send_dy != 0:
            send_input_delta(send_dx, send_dy)
    else:
        for i in range(1, steps + 1):
            t = i / steps
            eased = (1 - math.cos(t * math.pi)) / 2
            inv = 1 - eased
            bx = inv * inv * start_x + 2 * inv * eased * mid_bx + eased * eased * target_x
            by = inv * inv * start_y + 2 * inv * eased * mid_by + eased * eased * target_y
            curr_x = int(bx) + (random.randint(-1, 1) if i < steps else 0)
            curr_y = int(by) + (random.randint(-1, 1) if i < steps else 0)
            send_input_move(curr_x, curr_y)
            time.sleep(duration / steps)
        send_input_move(target_x, target_y)


# ============================================================================
# CLAVIER
# ============================================================================

KEY_MAP = {
    **{chr(i): ord(chr(i).upper()) for i in range(ord('a'), ord('z') + 1)},
    **{chr(i): ord(chr(i)) for i in range(ord('A'), ord('Z') + 1)},
    **{str(i): ord(str(i)) for i in range(10)},
    'esc': win32con.VK_ESCAPE,
    'escape': win32con.VK_ESCAPE,
    'enter': win32con.VK_RETURN,
    'return': win32con.VK_RETURN,
    'space': win32con.VK_SPACE,
    'tab': win32con.VK_TAB,
    'shift': win32con.VK_SHIFT,
    'ctrl': win32con.VK_CONTROL,
    'control': win32con.VK_CONTROL,
    'alt': win32con.VK_MENU,
    'backspace': win32con.VK_BACK,
    'delete': win32con.VK_DELETE,
    'up': win32con.VK_UP,
    'down': win32con.VK_DOWN,
    'left': win32con.VK_LEFT,
    'right': win32con.VK_RIGHT,
    **{f'f{i}': win32con.VK_F1 + i - 1 for i in range(1, 13)},
    '/': ord('/'),
    '\\': 0xDC,   # VK_OEM_5
    '.': ord('.'),
    ',': ord(','),
    ';': ord(';'),
    ':': ord(':'),
    '!': ord('!'),
    '?': ord('?'),
    '-': ord('-'),
    '_': ord('_'),
    '+': ord('+'),
    '=': ord('='),
    '*': ord('*'),
    '&': ord('&'),
    '%': ord('%'),
    '$': ord('$'),
    '#': ord('#'),
    '@': ord('@'),
    '(': ord('('),
    ')': ord(')'),
    '[': ord('['),
    ']': ord(']'),
    '{': ord('{'),
    '}': ord('}'),
    '<': ord('<'),
    '>': ord('>'),
    '|': ord('|'),
    '"': ord('"'),
    "'": ord("'"),
    '`': ord('`'),
    '~': ord('~'),
    '^': ord('^'),
}

_held_keys: set = set()


def _get_key_code(key) -> int:
    if isinstance(key, int):
        return key
    key_lower = key.lower()
    if key_lower in KEY_MAP:
        return KEY_MAP[key_lower]
    if len(key) == 1:
        return ord(key.upper())
    raise ValueError(f"Touche inconnue: {key}")


def _get_scan_code(vk_code: int) -> int:
    return ctypes.windll.user32.MapVirtualKeyW(vk_code, 0)


def _is_extended_key(vk_code: int) -> bool:
    return vk_code in (
        win32con.VK_UP, win32con.VK_DOWN, win32con.VK_LEFT, win32con.VK_RIGHT,
        win32con.VK_INSERT, win32con.VK_DELETE,
        win32con.VK_HOME, win32con.VK_END,
        win32con.VK_PRIOR, win32con.VK_NEXT,
    )


def _send_key(vk_code: int, scan_code: int, flags: int) -> None:
    """Interne : envoie un événement clavier via SendInput."""
    PUL = ctypes.POINTER(ctypes.c_ulong)

    class KeyBdInput(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                    ("dwExtraInfo", PUL)]

    class HardwareInput(ctypes.Structure):
        _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short),
                    ("wParamH", ctypes.c_ushort)]

    class MouseInput(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

    class Input_I(ctypes.Union):
        _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(vk_code, scan_code, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def press(key, hold: bool = False) -> None:
    """
    Appuie sur une touche.

    Args:
        key:  La touche ('a', 'enter', 'f1', 'up', '\\', ...).
        hold: Si True, maintient la touche enfoncée sans la relâcher.
    """
    global _held_keys
    key_code = _get_key_code(key)
    scan_code = _get_scan_code(key_code)
    ext_flag = 0x0001 if _is_extended_key(key_code) else 0

    if hold:
        if key_code not in _held_keys:
            _send_key(key_code, scan_code, ext_flag)
            _held_keys.add(key_code)
    else:
        _send_key(key_code, scan_code, ext_flag)
        time.sleep(0.01)
        _send_key(key_code, scan_code, ext_flag | 0x0002)  # KEYUP


def release(key) -> None:
    """Relâche une touche maintenue avec press(hold=True)."""
    global _held_keys
    key_code = _get_key_code(key)
    scan_code = _get_scan_code(key_code)
    ext_flag = 0x0001 if _is_extended_key(key_code) else 0

    if key_code in _held_keys:
        _send_key(key_code, scan_code, ext_flag | 0x0002)
        _held_keys.remove(key_code)


def release_all() -> None:
    """Relâche toutes les touches et clics maintenus."""
    for key_code in list(_held_keys):
        release(key_code)
    release_left_click()
    release_right_click()


def write(text: str, delay: float = 0.05) -> None:
    """
    Écrit une chaîne de caractères en Unicode (accents, symboles supportés).

    Args:
        text:  Texte à écrire.
        delay: Délai entre chaque caractère en secondes (défaut : 0.05).
    """
    KEYEVENTF_UNICODE = 0x0004
    KEYEVENTF_KEYUP   = 0x0002
    PUL = ctypes.POINTER(ctypes.c_ulong)

    class KeyBdInput(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                    ("dwExtraInfo", PUL)]

    class HardwareInput(ctypes.Structure):
        _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short),
                    ("wParamH", ctypes.c_ushort)]

    class MouseInput(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                    ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

    class Input_I(ctypes.Union):
        _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

    for char in text:
        unicode_value = ord(char)
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput(0, unicode_value, KEYEVENTF_UNICODE, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        time.sleep(0.005)
        ii_.ki = KeyBdInput(0, unicode_value, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
        x = Input(ctypes.c_ulong(1), ii_)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        time.sleep(delay)


# ============================================================================
# PIXEL & ÉCRAN
# ============================================================================

def _to_screen_coords(x: int, y: int, window_title=None):
    if window_title is None:
        return x, y
    hwnd, _ = find_window(window_title)
    if hwnd is None:
        raise ValueError(f"Fenêtre '{window_title}' non trouvée")
    return win32gui.ClientToScreen(hwnd, (x, y))


def get_pixel_color(x: int, y: int, window_title=None):
    """
    Récupère la couleur d'un pixel.

    Args:
        x, y:         Position du pixel.
        window_title: Si fourni, x/y sont relatifs à la zone client de cette fenêtre.

    Returns:
        Tuple (R, G, B) ou None si erreur.
    """
    sx, sy = _to_screen_coords(x, y, window_title)
    hdc = ctypes.windll.user32.GetDC(0)
    color = ctypes.windll.gdi32.GetPixel(hdc, sx, sy)
    ctypes.windll.user32.ReleaseDC(0, hdc)
    if color < 0:
        return None
    return (color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF)


def check_pixel_color(x: int, y: int, r: int, g: int, b: int,
                      tolerance: int = 10, window_title=None) -> bool:
    """
    Vérifie si un pixel correspond à une couleur (avec tolérance par composante).

    Args:
        x, y:         Position du pixel.
        r, g, b:      Couleur attendue (0-255).
        tolerance:    Écart max accepté par composante (défaut : 10).
        window_title: Si fourni, x/y sont relatifs à la zone client.

    Returns:
        True si la couleur correspond, False sinon.
    """
    pixel = get_pixel_color(x, y, window_title)
    if pixel is None:
        return False
    pr, pg, pb = pixel
    return abs(pr - r) <= tolerance and abs(pg - g) <= tolerance and abs(pb - b) <= tolerance


def get_cursor_pos():
    """Retourne la position actuelle du curseur (x, y)."""
    point = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def get_screen_size():
    """Retourne la résolution de l'écran principal (width, height)."""
    return (ctypes.windll.user32.GetSystemMetrics(0),
            ctypes.windll.user32.GetSystemMetrics(1))


def screenshot_region(x: int, y: int, width: int, height: int, window_title=None):
    """
    Capture une zone de l'écran. Retourne une Image PIL.

    Args:
        x, y:          Coin supérieur gauche.
        width, height: Taille de la zone.
        window_title:  Si fourni, x/y sont relatifs à la zone client.
    """
    from PIL import ImageGrab
    sx, sy = _to_screen_coords(x, y, window_title)
    return ImageGrab.grab(bbox=(sx, sy, sx + width, sy + height))


def read_text(x: int, y: int, width: int, height: int,
              window_title=None, lang: str = 'fr') -> str:
    """
    Lit le texte dans une zone via OCR Windows natif (winocr).

    Args:
        x, y, width, height: Zone à lire.
        window_title:        Si fourni, x/y relatifs à la zone client.
        lang:                Code langue OCR (défaut : 'fr').

    Nécessite : pip install urmacro[ocr]
    """
    try:
        import winocr
    except ImportError:
        raise ImportError("winocr est requis : pip install urmacro[ocr]")

    import asyncio
    img = screenshot_region(x, y, width, height, window_title)

    async def _ocr():
        result = await winocr.recognize_pil(img, lang=lang)
        return result.text

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(lambda: asyncio.run(_ocr())).result()
    return asyncio.run(_ocr())


def find_color(x: int, y: int, width: int, height: int,
               r: int, g: int, b: int, tolerance: int = 10,
               direction: str = 'start', x_step: int = 1, y_step: int = 1,
               window_title=None):
    """
    Cherche un pixel d'une couleur dans une zone rectangulaire.

    Args:
        x, y, width, height: Zone de recherche.
        r, g, b:             Couleur recherchée.
        tolerance:           Écart max par composante (défaut : 10).
        direction:           'start' (haut-gauche) ou 'end' (bas-droite).
        x_step, y_step:      Pas de scan (défaut : 1).
        window_title:        Si fourni, coordonnées relatives à la fenêtre.

    Returns:
        (px, py) du premier pixel trouvé, ou False.
    """
    from PIL import ImageGrab
    sx, sy = _to_screen_coords(x, y, window_title)
    img = ImageGrab.grab(bbox=(sx, sy, sx + width, sy + height))
    pixels = img.load()

    y_range = range(height - 1, -1, -y_step) if direction == 'end' else range(0, height, y_step)
    x_range = range(width - 1, -1, -x_step) if direction == 'end' else range(0, width, x_step)

    for py in y_range:
        for px in x_range:
            pr, pg, pb = pixels[px, py][:3]
            if abs(pr - r) <= tolerance and abs(pg - g) <= tolerance and abs(pb - b) <= tolerance:
                return (x + px, y + py)
    return False


def find_color_bounds(x: int, y: int, width: int, height: int,
                      ref_x: int, ref_y: int, tolerance: int = 10,
                      window_title=None):
    """
    Trouve le rectangle englobant d'une zone de couleur.
    Prend la couleur du pixel (ref_x, ref_y) et cherche tous les pixels
    de cette couleur dans la zone donnée.

    Returns:
        (x1, y1, x2, y2) ou False si aucun pixel trouvé.
    """
    ref_color = get_pixel_color(ref_x, ref_y, window_title)
    if ref_color is None:
        return False

    from PIL import ImageGrab
    sx, sy = _to_screen_coords(x, y, window_title)
    img = ImageGrab.grab(bbox=(sx, sy, sx + width, sy + height))
    pixels = img.load()
    ref_r, ref_g, ref_b = ref_color

    min_x, min_y = width, height
    max_x, max_y = -1, -1

    for py in range(height):
        for px in range(width):
            pr, pg, pb = pixels[px, py][:3]
            if (abs(pr - ref_r) <= tolerance and
                    abs(pg - ref_g) <= tolerance and
                    abs(pb - ref_b) <= tolerance):
                if px < min_x: min_x = px
                if py < min_y: min_y = py
                if px > max_x: max_x = px
                if py > max_y: max_y = py

    if max_x == -1:
        return False
    return (x + min_x, y + min_y, x + max_x, y + max_y)


def get_zone_center(x1: int, y1: int, x2: int, y2: int):
    """Retourne le centre d'une zone rectangulaire (cx, cy)."""
    return ((x1 + x2) // 2, (y1 + y2) // 2)
