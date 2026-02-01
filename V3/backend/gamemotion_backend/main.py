import cv2, os, sys, time, argparse, logging, threading, pathlib, json
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from .util import ensure_dirs, load_json, setup_logging, CONFIG_DIR
from .pose import PoseTracker
from .features import extract_angle_signature
from .actions import ActionRecognizer, ActionDB
from .game_detect import get_foreground_exe
from .key_sender import KeySender
from .profiles import ProfileManager

# FastAPI app + runtime (no circular import)
from .api import app as fastapi_app, RUNTIME as API_RUNTIME, append_log
import uvicorn

log = logging.getLogger("main")

# Platform detection
IS_WINDOWS = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

# Event to signal when API server is ready
_api_ready = threading.Event()


def run_api_server():
    """Run the FastAPI server and signal when ready."""
    import socket

    # Quick check if port is available before starting
    def port_ready():
        for _ in range(20):  # Try for up to 2 seconds
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                result = sock.connect_ex(('127.0.0.1', 8000))
                sock.close()
                if result == 0:
                    return True
            except:
                pass
            time.sleep(0.1)
        return False

    # Start uvicorn in a way that we can detect when it's ready
    config = uvicorn.Config(
        fastapi_app,
        host="127.0.0.1",
        port=8000,
        log_level="warning",
        loop="asyncio"
    )
    server = uvicorn.Server(config)

    # Signal ready shortly after server starts
    def signal_ready():
        time.sleep(0.3)  # Brief delay for server to bind
        if port_ready():
            _api_ready.set()
            log.info("API server is ready")
        else:
            # Signal anyway after timeout
            _api_ready.set()
            log.warning("API server may not be fully ready")

    threading.Thread(target=signal_ready, daemon=True).start()
    server.run()


def overlay_text(img, text, y=30):
    cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 4, cv2.LINE_AA)
    cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2, cv2.LINE_AA)


