import os, json, time, logging, pathlib
from dotenv import load_dotenv

load_dotenv()  # load variables from .env into os.environ
ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
PROFILES_DIR = ROOT / "profiles"
DATA_DIR = ROOT / "data"
LOGS_DIR = ROOT / "logs"

def ensure_dirs():
    for d in [CONFIG_DIR, PROFILES_DIR, DATA_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

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
