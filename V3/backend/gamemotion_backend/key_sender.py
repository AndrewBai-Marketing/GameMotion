import time
import logging
import sys

log = logging.getLogger("keys")

# Detect platform
IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

# Try pynput first (cross-platform, works on Mac/Windows/Linux)
pynput_keyboard = None
pynput_mouse = None
Key = None
Button = None
PYNPUT_SPECIAL_KEYS = {}
PYNPUT_MOUSE_BUTTONS = {}

try:
    from pynput.keyboard import Controller as KeyboardController, Key as PynputKey
    from pynput.mouse import Controller as MouseController, Button as PynputButton
    pynput_keyboard = KeyboardController()
    pynput_mouse = MouseController()
    Key = PynputKey
    Button = PynputButton

    # Map normalized key names to pynput Key objects
    PYNPUT_SPECIAL_KEYS = {
        "space": Key.space,
        "enter": Key.enter,
        "escape": Key.esc,
        "tab": Key.tab,
        "ctrl": Key.ctrl,
        "alt": Key.alt,
        "shift": Key.shift,
        "left": Key.left,
        "right": Key.right,
        "up": Key.up,
        "down": Key.down,
        "pageup": Key.page_up,
        "pagedown": Key.page_down,
        "delete": Key.delete,
        "backspace": Key.backspace,
        "home": Key.home,
        "end": Key.end,
        "insert": Key.insert,
        "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
        "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
        "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    }

    # Add cmd/super key (platform-specific)
    if IS_MAC:
        PYNPUT_SPECIAL_KEYS["cmd"] = Key.cmd
    else:
        PYNPUT_SPECIAL_KEYS["cmd"] = Key.cmd_l if hasattr(Key, 'cmd_l') else Key.ctrl

    # Map mouse button names to pynput Button objects
    PYNPUT_MOUSE_BUTTONS = {
        "left": Button.left,
        "right": Button.right,
        "middle": Button.middle,
    }

    log.info("Using pynput for input (cross-platform)")
except ImportError:
    log.warning("pynput not available")

# Fallback: pydirectinput for Windows games (better DirectInput support)
pdi = None
if IS_WINDOWS and pynput_keyboard is None:
    try:
        import pydirectinput as pdi
        pdi.FAILSAFE = False
        log.info("Using pydirectinput for input (Windows DirectInput)")
    except ImportError:
        pdi = None

# Fallback: keyboard library
kb = None
if pynput_keyboard is None and pdi is None:
    try:
        import keyboard as kb
        log.info("Using keyboard library for input")
    except ImportError:
        kb = None

# Map common aliases -> normalized key names
KEY_ALIASES = {
    "spacebar": "space",
    "space": "space",
    "return": "enter",
    "enter": "enter",
    "esc": "escape",
    "escape": "escape",
    "tab": "tab",
    "ctrl": "ctrl",
    "control": "ctrl",
    "alt": "alt",
    "shift": "shift",
    "left": "left",
    "right": "right",
    "up": "up",
    "down": "down",
    "pgup": "pageup",
    "pageup": "pageup",
    "pgdn": "pagedown",
    "pagedown": "pagedown",
    "del": "delete",
    "delete": "delete",
    "bksp": "backspace",
    "backspace": "backspace",
    "cmd": "cmd",
    "command": "cmd",
    "win": "cmd",
    "super": "cmd",
}


def _norm_key(k: str) -> str:
    if not k:
        return ""
    k = k.strip().lower()
    return KEY_ALIASES.get(k, k)


def _get_pynput_key(key_name: str):
    """Convert a key name to a pynput key object or character."""
    if key_name in PYNPUT_SPECIAL_KEYS:
        return PYNPUT_SPECIAL_KEYS[key_name]
    # Single character keys
    if len(key_name) == 1:
        return key_name
    # Unknown key - try as-is
    log.warning(f"Unknown key '{key_name}', attempting to use as character")
    return key_name


class KeySender:
    """
    Cross-platform key/mouse sender supporting Windows, Mac, and Linux.

    Mapping examples:
      {"type":"keyboard","keys":["space"],"hold_ms":50}
      {"type":"keyboard","keys":["ctrl","shift","a"],"hold_ms":50}
      {"type":"mouse","buttons":["left"],"hold_ms":50}
    """

    def __init__(self):
        self._backend = self._detect_backend()
        log.info(f"KeySender initialized with backend: {self._backend}")

    def _detect_backend(self) -> str:
        if pynput_keyboard is not None:
            return "pynput"
        if pdi is not None:
            return "pydirectinput"
        if kb is not None:
            return "keyboard"
        return "none"

    def _send_keyboard_pynput(self, keys: list, hold_ms: int):
        """Send keyboard input using pynput (cross-platform)."""
        norm = [_norm_key(k) for k in keys if k]
        if not norm:
            log.warning("No keys to send.")
            return

        log.info(f"[pynput] Sending keys: {norm} | hold_ms={hold_ms}")

        modifiers = {"ctrl", "shift", "alt", "cmd"}

        # Check if this is a chord (modifiers + final key)
        if len(norm) >= 2 and all(k in modifiers for k in norm[:-1]):
            mods = norm[:-1]
            final = norm[-1]

            # Press modifiers
            for m in mods:
                pynput_keyboard.press(_get_pynput_key(m))
            time.sleep(0.01)

            # Press and release final key
            final_key = _get_pynput_key(final)
            pynput_keyboard.press(final_key)
            time.sleep(hold_ms / 1000.0)
            pynput_keyboard.release(final_key)

            # Release modifiers in reverse order
            for m in reversed(mods):
                pynput_keyboard.release(_get_pynput_key(m))
            return

        # Sequential key presses
        for k in norm:
            key = _get_pynput_key(k)
            pynput_keyboard.press(key)
            time.sleep(hold_ms / 1000.0)
            pynput_keyboard.release(key)

    def _send_keyboard_pdi(self, keys: list, hold_ms: int):
        """Send keyboard input using pydirectinput (Windows games)."""
        norm = [_norm_key(k) for k in keys if k]
        if not norm:
            log.warning("No keys to send.")
            return

        log.info(f"[pydirectinput] Sending keys: {norm} | hold_ms={hold_ms}")

        modifiers = {"ctrl", "shift", "alt"}

        # Chord handling
        if len(norm) >= 2 and all(k in modifiers for k in norm[:-1]):
            mods = norm[:-1]
            final = norm[-1]
            for m in mods:
                pdi.keyDown(m)
            time.sleep(0.01)
            pdi.keyDown(final)
            time.sleep(hold_ms / 1000.0)
            pdi.keyUp(final)
            for m in reversed(mods):
                pdi.keyUp(m)
            return

        # Sequential
        for k in norm:
            pdi.keyDown(k)
            time.sleep(hold_ms / 1000.0)
            pdi.keyUp(k)

    def _send_keyboard_kb(self, keys: list, hold_ms: int):
        """Send keyboard input using keyboard library."""
        norm = [_norm_key(k) for k in keys if k]
        if not norm:
            log.warning("No keys to send.")
            return

        log.info(f"[keyboard] Sending keys: {norm} | hold_ms={hold_ms}")

        modifiers = {"ctrl", "shift", "alt"}

        # Chord handling
        if len(norm) >= 2 and all(k in modifiers for k in norm[:-1]):
            combo = "+".join(norm)
            kb.send(combo, do_press=True, do_release=True)
            return

        # Sequential
        for k in norm:
            kb.press(k)
            time.sleep(hold_ms / 1000.0)
            kb.release(k)

    def _send_keyboard(self, keys: list, hold_ms: int):
        """Route keyboard input to the appropriate backend."""
        if self._backend == "pynput":
            self._send_keyboard_pynput(keys, hold_ms)
        elif self._backend == "pydirectinput":
            self._send_keyboard_pdi(keys, hold_ms)
        elif self._backend == "keyboard":
            self._send_keyboard_kb(keys, hold_ms)
        else:
            log.error("No input backend available. Install pynput: pip install pynput")

    def _send_mouse_pynput(self, buttons: list, hold_ms: int):
        """Send mouse input using pynput (cross-platform)."""
        norm = [_norm_key(b) for b in buttons if b]
        log.info(f"[pynput] Clicking mouse: {norm} | hold_ms={hold_ms}")

        for b in norm:
            if b in PYNPUT_MOUSE_BUTTONS:
                btn = PYNPUT_MOUSE_BUTTONS[b]
                pynput_mouse.press(btn)
                time.sleep(hold_ms / 1000.0)
                pynput_mouse.release(btn)
            else:
                log.warning(f"Unknown mouse button: {b}")

    def _send_mouse_pdi(self, buttons: list, hold_ms: int):
        """Send mouse input using pydirectinput (Windows)."""
        norm = [_norm_key(b) for b in buttons if b]
        log.info(f"[pydirectinput] Clicking mouse: {norm} | hold_ms={hold_ms}")

        for b in norm:
            if b in ("left", "right", "middle"):
                pdi.mouseDown(button=b)
                time.sleep(hold_ms / 1000.0)
                pdi.mouseUp(button=b)
            else:
                log.warning(f"Unknown mouse button: {b}")

    def _send_mouse(self, buttons: list, hold_ms: int):
        """Route mouse input to the appropriate backend."""
        if self._backend == "pynput":
            self._send_mouse_pynput(buttons, hold_ms)
        elif self._backend == "pydirectinput":
            self._send_mouse_pdi(buttons, hold_ms)
        else:
            log.error("Mouse input requires pynput or pydirectinput. Install pynput: pip install pynput")

    def run_macro(self, mapping: dict):
        """Execute a macro from the given mapping."""
        if not mapping:
            return
        typ = mapping.get("type", "keyboard").lower()
        hold_ms = int(mapping.get("hold_ms", 50))
        if typ == "mouse":
            self._send_mouse(mapping.get("buttons", []), hold_ms)
        else:
            self._send_keyboard(mapping.get("keys", []), hold_ms)
