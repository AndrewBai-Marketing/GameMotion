import os, sys, json, time, logging, pathlib, shutil
from dotenv import load_dotenv

load_dotenv()  # load variables from .env into os.environ


def _resolve_root() -> pathlib.Path:
    """
    Determine the writable root directory for config, profiles, data, logs.

    Priority:
      1. GAMEMOTION_DATA_DIR env var (set by Electron in production)
      2. PyInstaller frozen mode -> platform user data dir
      3. Development fallback -> two levels up from this file (V3/backend/)
    """
    env_dir = os.environ.get("GAMEMOTION_DATA_DIR")
    if env_dir:
        return pathlib.Path(env_dir)

    if getattr(sys, "frozen", False):
        if sys.platform == "darwin":
            return pathlib.Path.home() / "Library" / "Application Support" / "GameMotion"
        elif sys.platform == "win32":
            return pathlib.Path(os.environ.get("APPDATA", str(pathlib.Path.home()))) / "GameMotion"
        else:
            return pathlib.Path.home() / ".config" / "GameMotion"

    return pathlib.Path(__file__).resolve().parent.parent


def _bundled_defaults_dir() -> pathlib.Path:
    """Where default config/profiles live inside a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys._MEIPASS)
    return pathlib.Path(__file__).resolve().parent.parent


ROOT = _resolve_root()
_DEFAULTS = _bundled_defaults_dir()
CONFIG_DIR = ROOT / "config"
PROFILES_DIR = ROOT / "profiles"
DATA_DIR = ROOT / "data"
LOGS_DIR = ROOT / "logs"


def ensure_dirs():
    for d in [CONFIG_DIR, PROFILES_DIR, DATA_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # On first run, copy bundled defaults to writable user directory
    default_settings = _DEFAULTS / "config" / "settings.json"
    if default_settings.exists() and not (CONFIG_DIR / "settings.json").exists():
        shutil.copy2(str(default_settings), str(CONFIG_DIR / "settings.json"))

    default_profiles = _DEFAULTS / "profiles"
    if default_profiles.exists() and not any(PROFILES_DIR.glob("*.json")):
        for f in default_profiles.glob("*.json"):
            dest = PROFILES_DIR / f.name
            if not dest.exists():
                shutil.copy2(str(f), str(dest))

def load_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def setup_logging(level="INFO"):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "backend.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
