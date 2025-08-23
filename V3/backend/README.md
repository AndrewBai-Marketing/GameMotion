# GameMotion Backend (Windows-native friendly)

Backend service for **GameMotion**: real-time pose tracking + action mapping to key/mouse inputs,
with optional OpenAI Vision **AI Assist** for action recognition.

> ⚠️ This is **backend only**. A minimal OpenCV preview window is included to visualize the pose overlay.
> You can hook your future native UI to the local API or to the log/events file if you prefer.

---

## Features

- **Real-time pose** with MediaPipe BlazePose (CPU) via OpenCV.
- **Preview window** (toggle with `--preview`) showing camera & skeleton overlay.
- **Profiles per game**: auto-detects the **foreground process** (exe) and switches profile.
- **Train custom actions** per game: capture samples & store feature vectors (angles).
- **Action recognition**:
  - Offline, fast heuristic: compares body angles to your trained samples.
  - Optional **AI Assist** (`--ai-assist`): sends snapshot + labels to OpenAI Vision model to pick the best label.
- **Key/Mouse output** via `pydirectinput` (fallback to `keyboard`/`mouse`) with per-action macros.
- **Local API** (FastAPI, optional): `/health`, `/profile/current`, `/actions/trigger/test`.
- **Windows-native** friendly: no Electron. Package as EXE with PyInstaller if desired.

---

## Quickstart (Windows)

1. **Install Python 3.11+** (64-bit).  
2. Open **PowerShell (Admin recommended)** in the project folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3. (Optional) **OpenAI** — for AI Assist classification. Set your key:
```powershell
setx OPENAI_API_KEY "sk-...your_key_here..."
$env:OPENAI_API_KEY="sk-...your_key_here..."  # For the current shell session
```

4. **Run** pose preview + backend pipeline:
```powershell
python -m gamemotion_backend.main --preview --ai-assist
```
- Remove `--ai-assist` to skip OpenAI calls (offline classifier only).
- Use `Esc` or `Q` to exit the preview window.

5. **Train actions** (example): capture 25 samples for action `LEFT_RAISE` under Minecraft profile.
```powershell
python -m gamemotion_backend.main --train --game "Minecraft.exe" --action "LEFT_RAISE" --samples 25 --preview
```

6. **Profiles**: edit JSON files in `profiles/`. A sample is created for you: `profiles/sample_minecraft.json`.
Map your action labels to key/mouse macros there.

---

## How it works

- `mediapipe` tracks landmarks → we derive an **angle feature vector** (shoulders, elbows, hips, knees, etc.).
- Training saves `(image, landmarks, features)` per sample in `data/<game>/<action>/...`.
- At runtime:
  1. We detect **current foreground exe** (game) and load its profile.
  2. We compute features from the live pose and compare to trained actions.
  3. If confidence is borderline and `--ai-assist` is enabled, we send a snapshot + candidate labels to OpenAI for a tie-break.
  4. When an action fires, we execute its mapped macro (keys/mouse). Cooldowns prevent spam.

---

## Local API (optional)

Start the server (it starts automatically with `main.py`):
- `GET /health` → service status
- `GET /profile/current` → active exe & profile name
- `POST /actions/trigger/test` → body: `{ "action": "LEFT_RAISE" }` to simulate an action event

Default host: `http://127.0.0.1:8000`

---

## Packaging (optional)

You can create a single EXE with PyInstaller (install it first):
```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --name GameMotionBackend --add-data "profiles;profiles" --add-data "config;config" -m gamemotion_backend.main
```

> Some games with anti-cheat may block synthetic input; try running as **Administrator** and prefer `pydirectinput` output.

---

## Folder layout

```
GameMotionBackend/
  gamemotion_backend/
    __init__.py
    main.py
    pose.py
    features.py
    actions.py
    ai_assist.py
    game_detect.py
    key_sender.py
    profiles.py
    api.py
    util.py
  profiles/
    sample_minecraft.json
  data/
  config/
    settings.json
  logs/
  requirements.txt
  README.md
```

---

## Notes & Tips

- **Camera index**: use `--camera 0` (default), change if needed.
- **Performance**: set `--complexity 0` for the fastest MediaPipe mode (default).
- **OpenAI costs**: AI Assist classifies only when needed and respects a cooldown; still, monitor usage.
- **Safety**: Respect game TOS/anti-cheat. This tool is intended for accessibility & rehab use cases.

