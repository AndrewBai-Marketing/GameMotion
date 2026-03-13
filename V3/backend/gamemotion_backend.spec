# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for GameMotion Backend
# Build with:  pyinstaller gamemotion_backend.spec --noconfirm

import sys, os, pathlib
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
is_mac = sys.platform == "darwin"
is_win = sys.platform == "win32"

# ── MediaPipe: models + submodules ──────────────────────────────────────
mediapipe_datas = collect_data_files("mediapipe")
mediapipe_imports = collect_submodules("mediapipe")

# ── Platform-specific hidden imports ────────────────────────────────────
platform_imports = []
if is_mac:
    platform_imports += [
        "AppKit", "Cocoa", "Foundation", "Quartz",
        "objc", "PyObjCTools",
    ]
    platform_imports += collect_submodules("AppKit")
    platform_imports += collect_submodules("Quartz")
elif is_win:
    platform_imports += [
        "win32gui", "win32process", "win32api", "win32con", "pywintypes",
        "pydirectinput", "keyboard", "mouse",
    ]

a = Analysis(
    ["gamemotion_backend/main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("config", "config"),
        ("profiles", "profiles"),
    ] + mediapipe_datas,
    hiddenimports=[
        # Core
        "cv2",
        "numpy",
        "PIL",
        "mediapipe",
        # Web server
        "fastapi",
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "pydantic",
        "starlette",
        "starlette.staticfiles",
        "starlette.responses",
        "anyio",
        "anyio._backends",
        "anyio._backends._asyncio",
        # Input
        "pynput",
        "pynput.keyboard",
        "pynput.keyboard._xorg",
        "pynput.keyboard._win32",
        "pynput.keyboard._darwin",
        "pynput.mouse",
        "pynput.mouse._xorg",
        "pynput.mouse._win32",
        "pynput.mouse._darwin",
        # Misc
        "psutil",
        "dotenv",
        # Our own package
        "gamemotion_backend",
        "gamemotion_backend.api",
        "gamemotion_backend.main",
        "gamemotion_backend.util",
        "gamemotion_backend.pose",
        "gamemotion_backend.features",
        "gamemotion_backend.actions",
        "gamemotion_backend.game_detect",
        "gamemotion_backend.key_sender",
        "gamemotion_backend.profiles",
    ] + mediapipe_imports + platform_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt6", "PyQt5", "tkinter",   # not needed in Electron mode
        "openai",                        # optional feature
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GameMotionBackend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    # For Mac App Store builds, set CODESIGN_IDENTITY env var to your
    # "Apple Distribution: ..." certificate name and point ENTITLEMENTS_FILE
    # to the backend.entitlements path before running pyinstaller.
    codesign_identity=os.environ.get("CODESIGN_IDENTITY"),
    entitlements_file=os.environ.get(
        "ENTITLEMENTS_FILE",
        str(pathlib.Path(SPECPATH).parent / "macos" / "GameMotion" / "backend.entitlements")
        if is_mac else None,
    ),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GameMotionBackend",
)
