import threading
import time
import cv2
import numpy as np
from core.translator import translate_payload

class HUDState:
    def __init__(self):
        self.engine = None
        self.lang = "Tamil"
        self.allergies = ""
        self.current_data = None
        self.is_analyzing = False
        self.is_stable = False
        self.stable_since = 0
        self.cooldown_until = 0
        self.prev_gray = None
        self._lock = threading.Lock()

    def update_stability(self, frame):
        small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (15, 15), 0)
        
        with self._lock:
            if self.prev_gray is None:
                self.prev_gray = gray
                return
            diff = cv2.absdiff(self.prev_gray, gray)
            motion = np.sum(cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1])
            self.prev_gray = gray
            self.is_stable = motion < 4000
            if self.is_stable:
                if self.stable_since == 0:
                    self.stable_since = time.time()
            else:
                self.stable_since = 0

    def trigger_scan(self, pil_img):
        now = time.time()
        if self.is_analyzing or now < self.cooldown_until:
            return

        if self.stable_since == 0 or (now - self.stable_since < 1.2):
            return

        def _async_scan(img_to_process):
            self.is_analyzing = True
            self.current_data = None
            try:
                raw_res = self.engine.analyze(img_to_process, self.allergies)
                if raw_res and "error" not in raw_res:
                    final_res = translate_payload(raw_res, self.lang)
                    with self._lock:
                        self.current_data = final_res
                self.cooldown_until = time.time() + 4.0
            except Exception as e:
                print(f"HUD Engine Error: {e}")
            finally:
                self.is_analyzing = False

        thread = threading.Thread(target=_async_scan, args=(pil_img,), daemon=True)
        thread.start()

hud = HUDState()