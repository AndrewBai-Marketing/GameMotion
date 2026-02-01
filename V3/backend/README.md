# GameMotion Backend (Cross-Platform)

Backend service for **GameMotion**: real-time pose tracking + action mapping to key/mouse inputs,
with optional OpenAI Vision **AI Assist** for action recognition.

> ⚠️ This is **backend only**. A minimal OpenCV preview window is included to visualize the pose overlay.
> You can hook your future native UI to the local API or to the log/events file if you prefer.

---

## Features

- **Real-time pose** with MediaPipe BlazePose (CPU) via OpenCV.
- **Cross-platform support**: Windows, macOS, and Linux.
- **Preview window** (toggle with `--preview`) showing camera & skeleton overlay.
- **Profiles per game**: auto-detects the **foreground process** (exe/app) and switches profile.
- **Train custom actions** per game: capture samples & store feature vectors (angles).
- **Action recognition**:
  - Offline, fast heuristic: compares body angles to your trained samples.
  - Optional **AI Assist** (`--ai-assist`): sends snapshot + labels to OpenAI Vision model to pick the best label.
- **Key/Mouse output** via `pynput` (cross-platform) with fallback to `pydirectinput` on Windows.
- **Local API** (FastAPI, optional): `/health`, `/profile/current`, `/actions/trigger/test`.
- **Fast startup**: Parallel initialization with lazy model loading.

---

## Quickstart

### Windows

1. **Install Python 3.11+** (64-bit).
2. Open **PowerShell (Admin recommended)** in the project folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3. **Run** pose preview + backend pipeline:
```powershell
python -m gamemotion_backend.main --preview
```

### macOS

1. **Install Python 3.11+** via Homebrew or python.org:
```bash
brew install python@3.11
```

2. **Create virtual environment** and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Grant permissions** (required for input simulation):
   - Open **System Preferences → Security & Privacy → Privacy**
   - Add Terminal (or your IDE) to:
     - **Accessibility** (for keyboard/mouse control)
     - **Camera** (for pose detection)
     - **Automation** (for app detection)

4. **Run** pose preview + backend pipeline:
```bash
python -m gamemotion_backend.main --preview
```

### Linux

1. **Install Python 3.11+** and dependencies:
```bash
sudo apt install python3.11 python3.11-venv xdotool
```

2. **Create virtual environment** and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Run** pose preview + backend pipeline:
```bash
python -m gamemotion_backend.main --preview
```

> **Note**: On Wayland, window detection may be limited. X11 is recommended for full functionality.

---

## OpenAI Integration (Optional)

For AI Assist classification, set your OpenAI API key:

**Windows:**
```powershell
setx OPENAI_API_KEY "sk-...your_key_here..."
```

**macOS/Linux:**
```bash
export OPENAI_API_KEY="sk-...your_key_here..."
```

Then run with `--ai-assist`:
```bash
python -m gamemotion_backend.main --preview --ai-assist
```

---

## Training Actions

Capture samples for a custom action (example: 25 samples for `LEFT_RAISE` in Minecraft):

**Windows:**
```powershell
python -m gamemotion_backend.main --train --game "Minecraft.exe" --action "LEFT_RAISE" --samples 25 --preview
```

**macOS:**
```bash
python -m gamemotion_backend.main --train --game "java" --action "LEFT_RAISE" --samples 25 --preview
```

---

## How it works

- `mediapipe` tracks landmarks → we derive an **angle feature vector** (shoulders, elbows, hips, knees, etc.).
- Training saves `(image, landmarks, features)` per sample in `data/<game>/<action>/...`.
- At runtime:
  1. We detect **current foreground app** (exe/process) and load its profile.
  2. We compute features from the live pose and compare to trained actions.
  3. If confidence is borderline and `--ai-assist` is enabled, we send a snapshot + candidate labels to OpenAI for a tie-break.
  4. When an action fires, we execute its mapped macro (keys/mouse). Cooldowns prevent spam.

---

## Local API

Start the server (it starts automatically with `main.py`):
- `GET /health` → service status
- `GET /runtime` → active exe & profile name
- `GET /telemetry` → detection state (armed, confidence, cooldown)
- `POST /detect/start` / `POST /detect/stop` → enable/disable detection
- `POST /train/start` → start training mode
- `GET /preview.jpg` → live camera frame with pose overlay

Default host: `http://127.0.0.1:8000`

---

## Packaging

### Windows (PyInstaller)

```powershell
pip install pyinstaller
pyinstaller --noconfirm --onefile --name GameMotionBackend --add-data "profiles;profiles" --add-data "config;config" -m gamemotion_backend.main
```

### macOS (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --name GameMotionBackend --add-data "profiles:profiles" --add-data "config:config" gamemotion_backend/main.py
```

> **Note**: macOS apps require code signing for Accessibility permissions to work properly in distributed builds.

---

## Folder Layout

```
backend/
  gamemotion_backend/
    __init__.py
    main.py          # Entry point with parallel initialization
    pose.py          # MediaPipe pose tracking (lazy loading)
    features.py      # Angle feature extraction
    actions.py       # Action recognition
    ai_assist.py     # OpenAI Vision integration
    game_detect.py   # Cross-platform foreground app detection
    key_sender.py    # Cross-platform keyboard/mouse simulation
    profiles.py      # Profile management
    api.py           # FastAPI server
    util.py          # Utilities
  profiles/
    sample_minecraft.json
  data/              # Training data
  config/
    settings.json
  logs/
  requirements.txt
  README.md
```

---

## Platform-Specific Notes

### Windows
- `pydirectinput` is preferred for games using DirectInput.
- Some games with anti-cheat may block synthetic input; try running as **Administrator**.

### macOS
- Requires **Accessibility** permission for keyboard/mouse simulation.
- Input simulation uses `pynput` which works with most apps.
- Some games may require additional permissions or run in windowed mode.

### Linux
- Uses `xdotool` for window detection (install via package manager).
- Wayland support is limited; X11 recommended.
- May require `sudo` for some input simulation scenarios.

---

## Notes & Tips

- **Camera index**: use `--camera 0` (default), change if needed.
- **Performance**: set `--complexity 0` for the fastest MediaPipe mode (default).
- **Startup time**: The backend now uses parallel initialization and lazy model loading for faster startup.
- **OpenAI costs**: AI Assist classifies only when needed and respects a cooldown; still, monitor usage.
- **Safety**: Respect game TOS/anti-cheat. This tool is intended for accessibility & rehab use cases.
