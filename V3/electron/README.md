# GameMotion Electron Wrapper (Cross-Platform)

Electron desktop wrapper for GameMotion, supporting Windows, macOS, and Linux.

Place this `electron/` folder alongside your `backend/` and `frontend/` folders.

---

## Development Setup

### 1. Backend Setup

**Windows:**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ensure your backend exposes **GET /health** on `127.0.0.1:8000`.

### 2. Frontend Setup

```bash
cd frontend
npm install
```

Create `.env.local`:
```
NEXT_PUBLIC_BACKEND_URL=http://127.0.0.1:8000
```

### 3. Electron Setup

```bash
cd electron
npm install
npm run dev
```

---

## Building for Production

### Windows Installer (NSIS)

```powershell
cd electron
npm run build:win
```

Output: `dist/GameMotion Setup x.x.x.exe`

### macOS DMG

```bash
cd electron
npm run build:mac
```

Output: `dist/GameMotion-x.x.x.dmg` (Universal binary for Intel + Apple Silicon)

**Important macOS Notes:**
- Code signing requires an Apple Developer certificate
- Without signing, users must right-click → Open on first launch
- For distribution, notarization is required

### Linux (AppImage/deb)

```bash
cd electron
npm run build:linux
```

Output: `dist/GameMotion-x.x.x.AppImage` and `dist/gamemotion_x.x.x_amd64.deb`

### All Platforms

```bash
npm run build:all
```

---

## Build Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Run in development mode |
| `npm run start` | Start Electron directly |
| `npm run build` | Build for current platform |
| `npm run build:win` | Build Windows installer |
| `npm run build:mac` | Build macOS DMG (x64 + arm64) |
| `npm run build:linux` | Build Linux AppImage/deb |
| `npm run build:all` | Build for all platforms |

---

## macOS Permissions

The macOS build includes entitlements for:
- **Camera** - Required for pose detection
- **Microphone** - Optional for future voice commands
- **Accessibility** - Required for keyboard/mouse simulation
- **Automation** - Required for detecting foreground apps

Users will be prompted to grant these permissions on first launch.

---

## Folder Structure

```
V3/
├── backend/           # Python backend (FastAPI + MediaPipe)
├── frontend/          # Next.js web UI
├── electron/
│   ├── main.js        # Electron main process
│   ├── package.json   # Build configuration
│   └── build/
│       ├── icon.ico           # Windows icon
│       ├── icon.icns          # macOS icon
│       ├── icons/             # Linux icons
│       └── entitlements.mac.plist  # macOS permissions
```

---

## Production Notes

### Static Export Mode

For a fully static build (no server):
1. In `frontend/next.config.js`, add `output: 'export'`
2. Run `npx next build` in frontend
3. Electron will load `frontend/out/index.html`

### Server Mode

For server-side rendering:
1. Run `npm run build` in frontend
2. Electron spawns `next start` as a child process
3. Electron loads `http://127.0.0.1:3000`

---

## Troubleshooting

### Windows
- If the app doesn't start, check that Python is in your PATH
- Run as Administrator if input simulation doesn't work

### macOS
- Grant Accessibility permission: System Preferences → Privacy → Accessibility
- If blocked by Gatekeeper: Right-click → Open
- Camera permission prompt appears on first launch

### Linux
- Install `xdotool` for window detection: `sudo apt install xdotool`
- For Wayland, some features may require X11 compatibility mode
