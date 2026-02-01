# macOS Testing Guide

This guide covers testing the GameMotion Mac port. The goal is to verify that all functionality works correctly on macOS.

## Quick Setup

```bash
# 1. Clone and checkout the mac-support branch
git clone https://github.com/AndrewBai-Marketing/GameMotion.git
cd GameMotion
git checkout mac-support

# 2. Run setup (installs Python dependencies)
cd V3/backend
chmod +x setup.sh run.sh
./setup.sh

# 3. Run the backend
./run.sh
```

## Prerequisites

- macOS 12+ (Monterey or newer recommended)
- Python 3.10 or 3.11
- Webcam (built-in or external)
- A game to test with (any game that uses keyboard controls)

## Permission Requirements

macOS will prompt for these permissions - **grant all of them**:

1. **Camera** - Required for pose detection
2. **Accessibility** - Required for sending keyboard/mouse inputs to games
   - Go to: System Preferences → Privacy & Security → Accessibility
   - Add Terminal (or your terminal app) to the list

## Testing Checklist

### Test 1: Basic Startup
**Objective:** Verify the backend starts without errors

```bash
./run.sh
```

**Expected Result:**
- No Python errors or tracebacks
- You should see output like:
  ```
  INFO: Uvicorn running on http://127.0.0.1:7777
  ```
- A preview window should open showing your camera feed

**Pass Criteria:** Backend starts, camera preview shows your body

---

### Test 2: Pose Detection
**Objective:** Verify MediaPipe detects body landmarks

**Steps:**
1. Start the backend with `./run.sh`
2. Stand in front of the camera
3. Move your arms around

**Expected Result:**
- Skeleton overlay appears on your body in the preview window
- Landmarks track your movements smoothly

**Pass Criteria:** Skeleton visible and tracking in real-time

---

### Test 3: API Health Check
**Objective:** Verify the API server responds

```bash
# In a new terminal, while the backend is running:
curl http://127.0.0.1:7777/health
```

**Expected Result:**
```json
{"ok":true,"version":"1.0.0"}
```

**Pass Criteria:** Returns `ok: true`

---

### Test 4: Keyboard Input Simulation
**Objective:** Verify pynput can send keystrokes

```bash
# Run this test (will type "hello" after 3 seconds - focus a text editor!)
cd V3/backend
.venv/bin/python -c "
import time
from gamemotion_backend.key_sender import KeySender

ks = KeySender()
print('KeySender backend:', ks._backend)
print('Typing \"hello\" in 3 seconds... focus a text editor!')
time.sleep(3)

for char in 'hello':
    ks.run_macro({'type': 'keyboard', 'keys': [char], 'hold_ms': 50})
    time.sleep(0.1)

print('Done!')
"
```

**Expected Result:**
- "hello" appears in your focused text editor
- No permission errors

**Pass Criteria:** Text is typed successfully

---

### Test 5: Game Detection
**Objective:** Verify foreground window detection works

```bash
cd V3/backend
.venv/bin/python -c "
from gamemotion_backend.game_detect import get_foreground_exe
import time

print('Checking foreground window every 2 seconds...')
print('Switch between different apps to test.')
print('Press Ctrl+C to stop.\n')

while True:
    exe, title = get_foreground_exe()
    print(f'Foreground: {exe} - {title[:50]}')
    time.sleep(2)
"
```

**Expected Result:**
- Shows the currently focused app name
- Updates when you switch apps

**Pass Criteria:** Correctly identifies foreground application

---

### Test 6: Full Integration (with a Game)
**Objective:** Test the complete flow with an actual game

**Steps:**
1. Start a game that uses keyboard controls (e.g., a simple platformer, Minecraft, etc.)
2. Start GameMotion: `./run.sh`
3. The app should detect the game
4. Record a gesture (if the UI supports it) or use an existing profile
5. Perform the gesture and verify the game receives the input

**Pass Criteria:** Gestures trigger keyboard inputs in the game

---

## Troubleshooting

### "Camera not found" or black preview
- Check camera permissions in System Preferences
- Try specifying camera index: `./run.sh --camera 1`

### "pynput" errors or no keyboard input
- Grant Accessibility permissions to Terminal
- On newer macOS, you may need to grant Input Monitoring permission too

### "mediapipe" import errors
- Make sure you're using the virtual environment: `.venv/bin/python`
- Re-run `./setup.sh` to reinstall dependencies

### Game doesn't receive inputs
- Some games with anti-cheat may block simulated inputs
- Try testing with a simple app first (TextEdit, Notes)

## Reporting Issues

If something doesn't work, please report:

1. **macOS version** (e.g., macOS 14.2 Sonoma)
2. **Python version** (`python3 --version`)
3. **Mac chip** (Intel or Apple Silicon M1/M2/M3)
4. **Full error message** (copy the entire traceback)
5. **Which test failed** (reference the test number above)

Create an issue at: https://github.com/AndrewBai-Marketing/GameMotion/issues

## Success Criteria

The Mac port is considered working if:
- [ ] Test 1: Backend starts without errors
- [ ] Test 2: Pose detection works with skeleton overlay
- [ ] Test 3: API responds correctly
- [ ] Test 4: Keyboard simulation works
- [ ] Test 5: Game/window detection works
- [ ] Test 6: Full integration with a real game works

Thank you for testing!
