# gamemotion_backend/ui_main.py

import sys, os, json, pathlib, subprocess, threading, time, logging
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QTextEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import QTimer
from dotenv import load_dotenv
import requests

load_dotenv()

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROFILES_DIR = ROOT / "profiles"
LOGS_DIR = ROOT / "logs"

API_HOST = "127.0.0.1"
API_PORT = 8000
API_BASE = f"http://{API_HOST}:{API_PORT}"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("UI")


def _safe_read_json(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


class GameMotionUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GameMotion UI")
        self.resize(1150, 720)

        # child process handle for detection backend
        self.det_proc: subprocess.Popen | None = None

        layout = QVBoxLayout()

        # ---- Profile bar ----
        profbar = QHBoxLayout()
        profbar.addWidget(QLabel("Profile:"))
        self.profile_dropdown = QComboBox()
        profbar.addWidget(self.profile_dropdown)

        self.save_profile_btn = QPushButton("Save Profile")
        profbar.addWidget(self.save_profile_btn)

        self.start_btn = QPushButton("Start Detection")
        self.stop_btn = QPushButton("Stop Detection")
        self.stop_btn.setEnabled(False)
        profbar.addWidget(self.start_btn)
        profbar.addWidget(self.stop_btn)

        layout.addLayout(profbar)

        # ---- Actions table ----
        self.action_table = QTableWidget(0, 4)
        self.action_table.setHorizontalHeaderLabels(
            ["Action", "Type (keyboard/mouse)", "Keys/Buttons (comma)", "Hold (ms)"]
        )
        self.action_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.action_table)

        # ---- Status row ----
        self.exe_label = QLabel("Active exe: - (Profile: -)")
        self.exe_label.setStyleSheet("font-size:16px; font-weight:bold; color:#ffaa00")
        layout.addWidget(self.exe_label)

        # ---- Training controls (offline-only; no AI) ----
        train_row = QHBoxLayout()
        self.game_input = QLineEdit()
        self.game_input.setPlaceholderText("Game EXE (e.g., Minecraft.exe)")
        self.action_input = QLineEdit()
        self.action_input.setPlaceholderText("Action label (e.g., JUMP)")
        self.samples_spin = QSpinBox()
        self.samples_spin.setRange(5, 200)
        self.samples_spin.setValue(25)
        self.train_btn = QPushButton("Start Training")
        train_row.addWidget(self.game_input)
        train_row.addWidget(self.action_input)
        train_row.addWidget(self.samples_spin)
        train_row.addWidget(self.train_btn)
        layout.addLayout(train_row)

        # ---- Logs ----
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        layout.addWidget(self.log_window)

        self.setLayout(layout)

        # Wire signals
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.profile_dropdown.currentIndexChanged.connect(self.load_selected_profile)
        self.train_btn.clicked.connect(self.start_training_clicked)
        self.start_btn.clicked.connect(self.start_detection)
        self.stop_btn.clicked.connect(self.stop_detection)

        # Populate profiles
        self.load_profiles()
        if self.profile_dropdown.count() > 0:
            self.load_selected_profile()

        # UI update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000)

    # ----------------- detection (subprocess) -----------------
    def start_detection(self):
        if self.det_proc and self.det_proc.poll() is None:
            self.log_window.append("ℹ️ Detection already running.")
            return

        args = [sys.executable, "-m", "gamemotion_backend.main", "--preview"]
        # Launch backend as a child process so we can stop it cleanly and avoid port reuse
        self.det_proc = subprocess.Popen(args, cwd=str(ROOT))
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_window.append("🚀 Detection started.")

    def stop_detection(self):
        if self.det_proc and self.det_proc.poll() is None:
            try:
                self.det_proc.kill()
                self.det_proc.wait(timeout=5)
                self.log_window.append("🛑 Detection stopped.")
            except Exception as e:
                self.log_window.append(f"❌ Failed to stop detection: {e}")
        self.det_proc = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    # ----------------- training (subprocess) -----------------
    def start_training_clicked(self):
        game = self.game_input.text().strip()
        action = self.action_input.text().strip()
        samples = int(self.samples_spin.value())
        if not game or not action:
            self.log_window.append("❌ Enter Game EXE and Action first.")
            return

        # Stop detection first so camera/API port are free
        was_running = (self.det_proc and self.det_proc.poll() is None)
        if was_running:
            self.stop_detection()

        threading.Thread(
            target=self._train_thread, args=(game, action, samples, was_running), daemon=True
        ).start()

    def _train_thread(self, game: str, action: str, samples: int, restart_after: bool):
        self.log_window.append(f"⚡ Training {action} for {game} ({samples} samples)…")

        args = [sys.executable, "-m", "gamemotion_backend.main",
                "--train", "--game", game, "--action", action,
                "--samples", str(samples), "--preview", "--no-api"]

        # run blocking
        try:
            subprocess.run(args, cwd=str(ROOT), check=True)
            self.log_window.append("✅ Training finished.")
        except subprocess.CalledProcessError as e:
            self.log_window.append(f"❌ Training failed: {e}")
            return

        # Write/Update the profile JSON the UI loads: profiles/<GameExe>.json
        profile_path = PROFILES_DIR / f"{game}.json"
        if profile_path.exists():
            profile = _safe_read_json(profile_path, {"exe_name": game, "display_name": game.replace(".exe",""), "actions": {}})
        else:
            profile = {"exe_name": game, "display_name": game.replace(".exe",""), "actions": {}}

        if action not in profile.get("actions", {}):
            # Default so it shows up immediately (edit in table as needed)
            profile["actions"][action] = {"type": "keyboard", "keys": ["space"], "hold_ms": 50}
            profile_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
            self.log_window.append(f"✅ Added '{action}' to {profile_path.name}")

        # Reload profiles and table
        self.load_profiles()
        idx = self.profile_dropdown.findText(profile_path.stem)
        if idx >= 0:
            self.profile_dropdown.setCurrentIndex(idx)
        self.load_selected_profile()

        # Restart detection if it was running before
        if restart_after:
            self.log_window.append("🔄 Restarting detection…")
            self.start_detection()

    # ----------------- profiles & table -----------------
    def load_profiles(self):
        self.profile_dropdown.clear()
        PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        for f in sorted(PROFILES_DIR.glob("*.json")):
            self.profile_dropdown.addItem(f.stem, f)

    def load_selected_profile(self):
        path: pathlib.Path = self.profile_dropdown.currentData()
        if not path:
            self.action_table.setRowCount(0)
            return
        prof = _safe_read_json(path, {"actions": {}})
        actions = prof.get("actions", {})

        self.action_table.setRowCount(0)
        for act, mapping in actions.items():
            row = self.action_table.rowCount()
            self.action_table.insertRow(row)
            self.action_table.setItem(row, 0, QTableWidgetItem(act))
            self.action_table.setItem(row, 1, QTableWidgetItem(mapping.get("type", "keyboard")))
            keys_or_buttons = mapping.get("keys") or mapping.get("buttons") or []
            self.action_table.setItem(row, 2, QTableWidgetItem(",".join(keys_or_buttons)))
            self.action_table.setItem(row, 3, QTableWidgetItem(str(mapping.get("hold_ms", 50))))

    def save_profile(self):
        path: pathlib.Path = self.profile_dropdown.currentData()
        if not path:
            self.log_window.append("❌ No profile selected.")
            return

        prof = _safe_read_json(path, {"exe_name": path.stem, "display_name": path.stem, "actions": {}})
        actions = {}

        for row in range(self.action_table.rowCount()):
            a_item = self.action_table.item(row, 0)
            t_item = self.action_table.item(row, 1)
            k_item = self.action_table.item(row, 2)
            h_item = self.action_table.item(row, 3)
            if not a_item:
                continue
            act = a_item.text().strip()
            if not act:
                continue

            typ = (t_item.text().strip().lower() if t_item and t_item.text() else "keyboard")
            keys_field = (k_item.text().strip() if k_item and k_item.text() else "")
            hold = int((h_item.text().strip() if h_item and h_item.text().strip() else "50"))

            values = [x.strip().lower() for x in keys_field.split(",")] if keys_field else []

            if typ == "mouse":
                actions[act] = {"type": "mouse", "buttons": values, "hold_ms": hold}
            else:
                actions[act] = {"type": "keyboard", "keys": values, "hold_ms": hold}

        prof["actions"] = actions
        path.write_text(json.dumps(prof, indent=2), encoding="utf-8")
        self.log_window.append(f"✅ Saved {path.name}")

    # ----------------- UI heartbeat -----------------
    def update_ui(self):
        # Update exe/profile via API (if detection is running)
        exe = "-"
        profname = "-"
        try:
            r = requests.get(f"{API_BASE}/profile/current", timeout=0.25)
            if r.ok:
                data = r.json()
                exe = data.get("exe") or "-"
                profname = data.get("profile") or "-"
        except Exception:
            pass
        self.exe_label.setText(f"Active exe: {exe} (Profile: {profname})")

        # Logs (tail)
        try:
            if LOGS_DIR.exists():
                with open(LOGS_DIR / "backend.log", "r", encoding="utf-8") as f:
                    self.log_window.setText("".join(f.readlines()[-20:]))
        except Exception:
            pass

    # --------------- cleanup ---------------
    def closeEvent(self, event):
        try:
            self.stop_detection()
        finally:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = GameMotionUI()
    ui.show()
    sys.exit(app.exec())
