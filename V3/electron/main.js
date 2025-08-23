// electron/main.js
const { app, BrowserWindow, shell, Menu } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const http = require("http");
const net = require("net");

const isDev = process.env.NODE_ENV !== "production";
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

/** ---------- spawn backend ---------- */
async function startBackend() {
  const backendDir = path.resolve(__dirname, "..", "backend");
  const env = { ...process.env };
  const python = path.join(backendDir, ".venv", "Scripts", "python.exe");
  const args = ["-m", "gamemotion_backend.main"]; // no --preview when inside Electron

  backendProc = spawn(python, args, { cwd: backendDir, env, shell: true });
  backendProc.stdout.on("data", (d) => log("backend", d.toString().trim()));
  backendProc.stderr.on("data", (d) => log("backend", d.toString().trim()));
  backendProc.on("exit", (code, sig) => log("backend", "exited", code, sig));

  // wait until /health is OK (don’t block forever)
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
  frontendProc = spawn(process.platform === "win32" ? "npm.cmd" : "npm", ["run", "dev", "--", "-p", `${FRONTEND_PORT}`], {
    cwd: frontendDir,
    env: { ...process.env, BROWSER: "none" }, // don’t auto-open Chrome
    shell: true
  });
  frontendProc.stdout.on("data", (d) => log("frontend", d.toString().trim()));
  frontendProc.stderr.on("data", (d) => log("frontend", d.toString().trim()));
  frontendProc.on("exit", (code, sig) => log("frontend", "exited", code, sig));
}

/** ---------- create window ---------- */
async function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 800,
    show: false, // show when ready
    backgroundColor: "#111111",
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

  // simple app menu (adds DevTools toggle)
  const menu = Menu.buildFromTemplate([
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forcereload" },
        { type: "separator" },
        {
          label: "Toggle DevTools (F12)",
          accelerator: "F12",
          click: () => win.webContents.toggleDevTools(),
        },
      ],
    },
  ]);
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

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  try { if (frontendProc) frontendProc.kill(); } catch {}
  try { if (backendProc) backendProc.kill(); } catch {}
});
