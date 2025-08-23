# gamemotion_backend/features.py
import numpy as np

# --- Pose landmark indices (no face) ---
LS, RS = 11, 12
LE, RE = 13, 14
LW, RW = 15, 16
LH, RH = 23, 24
LK, RK = 25, 26
LA, RA = 27, 28

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1D vectors."""
    a = np.asarray(a, dtype=np.float32).ravel()
    b = np.asarray(b, dtype=np.float32).ravel()
    na = float(np.linalg.norm(a)) + 1e-6
    nb = float(np.linalg.norm(b)) + 1e-6
    return float(np.dot(a, b) / (na * nb))

def _u(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    return v / (n + 1e-6)

def _ang(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at b formed by a-b and c-b (radians)."""
    v1 = a - b
    v2 = c - b
    u1 = _u(v1); u2 = _u(v2)
    d = float(np.clip(np.dot(u1, u2), -1.0, 1.0))
    return np.arccos(d)

def extract_angle_signature(landmarks_xy: np.ndarray) -> np.ndarray:
    """
    Body-only signature (no face): shoulders, elbows, wrists, hips, knees, ankles.
    landmarks_xy: (N,2) or (N,3) array from Pose; only XY used.
    Returns a fixed-length float32 vector.
    """
    lm = np.asarray(landmarks_xy, dtype=np.float32)
    if lm.ndim != 2 or lm.shape[1] < 2:
        raise ValueError("landmarks array must have shape (N, >=2)")
    P = lm[:, :2]

    need = [LS, RS, LE, RE, LW, RW, LH, RH, LK, RK, LA, RA]
    if np.any(~np.isfinite(P[need]).reshape(-1)):
        return np.zeros(12, dtype=np.float32)

    feats = []

    # Elbows
    feats.append(_ang(P[LS], P[LE], P[LW]))
    feats.append(_ang(P[RS], P[RE], P[RW]))

    # Shoulders (arm raise)
    feats.append(_ang(P[LE], P[LS], P[LH]))
    feats.append(_ang(P[RE], P[RS], P[RH]))

    # Knees
    feats.append(_ang(P[LH], P[LK], P[LA]))
    feats.append(_ang(P[RH], P[RK], P[RA]))

    # Hips (torso/leg)
    feats.append(_ang(P[LK], P[LH], P[LS]))
    feats.append(_ang(P[RK], P[RH], P[RS]))

    # Torso relations
    shoulder_vec = _u(P[RS] - P[LS])
    hip_vec      = _u(P[RH] - P[LH])
    feats.append(np.arccos(float(np.clip(np.dot(shoulder_vec, hip_vec), -1, 1))))

    vertical = np.array([0.0, -1.0], dtype=np.float32)
    feats.append(np.arccos(float(np.clip(np.dot(shoulder_vec, vertical), -1, 1))))
    feats.append(np.arccos(float(np.clip(np.dot(hip_vec, vertical), -1, 1))))

    # Cross-arm relation
    upper_left  = _u(P[LS] - P[LE])
    upper_right = _u(P[RS] - P[RE])
    feats.append(np.arccos(float(np.clip(np.dot(upper_left, upper_right), -1, 1))))

    return np.asarray(feats, dtype=np.float32)
