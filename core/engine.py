import os
import json
import io
import base64
from PIL import Image
from groq import Groq

class NomadEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
            
        self.client = Groq(api_key=self.api_key)
        self.model_id = "meta-llama/llama-4-scout-17b-16e-instruct"

    def analyze(self, pil_img, allergies):
        # Image optimization for token efficiency
        pil_img.thumbnail((640, 640))
        buf = io.BytesIO()
        pil_img.convert("RGB").save(buf, format="JPEG", quality=80)
        base64_image = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # High-precision prompt using XML-style logic and Chain-of-Thought
        prompt = (
            "SYSTEM: YOU ARE AN EXPERT TOXICOLOGIST AND MULTILINGUAL SAFETY ADVISOR.\n"
            f"USER RESTRICTIONS: {allergies}\n\n"
            "TASK: Analyze the provided image with absolute precision.\n"
            "COGNITIVE STEPS:\n"
            "1. IDENTIFY: Determine the product name and brand.\n"
            "2. SCAN: Read the full ingredient list using OCR.\n"
            f"3. CROSS-REFERENCE: Look for direct matches or derivatives of: {allergies}.\n"
            "4. EVALUATE: RED (Dangerous), YELLOW (Unknown/Caution), GREEN (Safe).\n\n"
            "JSON OUTPUT REQUIREMENTS:\n"
            "{\n"
            '  "eng_name": "Product Name",\n'
            '  "safety": "RED/YELLOW/GREEN",\n'
            '  "contents": "Explain WHY. Mention specific ingredients found.",\n'
            '  "request_phrase": "One sentence to ask for this in a local market.",\n'
            '  "box_2d": [100, 100, 900, 900]\n'
            "}"
        )

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                model=self.model_id,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            return {"error": str(e)}