def main():
    startup_time = time.time()

    ensure_dirs()
    cfg = load_json(CONFIG_DIR / "settings.json", default={})
    setup_logging(cfg.get("log_level", "INFO"))

    log.info("GameMotion starting...")

    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--width", type=int, default=cfg.get("frame_width", 1280))
    ap.add_argument("--height", type=int, default=cfg.get("frame_height", 720))
    ap.add_argument("--preview", action="store_true", help="Show camera window")
    ap.add_argument("--complexity", type=int, default=cfg.get("model_complexity", 0))
    ap.add_argument("--train", action="store_true", help="Training mode")
    ap.add_argument("--game", type=str, default=None)
    ap.add_argument("--action", type=str, default=None)
    ap.add_argument("--samples", type=int, default=25)
    ap.add_argument("--no-api", action="store_true", help="Disable local API")
    args = ap.parse_args()

    # === PARALLEL INITIALIZATION ===
    # Start multiple components in parallel for faster startup

    # 1. Start API server in background (non-blocking)
    if not args.no_api:
        api_thread = threading.Thread(target=run_api_server, daemon=True)
        api_thread.start()
        log.info("API server starting in background...")

    # 2. Create pose tracker (lazy loading - doesn't load model yet)
    tracker = PoseTracker(
        complexity=args.complexity,
        min_det=cfg.get("min_detection_confidence", 0.5),
        min_track=cfg.get("min_tracking_confidence", 0.5)
    )

    # 3. Start model warmup in background while we set up other components
    warmup_thread = tracker.warmup()
    log.info("MediaPipe model warming up in background...")

    # 4. Initialize other components (these are fast)
    key_sender = KeySender()
    profman = ProfileManager()

    # Publish to API runtime
    API_RUNTIME["key_sender"] = key_sender
    API_RUNTIME["profile_manager"] = profman

    # 5. Open camera (can take a moment)
    log.info(f"Opening camera {args.camera}...")
    if IS_WINDOWS:
        cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    elif IS_MAC:
        cap = cv2.VideoCapture(args.camera, cv2.CAP_AVFOUNDATION)
    else:
        cap = cv2.VideoCapture(args.camera)  # Default backend for Linux

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not cap.isOpened():
        log.error("Camera not available")
        return

    log.info(f"Camera opened: {args.width}x{args.height}")

    # 6. Wait for API server to be ready (with timeout)
    if not args.no_api:
        if _api_ready.wait(timeout=5.0):
            log.info("API server confirmed ready")
        else:
            log.warning("API server startup timeout - continuing anyway")

    # 7. Wait for model warmup to complete (if not done yet)
    warmup_thread.join(timeout=10.0)

    startup_elapsed = time.time() - startup_time
    log.info(f"Startup complete in {startup_elapsed:.2f}s")

    # === MAIN LOOP SETUP ===
    offline_threshold = float(cfg.get("offline_threshold", 0.82))
    action_cooldown = float(cfg.get("action_cooldown_sec", 1.0))
    frames_confirm = int(cfg.get("frames_confirm", 4))

    recognizer = None
    adb = ActionDB()
    feat_history = deque(maxlen=5)
    stable_label = None
    stable_count = 0
    last_action_time = 0.0
    last_conf = 0.0

    # exe/profile tracking
    active_exe = None

    def update_active_profile():
        nonlocal active_exe, recognizer
        while True:
            exe, _ = get_foreground_exe()
            if args.game:
                exe = args.game
            if exe and exe != active_exe:
                active_exe = exe
                recognizer = ActionRecognizer(exe, offline_threshold=offline_threshold)
                _ = adb._load_all(exe)  # ensure index
                prof = profman.get_profile_for_exe(exe)
                API_RUNTIME["active_exe"] = exe
                API_RUNTIME["active_profile"] = prof
                log.info(f"Active exe: {exe} | profile: {prof.get('display_name') if prof else 'None'}")
            time.sleep(1.0)

    threading.Thread(target=update_active_profile, daemon=True).start()

    # training request watcher (from API)
    def check_train_request():
        tr = API_RUNTIME.get("train_request")
        if tr:
            API_RUNTIME["train_request"] = None
            return tr
        return None

    # === MAIN LOOP ===
    log.info("Starting main detection loop...")
    frame_i = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = tracker.process(frame)
        label_to_fire = None

        if results.pose_landmarks is not None:
            landmarks = tracker.to_landmark_array(results)
            feats = extract_angle_signature(landmarks)
            feat_history.append(feats)

            # live classification
            if recognizer:
                best_label, best_score, second_best = recognizer.classify_offline(feats)
                last_conf = float(best_score)
                # stability filter
                if best_label == stable_label:
                    stable_count = min(stable_count + 1, 1000)
                else:
                    stable_label = best_label
                    stable_count = 1

                # fire?
                now = time.time()
                API_RUNTIME["cooldown_left"] = max(0.0, action_cooldown - (now - last_action_time))
                if (API_RUNTIME.get("detect_enabled", True) and
                    best_label and
                    stable_count >= frames_confirm and
                    (now - last_action_time) >= action_cooldown):
                    label_to_fire = best_label

        # publish telemetry every frame
        API_RUNTIME["stable"] = stable_count
        API_RUNTIME["last_conf"] = float(last_conf)

        # make preview JPEG for the frontend (every 2nd frame)
        if results is not None:
            PoseTracker.draw(frame, results)
        if frame_i % 2 == 0:
            ok, jpeg = cv2.imencode(".jpg", frame)
            if ok:
                API_RUNTIME["latest_jpeg"] = jpeg.tobytes()
        frame_i += 1

        # fire mapping if any
        if label_to_fire and active_exe:
            prof = profman.get_profile_for_exe(active_exe)
            if prof:
                mapping = prof.get("actions", {}).get(label_to_fire)
                if mapping:
                    log.info(f"Firing action '{label_to_fire}'")
                    key_sender.run_macro(mapping)
                    last_action_time = time.time()
                    stable_count = 0  # reset after action

        # handle queued training request (from /train/start)
        tr = check_train_request()
        if tr:
            game = tr["game"]
            action = tr["action"]
            samples = int(tr["samples"])
            save_dir = (pathlib.Path(__file__).resolve().parent.parent / "data" / game / action)
            save_dir.mkdir(parents=True, exist_ok=True)
            log.info(f"Training mode: game={game} action={action} samples={samples}")
            collected = 0
            feat_history.clear()
            while collected < samples:
                ret2, frm = cap.read()
                if not ret2:
                    break
                res2 = tracker.process(frm)
                if res2.pose_landmarks is None:
                    continue
                lm2 = tracker.to_landmark_array(res2)
                f2 = extract_angle_signature(lm2)
                feat_history.append(f2)
                if len(feat_history) == feat_history.maxlen:
                    ts = int(time.time()*1000)
                    cv2.imwrite(str(save_dir / f"{ts}.jpg"), frm)
                    adb.add_sample(game, action, f2, str(save_dir / f"{ts}.jpg"), lm2)
                    collected += 1
                    log.info(f"Captured sample {collected}/{samples}")
                    feat_history.clear()
            log.info("Done collecting samples.")

        # preview window (optional)
        if args.preview:
            overlay_text(frame, f"exe: {API_RUNTIME.get('active_exe') or 'n/a'}", y=30)
            overlay_text(frame, f"conf: {API_RUNTIME.get('last_conf',0):.3f} stab:{API_RUNTIME.get('stable',0)}/10", y=60)
            cv2.imshow("GameMotion Backend - Preview", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q'), ord('Q')):
                break

    cap.release()
    tracker.close()
    cv2.destroyAllWindows()
    log.info("GameMotion stopped")


if __name__ == "__main__":
    main()
