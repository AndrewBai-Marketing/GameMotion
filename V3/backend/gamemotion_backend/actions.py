# backend/gamemotion_backend/actions.py
from __future__ import annotations
import time, logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np

try:
    # use your shared DATA_DIR if present
    from .util import DATA_DIR  # type: ignore
except Exception:
    DATA_DIR = Path(__file__).resolve().parents[1] / "data"

log = logging.getLogger("actions")


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float32).ravel()
    b = b.astype(np.float32).ravel()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


class ActionDB:
    """
    Disk-backed sample store:
      data/<exe>/<action>/*.npz
        - features: np.ndarray (angle signature)
        - landmarks: np.ndarray (optional)
        - image: str (path to jpg captured)
    """

    def __init__(self, base: Optional[Path] = None):
        self.base: Path = Path(base) if base else Path(DATA_DIR)
        self._centroid_cache: Dict[str, Dict[str, np.ndarray]] = {}
        self._centroid_cache_mtime: Dict[str, float] = {}

    # ---- IO ----
    def add_sample(
        self,
        exe_name: str,
        action: str,
        features: np.ndarray,
        image_path: str,
        landmarks: Optional[np.ndarray] = None,
    ) -> None:
        folder = self.base / exe_name / action
        folder.mkdir(parents=True, exist_ok=True)
        ts = int(time.time() * 1000)
        np.savez_compressed(
            folder / f"{ts}.npz",
            features=features.astype(np.float32),
            image=str(image_path),
            landmarks=(landmarks.astype(np.float32) if landmarks is not None else np.zeros((0,), np.float32)),
        )

    def load_all(self, exe_name: str) -> Dict[str, List[np.ndarray]]:
        """
        Public method expected by main.py. Returns:
          { action_label: [features_np_array, ...], ... }
        """
        out: Dict[str, List[np.ndarray]] = {}
        exe_dir = self.base / exe_name
        if not exe_dir.exists():
            return out
        for action_dir in exe_dir.iterdir():
            if not action_dir.is_dir():
                continue
            feats: List[np.ndarray] = []
            for f in action_dir.glob("*.npz"):
                try:
                    with np.load(f, allow_pickle=True) as z:
                        feats.append(z["features"].astype(np.float32))
                except Exception:
                    pass
            if feats:
                out[action_dir.name] = feats
        return out

    # Back-compat: if some code calls _load_all, keep it working
    _load_all = load_all

    def labels_for_game(self, exe_name: str) -> List[str]:
        return list(self.load_all(exe_name).keys())

    # ---- centroids & matching ----
    def _centroids(self, exe_name: str) -> Dict[str, np.ndarray]:
        """Compute or fetch cached centroids per action label."""
        exe_dir = self.base / exe_name
        mtime = exe_dir.stat().st_mtime if exe_dir.exists() else 0.0
        cached = self._centroid_cache.get(exe_name)
        if cached is not None and self._centroid_cache_mtime.get(exe_name) == mtime:
            return cached

        all_feats = self.load_all(exe_name)
        cents: Dict[str, np.ndarray] = {}
        for label, feats in all_feats.items():
            try:
                stack = np.stack(feats, axis=0).astype(np.float32)
                cents[label] = np.mean(stack, axis=0)
            except Exception:
                pass

        self._centroid_cache[exe_name] = cents
        self._centroid_cache_mtime[exe_name] = mtime
        log.info("Built centroid index for %s: %s", exe_name, list(cents.keys()))
        return cents

    def best_match(self, exe_name: str, feats: np.ndarray) -> Tuple[Optional[str], float, float]:
        """
        Returns (best_label, best_score, second_best_score).
        If no centroids available, returns (None, 0.0, 0.0).
        """
        cents = self._centroids(exe_name)
        if not cents:
            return None, 0.0, 0.0

        best_label: Optional[str] = None
        best = -1.0
        second = -1.0
        for lbl, c in cents.items():
            s = _cosine(feats, c)
            if s > best:
                second = best
                best = s
                best_label = lbl
            elif s > second:
                second = s
        return best_label, float(best), float(second)


class ActionRecognizer:
    def __init__(self, exe_name: str, offline_threshold: float = 0.9):
        self.exe_name = exe_name
        self.db = ActionDB()
        self.offline_threshold = float(offline_threshold)

    def classify_offline(self, feats: np.ndarray) -> Tuple[Optional[str], float, float]:
        """
        Returns (label|None, best_score, second_best).
        Applies the offline_threshold only in main.py when deciding to fire.
        """
        label, best, second = self.db.best_match(self.exe_name, feats)
        if label is None:
            return None, 0.0, 0.0
        return label, float(best), float(second)

    def candidate_labels(self) -> List[str]:
        return self.db.labels_for_game(self.exe_name)
