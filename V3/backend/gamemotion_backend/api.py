from fastapi import FastAPI, Body, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import time

app = FastAPI(title="GameMotion Backend API", version="1.0.0")

# CORS for web/electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Runtime shared state (populated by main.py) ----
RUNTIME: Dict[str, Any] = {
    "active_exe": None,
    "active_profile": None,
    "detect_enabled": True,
    "train_request": None,
    "key_sender": None,
    "profile_manager": None,
    "latest_jpeg": b"",
    "stable": 0,
    "last_conf": 0.0,
    "cooldown_left": 0.0,
}

LATEST_SETTINGS: Dict[str, Any] = {}
LATEST_LOG_LINES: List[str] = []

def append_log(line: str):
    LATEST_LOG_LINES.append(line)
    if len(LATEST_LOG_LINES) > 2000:
        del LATEST_LOG_LINES[:1000]

# ---- Health & status ----
@app.get("/health")
def health():
    return {"ok": True, "version": "1.0.0"}

@app.get("/runtime")
def runtime():
    return {
        "active_exe": RUNTIME.get("active_exe"),
        "active_profile": RUNTIME.get("active_profile"),
    }

@app.get("/telemetry")
def telemetry():
    return {
        "online": True,
        "armed": bool(RUNTIME.get("detect_enabled", True)),
        "stable": int(RUNTIME.get("stable", 0)),
        "confidence": float(RUNTIME.get("last_conf", 0.0)),
        "cooldown": float(RUNTIME.get("cooldown_left", 0.0)),
        "exe": RUNTIME.get("active_exe"),
        "profile": RUNTIME.get("active_profile"),
    }

# ---- Detect controls ----
@app.post("/detect/start")
def detect_start():
    RUNTIME["detect_enabled"] = True
    append_log(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] api: detect start")
    return {"started": True}

@app.post("/detect/stop")
def detect_stop():
    RUNTIME["detect_enabled"] = False
    append_log(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] api: detect stop")
    return {"stopped": True}

# ---- Training ----
class TrainPayload(BaseModel):
    game: str
    action: str
    samples: int
    preview: Optional[bool] = True

@app.post("/train/start")
def train_start(payload: TrainPayload):
    RUNTIME["train_request"] = payload.dict()
    append_log(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] api: train request {payload.dict()}")
    return {"started": True}

# ---- Profiles ----
from .profiles import ProfileManager
profman = ProfileManager()

@app.get("/profiles")
def list_profiles():
    # Return list of exe/profile names
    return profman.list_profile_names()

@app.get("/profiles/{exe_name}")
def get_profile(exe_name: str):
    return profman.get_profile_for_exe(exe_name) or {
        "exe_name": exe_name,
        "display_name": exe_name.replace(".exe", ""),
        "actions": {},
    }

@app.post("/profiles/{exe_name}")
def save_profile(exe_name: str, profile: Dict[str, Any] = Body(...)):
    profman.save_profile(exe_name, profile)
    append_log(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] api: saved profile {exe_name}")
    return {"saved": True}

class TriggerBody(BaseModel):
    action: str

@app.post("/profiles/{exe_name}/test")
def trigger_action(exe_name: str, body: TriggerBody):
    prof = profman.get_profile_for_exe(exe_name)
    ks = RUNTIME.get("key_sender")
    if not (prof and ks):
        return {"ok": False, "error": "No active key sender or profile"}
    mapping = prof.get("actions", {}).get(body.action)
    if not mapping:
        return {"ok": False, "error": f"No mapping for action {body.action}"}
    ks.run_macro(mapping)
    return {"ok": True}

# ---- Settings & logs ----
@app.get("/settings")
def get_settings():
    return LATEST_SETTINGS

@app.post("/settings")
def set_settings(settings: Dict[str, Any] = Body(...)):
    LATEST_SETTINGS.clear()
    LATEST_SETTINGS.update(settings)
    append_log(f"{time.strftime('%Y-%m-%d %H:%M:%S')} [INFO] api: settings updated")
    return {"saved": True}

@app.get("/logs")
def tail_logs(tail: int = 500):
    return {"lines": LATEST_LOG_LINES[-tail:]}

# ---- Camera Preview (JPEG) ----
@app.get("/preview.jpg")
def preview_jpg():
    data = RUNTIME.get("latest_jpeg", b"")
    return Response(content=data, media_type="image/jpeg")
