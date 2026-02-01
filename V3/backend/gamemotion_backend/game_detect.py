import os
import sys
import logging
import psutil
from typing import Optional, Tuple

log = logging.getLogger("game_detect")

IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def get_foreground_exe() -> Tuple[Optional[str], Optional[str]]:
    """
    Get the foreground window's executable name and title.
    Returns (exe_name, window_title) or (None, None) on failure.

    Cross-platform: Windows, macOS, Linux (X11).
    """
    try:
        if IS_WINDOWS:
            return _get_foreground_windows()
        elif IS_MAC:
            return _get_foreground_mac()
        elif IS_LINUX:
            return _get_foreground_linux()
        else:
            log.warning(f"Unsupported platform: {sys.platform}")
            return None, None
    except Exception as e:
        log.debug(f"Failed to get foreground exe: {e}")
        return None, None


def _get_foreground_windows() -> Tuple[Optional[str], Optional[str]]:
    """Windows implementation using win32gui."""
    try:
        import win32gui
        import win32process
    except ImportError:
        log.warning("pywin32 not installed - run: pip install pywin32")
        return None, None

    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None, None

        tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        title = win32gui.GetWindowText(hwnd)
        exe = None

        for p in psutil.process_iter(['pid', 'name', 'exe']):
            if p.info['pid'] == pid:
                exe = os.path.basename(p.info['exe'] or p.info['name'] or "")
                break

        return exe, title
    except Exception as e:
        log.debug(f"Windows foreground detection failed: {e}")
        return None, None


def _get_foreground_mac() -> Tuple[Optional[str], Optional[str]]:
    """macOS implementation using AppKit/NSWorkspace."""
    try:
        from AppKit import NSWorkspace
    except ImportError:
        # Try alternative: use AppleScript via subprocess
        return _get_foreground_mac_applescript()

    try:
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()

        if not active_app:
            return None, None

        # Get the app name (e.g., "Safari", "Minecraft")
        app_name = active_app.localizedName()

        # Get the executable path and extract basename
        bundle_url = active_app.bundleURL()
        if bundle_url:
            # For .app bundles, get the actual executable
            exe_url = active_app.executableURL()
            if exe_url:
                exe_path = exe_url.path()
                exe_name = os.path.basename(exe_path)
            else:
                # Fallback to bundle name
                exe_name = os.path.basename(bundle_url.path())
        else:
            exe_name = app_name

        # Try to get window title using Accessibility API or default to app name
        window_title = _get_mac_window_title(active_app) or app_name

        return exe_name, window_title
    except Exception as e:
        log.debug(f"macOS NSWorkspace detection failed: {e}")
        return _get_foreground_mac_applescript()


def _get_mac_window_title(app) -> Optional[str]:
    """Try to get the window title for a macOS app using Accessibility API."""
    try:
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
            kCGWindowOwnerPID,
            kCGWindowName,
            kCGWindowLayer
        )

        pid = app.processIdentifier()
        window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)

        for window in window_list:
            if window.get(kCGWindowOwnerPID) == pid:
                # Skip menu bar and other system windows (layer != 0)
                if window.get(kCGWindowLayer, 0) == 0:
                    title = window.get(kCGWindowName)
                    if title:
                        return title
        return None
    except Exception:
        return None


def _get_foreground_mac_applescript() -> Tuple[Optional[str], Optional[str]]:
    """Fallback macOS implementation using AppleScript."""
    import subprocess

    try:
        # Get frontmost app name
        script_app = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            return name of frontApp
        end tell
        '''
        result = subprocess.run(
            ['osascript', '-e', script_app],
            capture_output=True, text=True, timeout=2
        )
        app_name = result.stdout.strip() if result.returncode == 0 else None

        if not app_name:
            return None, None

        # Try to get window title
        script_title = f'''
        tell application "System Events"
            tell process "{app_name}"
                try
                    return name of front window
                on error
                    return ""
                end try
            end tell
        end tell
        '''
        result = subprocess.run(
            ['osascript', '-e', script_title],
            capture_output=True, text=True, timeout=2
        )
        window_title = result.stdout.strip() if result.returncode == 0 else app_name

        return app_name, window_title or app_name
    except Exception as e:
        log.debug(f"macOS AppleScript detection failed: {e}")
        return None, None


def _get_foreground_linux() -> Tuple[Optional[str], Optional[str]]:
    """Linux implementation using xdotool (X11) or alternative methods."""
    import subprocess

    # Try xdotool first (most common on X11)
    try:
        # Get active window ID
        result = subprocess.run(
            ['xdotool', 'getactivewindow'],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode != 0:
            return _get_foreground_linux_xprop()

        window_id = result.stdout.strip()

        # Get window name
        result = subprocess.run(
            ['xdotool', 'getwindowname', window_id],
            capture_output=True, text=True, timeout=2
        )
        window_title = result.stdout.strip() if result.returncode == 0 else None

        # Get window PID
        result = subprocess.run(
            ['xdotool', 'getwindowpid', window_id],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode != 0:
            return None, window_title

        pid = int(result.stdout.strip())

        # Get exe from PID
        exe = None
        for p in psutil.process_iter(['pid', 'name', 'exe']):
            if p.info['pid'] == pid:
                exe = os.path.basename(p.info['exe'] or p.info['name'] or "")
                break

        return exe, window_title
    except FileNotFoundError:
        return _get_foreground_linux_xprop()
    except Exception as e:
        log.debug(f"Linux xdotool detection failed: {e}")
        return _get_foreground_linux_xprop()


def _get_foreground_linux_xprop() -> Tuple[Optional[str], Optional[str]]:
    """Fallback Linux implementation using xprop."""
    import subprocess

    try:
        # Get active window ID
        result = subprocess.run(
            ['xprop', '-root', '_NET_ACTIVE_WINDOW'],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode != 0:
            return None, None

        # Parse window ID from output like "_NET_ACTIVE_WINDOW(WINDOW): window id # 0x12345"
        parts = result.stdout.strip().split()
        window_id = parts[-1] if parts else None
        if not window_id or window_id == "0x0":
            return None, None

        # Get window name
        result = subprocess.run(
            ['xprop', '-id', window_id, 'WM_NAME'],
            capture_output=True, text=True, timeout=2
        )
        window_title = None
        if result.returncode == 0:
            # Parse: WM_NAME(STRING) = "Window Title"
            if '=' in result.stdout:
                window_title = result.stdout.split('=', 1)[1].strip().strip('"')

        # Get PID
        result = subprocess.run(
            ['xprop', '-id', window_id, '_NET_WM_PID'],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode != 0:
            return None, window_title

        # Parse: _NET_WM_PID(CARDINAL) = 12345
        pid = None
        if '=' in result.stdout:
            try:
                pid = int(result.stdout.split('=')[1].strip())
            except ValueError:
                pass

        if not pid:
            return None, window_title

        # Get exe from PID
        exe = None
        for p in psutil.process_iter(['pid', 'name', 'exe']):
            if p.info['pid'] == pid:
                exe = os.path.basename(p.info['exe'] or p.info['name'] or "")
                break

        return exe, window_title
    except Exception as e:
        log.debug(f"Linux xprop detection failed: {e}")
        return None, None
