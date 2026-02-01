// electron/main.js
const { app, BrowserWindow, shell, Menu } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");
const net = require("net");
const fs = require("fs");

const isDev = process.env.NODE_ENV !== "production";
const isWindows = process.platform === "win32";
const isMac = process.platform === "darwin";
const isLinux = process.platform === "linux";

const FRONTEND_PORT = parseInt(process.env.FRONTEND_PORT || "3000", 10);
const FRONTEND_URL = `http://127.0.0.1:${FRONTEND_PORT}/`;
const BACKEND_URL = "http://127.0.0.1:8000/health";

let win;
let backendProc = null;
let frontendProc = null;

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

/** ---------- find python executable ---------- */
function findPythonExecutable(backendDir) {
  // Check for virtual environment first
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

  // Fallback to system python
  const systemPython = isWindows ? "python" : "python3";
  log("python", `Using system python: ${systemPython}`);
  return systemPython;
}

/** ---------- spawn backend ---------- */
async function startBackend() {
  const backendDir = path.resolve(__dirname, "..", "backend");
  const env = { ...process.env };
  const python = findPythonExecutable(backendDir);
  const args = ["-m", "gamemotion_backend.main"]; // no --preview when inside Electron

  log("backend", `Starting backend with: ${python} ${args.join(" ")}`);
  log("backend", `Working directory: ${backendDir}`);

  backendProc = spawn(python, args, {
    cwd: backendDir,
    env,
    shell: isWindows, // Use shell on Windows for better PATH handling
  });

  backendProc.stdout.on("data", (d) => log("backend", d.toString().trim()));
  backendProc.stderr.on("data", (d) => log("backend", d.toString().trim()));
  backendProc.on("exit", (code, sig) => log("backend", "exited", code, sig));
  backendProc.on("error", (err) => log("backend", "spawn error:", err.message));

  // wait until /health is OK (don't block forever)
  const healthy = await waitForUrl(BACKEND_URL, 20000, 500);
  if (healthy) log("electron", "Backend is healthy");
  else log("electron", "Backend did not report healthy (continuing anyway)");
}

/** ---------- spawn frontend ---------- */
async function startFrontend() {
  const already = await portInUse(FRONTEND_PORT);
  if (already) {
    log("frontend", `port ${FRONTEND_PORT} already in use; not spawning Next`);
    return;
  }

  const frontendDir = path.resolve(__dirname, "..", "frontend");
  const npmCmd = isWindows ? "npm.cmd" : "npm";

  log("frontend", `Starting frontend with: ${npmCmd} run dev`);

  frontendProc = spawn(npmCmd, ["run", "dev", "--", "-p", `${FRONTEND_PORT}`], {
    cwd: frontendDir,
    env: { ...process.env, BROWSER: "none" }, // don't auto-open Chrome
    shell: isWindows
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
    show: false, // show when ready
    backgroundColor: "#111111",
    // macOS specific: show traffic lights
    titleBarStyle: isMac ? "hiddenInset" : "default",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });

  // open target=_blank links in system browser
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  // useful diagnostics
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

  // Build application menu
  const menuTemplate = [
    // macOS app menu
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

  const menu = Menu.buildFromTemplate(menuTemplate);
  Menu.setApplicationMenu(menu);

  // start services, then load URL
  await startBackend();
  await startFrontend();

  const ok = await waitForUrl(FRONTEND_URL, 60000, 500);
  if (!ok) {
    log("electron", `Frontend never became ready at ${FRONTEND_URL}`);
  }

  try {
    await win.loadURL(FRONTEND_URL + "?inElectron=1");
  } catch (e) {
    log("electron", "loadURL error", e.message || e);
    // one retry after small delay
    await sleep(1500);
    try { await win.loadURL(FRONTEND_URL); } catch {}
  }

  if (isDev) win.webContents.openDevTools({ mode: "detach" });
}

// macOS: keep app running even when all windows closed
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  // On macOS, apps typically stay open until explicitly quit
  if (!isMac) app.quit();
});

app.on("before-quit", () => {
  // Clean up child processes
  const treeKill = require("tree-kill");

  if (frontendProc && frontendProc.pid) {
    try {
      treeKill(frontendProc.pid);
    } catch (e) {
      log("cleanup", "Failed to kill frontend:", e.message);
    }
  }

  if (backendProc && backendProc.pid) {
    try {
      treeKill(backendProc.pid);
    } catch (e) {
      log("cleanup", "Failed to kill backend:", e.message);
    }
  }
});
