# gamemotion_backend/ai_assist.py
import os, time, base64, logging
from typing import List, Optional

import cv2
from openai import OpenAI

log = logging.getLogger("ai_assist")


def _jpeg_b64(frame_bgr) -> str:
    # Encode OpenCV BGR -> JPEG -> base64 data uri
    ok, buf = cv2.imencode(".jpg", frame_bgr)
    if not ok:
        raise RuntimeError("cv2.imencode failed")
    b64 = base64.b64encode(buf.tobytes()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


class AIAssist:
    """
    Vision fallback that is invoked sparingly:
      • only when offline score is a near-miss (within trigger_band below threshold)
      • only if enough motion (not idle)
      • obeys cooldown
    """
    def __init__(self, enabled: bool, cooldown_sec: float = 2.5,
                 trigger_band: float = 0.02, min_motion_var: float = 35.0):
        self.enabled = bool(enabled)
        self.cooldown = float(cooldown_sec)
        self.trigger_band = float(trigger_band)
        self.min_motion_var = float(min_motion_var)
        self._last_call = 0.0

        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if (self.enabled and api_key) else None
        if self.enabled and not api_key:
            log.warning("AI Assist enabled but OPENAI_API_KEY not set; AI will be skipped.")

    def _cooldown_ok(self) -> bool:
        return (time.time() - self._last_call) >= self.cooldown

    def maybe_classify(self, frame_bgr, labels: List[str],
                       offline_score: float, offline_threshold: float,
                       motion_var: Optional[float]) -> Optional[str]:
        """
        Returns a label from labels or None.
        Triggers only on near-miss and with motion.
        """
        if not (self.enabled and self.client and labels):
            return None
        if not self._cooldown_ok():
            return None

        # Gate by motion to avoid spamming while idle
        if motion_var is not None and motion_var < self.min_motion_var:
            return None

        # Gate by near-miss band just below the threshold
        if offline_score <= 0:
            return None
        if not (offline_threshold - self.trigger_band <= offline_score < offline_threshold):
            return None

        try:
            log.info(f"AI Assist triggered — sending frame to OpenAI with labels: {labels}")
            data_uri = _jpeg_b64(frame_bgr)

            # Compose messages with text + image_url blocks (required format)
            resp = self.client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a pose classifier. Respond with exactly one label from the list. If none match, reply with NONE."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Valid labels: " + ", ".join(labels) +
                                    ". Return exactly one of these labels. If none match, reply with NONE."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": data_uri}
                            }
                        ]
                    }
                ],
            )

            self._last_call = time.time()
            out = (resp.choices[0].message.content or "").strip()
            # Normalize
            canon = {s.upper(): s for s in labels}
            res = out.upper()
            if res in ("NONE", "NO MATCH"):
                return None
            return canon.get(res, None)

        except Exception as e:
            log.warning(f"AI Assist error: {e}")
            return None
