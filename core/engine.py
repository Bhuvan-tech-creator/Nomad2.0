import os, json, io
from PIL import Image
from google import genai
from google.genai import types

class NomadEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("[CRITICAL] API KEY NOT FOUND IN .ENV")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-2.5-flash-lite"

    def analyze(self, pil_img, allergies):
        print("[ENGINE] Resizing image for API...")
        pil_img.thumbnail((640, 640))
        buf = io.BytesIO()
        pil_img.convert("RGB").save(buf, format="JPEG", quality=75)
        
        prompt = (
            f"STRICT SAFETY CHECK. User is ALLERGIC to: {allergies}.\n"
            "OUTPUT LANGUAGE: English only.\n\n"
            "MANDATORY VERIFICATION:\n"
            "1. Identify product ingredients.\n"
            f"2. If ANY match for '{allergies}', output RED.\n"
            "3. Return JSON ONLY: {\"eng_name\": \"...\", \"safety\": \"...\", \"contents\": \"...\", \"request_phrase\": \"...\", \"box_2d\": [ymin, xmin, ymax, xmax]}"
        )

        try:
            print("[ENGINE] Sending request to Gemini...")
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[prompt, types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")],
                config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json")
            )
            print("[ENGINE] API Response received.")
            return json.loads(response.text)
        except Exception as e:
            print(f"[ENGINE ERROR] API Call failed: {e}")
            return {"error": str(e)}