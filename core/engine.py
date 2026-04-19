import os, json, io, base64
from PIL import Image
from groq import Groq

class NomadEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key: raise ValueError("GROQ_API_KEY missing")
        self.client = Groq(api_key=self.api_key)
        self.model_id = "meta-llama/llama-4-scout-17b-16e-instruct"

    def analyze(self, pil_img, allergies):
        pil_img.thumbnail((640, 640))
        buf = io.BytesIO()
        pil_img.convert("RGB").save(buf, format="JPEG", quality=75)
        base64_image = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        prompt = (
            "ACT AS A TACTICAL HUD AI. Analyze image for allergies: " + str(allergies) + "\n"
            "1. Identify product and ingredients in the product.\n"
            "2. Determine Safety: GREEN (Safe), RED (Danger), YELLOW (Caution), this is determined through whether or not the user is allergic to one or more of the ingredients in the product.\n"
            "3. Reasoning: Be extremely concise (max 15 words).\n"
            "4. Phrase: If GREEN: 'Can I please buy this?'. If RED/YELLOW: 'I am allergic to " + str(allergies) + ", are there other options?'\n"
            "JSON ONLY:\n"
            "{\n"
            '  "eng_name": "Name",\n'
            '  "safety": "STATUS",\n'
            '  "contents": "Reasoning",\n'
            '  "consumer_phrase": "Phrase",\n'
            '  "box_2d": [100, 100, 900, 900]\n'
            "}"
        )

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}],
                model=self.model_id,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            return {"error": str(e)}