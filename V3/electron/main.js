// electron/main.js
const { app, BrowserWindow, shell, Menu } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");
const net = require("net");
const fs = require("fs");

const isWindows = process.platform === "win32";
const isMac = process.platform === "darwin";
const isPackaged = app.isPackaged;

const BACKEND_PORT = 8000;
const BACKEND_HEALTH_URL = `http://127.0.0.1:${BACKEND_PORT}/health`;
const FRONTEND_PORT = parseInt(process.env.FRONTEND_PORT || "3000", 10);

let win;
let backendProc = null;
let frontendProc = null; // dev mode only

/** ---------- tiny utils ---------- */
function log(tag, ...args) {
  console.log(`[${tag}]`, ...args);
}
function sleep(ms) { return new Promise(res => setTimeout(res, ms)); }
function portInUse(port) {
  return new Promise((resolve) => {
    const srv = net.createServer().once("error", () => resolve(true)).once("listening", () => {
      srv.close(() => resolve(false));
    }).listen(port, "127.0.0.1");
  });
}
async function waitForUrl(url, timeoutMs = 30000, intervalMs = 500) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const ok = await new Promise((resolve) => {
        const req = http.get(url, (res) => {
          const ct = (res.headers["content-type"] || "").toString();
          resolve(res.statusCode === 200 && (ct.includes("text/html") || ct.includes("application/json")));
        });
        req.on("error", () => resolve(false));
        req.setTimeout(3000, () => { req.destroy(); resolve(false); });
      });
      if (ok) return true;
    } catch {}
    await sleep(intervalMs);
  }
  return false;
}

/** ========== PRODUCTION: launch PyInstaller binary ========== */
async function startBackendProduction() {
  const backendDir = path.join(process.resourcesPath, "backend", "GameMotionBackend");
  const frontendDir = path.join(process.resourcesPath, "frontend");
  const userDataDir = app.getPath("userData");

  const exeName = isWindows ? "GameMotionBackend.exe" : "GameMotionBackend";
  const exePath = path.join(backendDir, exeName);

  if (!fs.existsSync(exePath)) {
    log("backend", `ERROR: Backend binary not found at ${exePath}`);
    return;
  }

  const env = {
    ...process.env,
    GAMEMOTION_DATA_DIR: userDataDir,
  };

  const args = ["--static-dir", frontendDir];

  log("backend", `Starting production backend: ${exePath}`);
  log("backend", `Static frontend dir: ${frontendDir}`);
  log("backend", `User data dir: ${userDataDir}`);

  backendProc = spawn(exePath, args, {
    cwd: backendDir,
    env,
    stdio: ["ignore", "pipe", "pipe"],
  });

  backendProc.stdout.on("data", (d) => log("backend", d.toString().trim()));
  backendProc.stderr.on("data", (d) => log("backend", d.toString().trim()));
  backendProc.on("exit", (code, sig) => log("backend", "exited", code, sig));
  backendProc.on("error", (err) => log("backend", "spawn error:", err.message));

  const healthy = await waitForUrl(BACKEND_HEALTH_URL, 30000, 500);
  if (healthy) log("electron", "Backend is healthy");
  else log("electron", "Backend did not report healthy (continuing anyway)");
}

/** ========== DEVELOPMENT: spawn python + npm run dev ========== */
function findPythonExecutable(backendDir) {
  const venvPaths = isWindows
    ? [
        path.join(backendDir, ".venv", "Scripts", "python.exe"),
        path.join(backendDir, "venv", "Scripts", "python.exe"),
      ]
    : [
        path.join(backendDir, ".venv", "bin", "python"),
        path.join(backendDir, "venv", "bin", "python"),
        path.join(backendDir, ".venv", "bin", "python3"),
        path.join(backendDir, "venv", "bin", "python3"),
      ];

  for (const p of venvPaths) {
    if (fs.existsSync(p)) {
      log("python", `Found venv python at: ${p}`);
      return p;
    }
  }

  const systemPython = isWindows ? "python" : "python3";
  log("python", `Using system python: ${systemPython}`);
  return systemPython;
}

async function startBackendDev() {
  const backendDir = path.resolve(__dirname, "..", "backend");
  const python = findPythonExecutable(backendDir);
  const args = ["-m", "gamemotion_backend.main"];

  log("backend", `[DEV] Starting: ${python} ${args.join(" ")}`);

  backendProc = spawn(python, args, {
    cwd: backendDir,
    env: { ...process.env },
    shell: isWindows,
  });

  backendProc.stdout.on("data", (d) => log("backend", d.toString().trim()));
  backendProc.stderr.on("data", (d) => log("backend", d.toString().trim()));
  backendProc.on("exit", (code, sig) => log("backend", "exited", code, sig));
  backendProc.on("error", (err) => log("backend", "spawn error:", err.message));

  const healthy = await waitForUrl(BACKEND_HEALTH_URL, 20000, 500);
  if (healthy) log("electron", "Backend is healthy");
  else log("electron", "Backend did not report healthy (continuing anyway)");
}

