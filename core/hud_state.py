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
        """
        Calculates motion in the center of the frame.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        with self._lock:
            if self.prev_gray is None:
                self.prev_gray = gray
                return
                
            diff = cv2.absdiff(self.prev_gray, gray)
            motion = np.sum(cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1])
            self.prev_gray = gray
            
            # This threshold (3500) determines how "still" you must be to scan.
            self.is_stable = motion < 3500
            
            if self.is_stable and self.stable_since == 0:
                self.stable_since = time.time()
            elif not self.is_stable:
                self.stable_since = 0

    def trigger_scan(self, pil_img):
        now = time.time()
        # Cooldown check: Must be stable for >1.5 seconds to scan
        if not self.is_analyzing and now > self.cooldown_until and self.stable_since != 0 and (now - self.stable_since > 1.5):
            print(f"\n[HUD_STATE] Triggering Groq Scan (L4S) for: {self.lang}")
            self.is_analyzing = True
            
            def _task():
                try:
                    # 1. AI Analysis
                    res = self.engine.analyze(pil_img, self.allergies)
                    if "error" in res:
                        print(f"[TASK ERROR] {res['error']}")
                        return

                    # 2. External Translation (French, Spanish, Tamil, etc.)
                    final_res = translate_payload(res, self.lang)
                    
                    with self._lock:
                        self.current_data = final_res
                        # Increased cooldown: 5 seconds of stability before next scan.
                        self.cooldown_until = time.time() + 5
                        print(f"[SUCCESS] NOMAD // HUD Data Updated: {final_res.get('eng_name')}")
                        
                except Exception as e:
                    print(f"[CRITICAL TASK ERROR] {e}")
                finally:
                    # Thread Cleanup
                    self.is_analyzing = False
                    print("[TASK] Thread clear. Ready.\n")
            
            t = threading.Thread(target=_task, daemon=True)
            t.start()

# Singular global state object
hud = HUDState()