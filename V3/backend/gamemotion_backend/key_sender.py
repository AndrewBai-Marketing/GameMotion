import time
import logging

log = logging.getLogger("keys")

# Try multiple backends; prefer pydirectinput for games.
try:
    import pydirectinput as pdi
    pdi.FAILSAFE = False
except Exception:
    pdi = None

try:
    import keyboard as kb  # requires admin for some apps
except Exception:
    kb = None

# Map common aliases -> pydirectinput names (lowercase).
KEY_ALIASES = {
    "spacebar": "space",
    "space": "space",
    "return": "enter",
    "enter": "enter",
    "esc": "esc",
    "escape": "esc",
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
}

def _norm_key(k: str) -> str:
    if not k:
        return ""
    k = k.strip().lower()
    return KEY_ALIASES.get(k, k)

class KeySender:
    """
    mapping examples:
      {"type":"keyboard","keys":["space"],"hold_ms":50}
      {"type":"keyboard","keys":["ctrl","shift","a"],"hold_ms":50}  # chord then release (A while held modifiers)
      {"type":"mouse","buttons":["left"],"hold_ms":50}
    """

    def __init__(self):
        pass

    def _send_keyboard(self, keys, hold_ms):
        norm = [_norm_key(k) for k in keys if k]
        if not norm:
            log.warning("No keys to send.")
            return

        log.info(f"Sending keys (normalized): {norm} | hold_ms={hold_ms}")

        # If it looks like a chord (modifiers + 1), press modifiers, tap final, release
        modifiers = {"ctrl", "shift", "alt"}
        if len(norm) >= 2 and all(k in modifiers for k in norm[:-1]):
            mods = norm[:-1]
            final = norm[-1]
            if pdi:
                for m in mods:
                    pdi.keyDown(m)
                time.sleep(0.01)
                pdi.keyDown(final); time.sleep(hold_ms/1000.0); pdi.keyUp(final)
                for m in reversed(mods):
                    pdi.keyUp(m)
                return
            if kb:
                combo = "+".join(norm[:-1] + [final])
                kb.send(combo, do_press=True, do_release=True)
                return

        # Otherwise send sequential presses
        if pdi:
            for k in norm:
                pdi.keyDown(k)
                time.sleep(hold_ms/1000.0)
                pdi.keyUp(k)
            return

        if kb:
            for k in norm:
                kb.press(k); time.sleep(hold_ms/1000.0); kb.release(k)
            return

        log.error("No input backend available (install pydirectinput or keyboard).")

    def _send_mouse(self, buttons, hold_ms):
        # Lazy mouse via pydirectinput only
        if not pdi:
            log.error("Mouse sending requires pydirectinput.")
            return
        norm = [_norm_key(b) for b in buttons if b]
        log.info(f"Clicking mouse: {norm} | hold_ms={hold_ms}")
        for b in norm:
            if b in ("left", "right", "middle"):
                pdi.mouseDown(button=b); time.sleep(hold_ms/1000.0); pdi.mouseUp(button=b)
            else:
                log.warning(f"Unknown mouse button: {b}")

    def run_macro(self, mapping: dict):
        if not mapping:
            return
        typ = mapping.get("type", "keyboard").lower()
        hold_ms = int(mapping.get("hold_ms", 50))
        if typ == "mouse":
            self._send_mouse(mapping.get("buttons", []), hold_ms)
        else:
            self._send_keyboard(mapping.get("keys", []), hold_ms)
