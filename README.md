# GameMotion

Control games with your body using pose detection. GameMotion uses your webcam to track body movements and translates them into keyboard/mouse inputs.

## Requirements

- macOS 12+ (Monterey or newer) or Windows 10+
- Python 3.10 or 3.11
- Webcam

## Quick Start (macOS)

```bash
# Clone the repository
git clone https://github.com/AndrewBai-Marketing/GameMotion.git
cd GameMotion

# Run setup and start
cd V3/backend
chmod +x setup.sh run.sh
./run.sh
```

The first run will install dependencies automatically.

## Permissions (macOS)

Grant these permissions when prompted:

1. **Camera** - Required for pose detection
2. **Accessibility** - Required for sending keyboard/mouse inputs
   - System Settings → Privacy & Security → Accessibility
   - Add Terminal (or your terminal app)

## Usage

1. Run `./run.sh` from the `V3/backend` directory
2. A preview window will open showing your camera feed with skeleton overlay
3. Stand in front of the camera so your body is visible
4. The app will detect your movements and send inputs to the focused game

## Troubleshooting

### SSL Certificate Error (macOS)
If you see certificate errors when downloading the MediaPipe model:
```bash
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
./run.sh
```

### Camera Not Found
- Check camera permissions in System Settings
- Try specifying camera index: `./run.sh --camera 1`

### Keyboard Input Not Working
- Grant Accessibility permissions to your terminal app
- On newer macOS, you may also need Input Monitoring permission

## Project Structure

```
V3/
├── backend/          # Python backend (pose detection, input simulation)
│   ├── setup.sh      # Installs dependencies
│   ├── run.sh        # Runs the backend
│   └── gamemotion_backend/
├── frontend/         # Web UI
└── electron/         # Desktop app wrapper
```
