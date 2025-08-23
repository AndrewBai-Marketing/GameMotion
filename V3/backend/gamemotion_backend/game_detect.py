import time, psutil, win32gui, win32process, os, logging
from typing import Optional, Tuple

log = logging.getLogger("game_detect")

def get_foreground_exe() -> Tuple[Optional[str], Optional[str]]:
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None
        tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        exe = None
        title = win32gui.GetWindowText(hwnd)
        for p in psutil.process_iter(['pid', 'name', 'exe']):
            if p.info['pid'] == pid:
                exe = os.path.basename(p.info['exe'] or p.info['name'] or "")
                break
        return exe, title
    except Exception:
        return None, None
