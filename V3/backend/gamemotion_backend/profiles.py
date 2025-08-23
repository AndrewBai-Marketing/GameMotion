# gamemotion_backend/profiles.py
import json
import pathlib
from typing import Optional, Dict, Any
from .util import PROFILES_DIR

class ProfileManager:
    """
    Loads profiles from profiles/<ExeName>.json.
    Hot-reloads when the file mtime changes so edits in the UI apply immediately.
    """
    def __init__(self, base: pathlib.Path = PROFILES_DIR):
        self.base = base
        self.base.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._mtimes: Dict[str, float] = {}

    def _path_for_exe(self, exe_name: str) -> pathlib.Path:
        # We store profiles as <ExeName>.json (e.g., Notepad.exe.json)
        return self.base / f"{exe_name}.json"

    def get_profile_for_exe(self, exe_name: str, reload_if_changed: bool = True) -> Optional[Dict[str, Any]]:
        path = self._path_for_exe(exe_name)
        if not path.exists():
            return None

        mtime = path.stat().st_mtime
        cached = self._cache.get(exe_name)
        if (cached is None) or (reload_if_changed and self._mtimes.get(exe_name) != mtime):
            try:
                self._cache[exe_name] = json.loads(path.read_text(encoding="utf-8"))
                self._mtimes[exe_name] = mtime
            except Exception:
                return None
        return self._cache.get(exe_name)
    
    def list_profile_names(self):
        """Return profile file stems (e.g., ['Notepad','Minecraft'])."""
        names = []
        for p in PROFILES_DIR.glob("*.json"):
            try:
                # optionally ensure it’s valid JSON
                json.loads(p.read_text(encoding="utf-8"))
                names.append(p.stem)
            except Exception:
                pass
        return sorted(names)
