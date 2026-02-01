# gamemotion_backend/pose.py
import cv2
import numpy as np
import logging
import threading

log = logging.getLogger("pose")

_BODY_CONN = [
    # torso
    (11, 12), (11, 23), (12, 24), (23, 24),
    # arms
    (11, 13), (13, 15), (12, 14), (14, 16),
    # legs
    (23, 25), (25, 27), (24, 26), (26, 28),
    # feet (optional; keep if you want)
    (27, 29), (29, 31), (28, 30), (30, 32),
]
_FACE_MAX_IDX = 10  # pose landmark indices 0..10 are head/face (nose/eyes/ears/mouth)


class PoseTracker:
    """
    Lazy-loading pose tracker using MediaPipe BlazePose.

    The MediaPipe model is loaded on first use (first call to process())
    rather than at construction time, which significantly improves startup time.
    """

    def __init__(self, complexity=0, min_det=0.5, min_track=0.5, ignore_face=True):
        self.ignore_face = bool(ignore_face)
        self._complexity = int(complexity)
        self._min_det = float(min_det)
        self._min_track = float(min_track)

        # Lazy-loaded components
        self._mp_pose = None
        self._mp_draw = None
        self._pose = None
        self._spec_lmk = None
        self._spec_con = None

        # Thread safety for lazy initialization
        self._init_lock = threading.Lock()
        self._initialized = False

        log.info(f"PoseTracker created (lazy loading enabled, complexity={complexity})")

    def _ensure_initialized(self):
        """Lazy initialization of MediaPipe - called on first use."""
        if self._initialized:
            return

        with self._init_lock:
            # Double-check after acquiring lock
            if self._initialized:
                return

            log.info("Initializing MediaPipe pose model...")
            import mediapipe as mp

            self._mp_pose = mp.solutions.pose
            self._mp_draw = mp.solutions.drawing_utils

            self._pose = self._mp_pose.Pose(
                model_complexity=self._complexity,
                min_detection_confidence=self._min_det,
                min_tracking_confidence=self._min_track,
                enable_segmentation=False,
                smooth_landmarks=True,
            )

            # drawing specs
            self._spec_lmk = self._mp_draw.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2)
            self._spec_con = self._mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)

            self._initialized = True
            log.info("MediaPipe pose model initialized successfully")

    def warmup(self):
        """
        Pre-initialize the model in a background thread.
        Call this early to reduce latency on first frame processing.
        """
        def _warmup():
            self._ensure_initialized()
            # Process a dummy frame to fully warm up the model
            dummy = np.zeros((480, 640, 3), dtype=np.uint8)
            self.process(dummy)
            log.info("PoseTracker warmup complete")

        thread = threading.Thread(target=_warmup, daemon=True)
        thread.start()
        return thread

    def process(self, frame_bgr):
        """Process a frame and return pose results."""
        self._ensure_initialized()
        # mediapipe expects RGB
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return self._pose.process(rgb)

    def to_landmark_array(self, results):
        """
        Returns np.ndarray shape (33, 3) with normalized coords (x,y,z).
        If ignore_face=True, head indices 0..10 are set to NaN so downstream
        code never uses face landmarks.
        """
        if results is None or results.pose_landmarks is None:
            return None
        lm = results.pose_landmarks.landmark
        arr = np.asarray([[p.x, p.y, p.z] for p in lm], dtype=np.float32)  # normalized
        if self.ignore_face:
            arr[0:_FACE_MAX_IDX + 1, :] = np.nan
        return arr

    @staticmethod
    def draw(frame_bgr, results, ignore_face=True):
        """Draw only body joints & connections (no face dots/lines)."""
        if results is None or results.pose_landmarks is None:
            return
        lm = results.pose_landmarks.landmark
        h, w = frame_bgr.shape[:2]

        # draw connections we care about
        for a, b in _BODY_CONN:
            pa, pb = lm[a], lm[b]
            if any(np.isnan([pa.x, pa.y, pb.x, pb.y])):  # if caller masked face, skip
                continue
            x1, y1 = int(pa.x * w), int(pa.y * h)
            x2, y2 = int(pb.x * w), int(pb.y * h)
            cv2.line(frame_bgr, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # draw only the joints used by body connections (no face points)
        used_idxs = {i for conn in _BODY_CONN for i in conn}
        for i in used_idxs:
            p = lm[i]
            if np.isnan([p.x, p.y]).any():
                continue
            cx, cy = int(p.x * w), int(p.y * h)
            cv2.circle(frame_bgr, (cx, cy), 3, (0, 255, 255), -1)

    def close(self):
        """Release resources."""
        if self._pose is not None:
            self._pose.close()
            self._pose = None
            self._initialized = False
            log.info("PoseTracker closed")