async function startFrontendDev() {
  const already = await portInUse(FRONTEND_PORT);
  if (already) {
    log("frontend", `[DEV] port ${FRONTEND_PORT} already in use; not spawning Next`);
    return;
  }

  const frontendDir = path.resolve(__dirname, "..", "frontend");
  const npmCmd = isWindows ? "npm.cmd" : "npm";

  log("frontend", `[DEV] Starting: ${npmCmd} run dev`);

  frontendProc = spawn(npmCmd, ["run", "dev", "--", "-p", `${FRONTEND_PORT}`], {
    cwd: frontendDir,
    env: { ...process.env, BROWSER: "none" },
    shell: isWindows,
  });

  frontendProc.stdout.on("data", (d) => log("frontend", d.toString().trim()));
  frontendProc.stderr.on("data", (d) => log("frontend", d.toString().trim()));
  frontendProc.on("exit", (code, sig) => log("frontend", "exited", code, sig));
  frontendProc.on("error", (err) => log("frontend", "spawn error:", err.message));
}

/** ---------- create window ---------- */
async function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 800,
    show: false,
    backgroundColor: "#111111",
    titleBarStyle: isMac ? "hiddenInset" : "default",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  win.webContents.on("did-fail-load", (e, code, desc, url) => {
    log("renderer", `did-fail-load ${code} ${desc} url=${url}`);
  });
  win.webContents.on("did-finish-load", () => {
    log("renderer", "did-finish-load");
    if (!win.isVisible()) win.show();
  });
  win.webContents.on("console-message", (_e, level, message) => {
    log("console", message);
  });

  // Application menu
  const menuTemplate = [
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: "about" },
        { type: "separator" },
        { role: "services" },
        { type: "separator" },
        { role: "hide" },
        { role: "hideOthers" },
        { role: "unhide" },
        { type: "separator" },
        { role: "quit" }
      ]
    }] : []),
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { type: "separator" },
        {
          label: "Toggle DevTools",
          accelerator: isMac ? "Cmd+Option+I" : "F12",
          click: () => win.webContents.toggleDevTools(),
        },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" }
      ],
    },
    {
      label: "Window",
      submenu: [
        { role: "minimize" },
        { role: "zoom" },
        ...(isMac ? [
          { type: "separator" },
          { role: "front" },
          { type: "separator" },
          { role: "window" }
        ] : [
          { role: "close" }
        ])
      ]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate));

  if (isPackaged) {
    // ── PRODUCTION ──────────────────────────────────────────────
    log("electron", "Running in PRODUCTION mode");
    await startBackendProduction();

    const appUrl = `http://127.0.0.1:${BACKEND_PORT}/`;
    const ok = await waitForUrl(appUrl, 30000, 500);
    if (!ok) log("electron", `App never became ready at ${appUrl}`);

    try {
      await win.loadURL(appUrl);
    } catch (e) {
      log("electron", "loadURL error", e.message || e);
      await sleep(1500);
      try { await win.loadURL(appUrl); } catch {}
    }

  } else {
    // ── DEVELOPMENT ────────────────────────────────────────────
    log("electron", "Running in DEVELOPMENT mode");
    await startBackendDev();
    await startFrontendDev();

    const frontendUrl = `http://127.0.0.1:${FRONTEND_PORT}/`;
    const ok = await waitForUrl(frontendUrl, 60000, 500);
    if (!ok) log("electron", `Frontend never became ready at ${frontendUrl}`);

    try {
      await win.loadURL(frontendUrl + "?inElectron=1");
    } catch (e) {
      log("electron", "loadURL error", e.message || e);
      await sleep(1500);
      try { await win.loadURL(frontendUrl); } catch {}
    }

    win.webContents.openDevTools({ mode: "detach" });
  }
}

// macOS: keep app running when all windows closed
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (!isMac) app.quit();
});

app.on("before-quit", () => {
  const treeKill = require("tree-kill");

  if (frontendProc && frontendProc.pid) {
    try { treeKill(frontendProc.pid); } catch (e) {
      log("cleanup", "Failed to kill frontend:", e.message);
    }
  }

  if (backendProc && backendProc.pid) {
    try { treeKill(backendProc.pid); } catch (e) {
      log("cleanup", "Failed to kill backend:", e.message);
    }
  }
});
