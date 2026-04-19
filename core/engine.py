import os, json, io, base64
from PIL import Image
from groq import Groq

class NomadEngine:
    def __init__(self):
        # The key must be in your Streamlit Secrets as GROQ_API_KEY
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("CRITICAL: GROQ_API_KEY missing from environment.")
        self.client = Groq(api_key=self.api_key)
        
        # UPGRADED: Llama 4 Scout is the new standard for fast vision
        self.model_id = "meta-llama/llama-4-scout-17b-16e-instruct"

    def analyze(self, pil_img, allergies):
        # Optimization: Llama 4 Scout handles base64 efficiently up to 4MB
        pil_img.thumbnail((800, 800)) 
        buf = io.BytesIO()
        pil_img.convert("RGB").save(buf, format="JPEG", quality=80)
        base64_image = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # Refined Tactical Prompt for Llama 4
        prompt = (
            f"SYSTEM: TACTICAL SCANNER ACTIVE. USER RESTRICTIONS: {allergies}\n"
            "TASK: Identify the product and determine safety status. Determine safety status based on allergies provided. For the consumer phrase, if you find that this product is not suitable with the restrictions, return the phrase as something like 'Are there any other alternatives to this?'. If there are no allergens, return something like 'I would like to purchase this'.\n"
            "OUTPUT RULES: Return strictly JSON. No markdown. No prose.\n"
            "JSON STRUCTURE:\n"
            "{"
            ' "eng_name": "Product Name", '
            ' "safety": "GREEN/RED/YELLOW", '
            ' "contents": "Short reason for status", '
            ' "consumer_phrase": "One sentence question for a store clerk"'
            "}"
        )

        try:
            completion = self.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }],
                model=self.model_id,
                response_format={"type": "json_object"},
                temperature=0.1 # Low temp for tactical consistency
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            print(f"API ERROR: {e}")
            return {"error": str(e)}