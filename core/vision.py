import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def get_dynamic_font(language_name, size):
    # Standardize name: "Hindi" -> "font_hindi.ttf"
    lang_key = language_name.lower().strip()
    font_file = f"font_{lang_key}.ttf"
    
    if os.path.exists(font_file):
        try:
            return ImageFont.truetype(font_file, size)
        except:
            pass
    
    # Check for a default font or fall back to system
    if os.path.exists("font_default.ttf"):
        return ImageFont.truetype("font_default.ttf", size)
    return ImageFont.load_default()

def render_ar(img, state):
    h, w = img.shape[:2]
    
    # 1. Stability Reticle
    ret_col = (0, 255, 0) if state.is_stable else (0, 0, 255)
    cv2.circle(img, (w//2, h//2), 20, ret_col, 2)

    if not (state.current_data and "box_2d" in state.current_data):
        return img

    d = state.current_data
    b = [int(v * (h if i%2==0 else w) / 1000) for i, v in enumerate(d["box_2d"])]
    ymin, xmin, ymax, xmax = b[0], b[1], b[2], b[3]

    # Safety Color
    safe_str = str(d.get("safety", "YELLOW")).upper()
    rgb = (0, 255, 0) if "GREEN" in safe_str else (255, 0, 0) if "RED" in safe_str else (255, 165, 0)
    cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (rgb[2], rgb[1], rgb[0]), 3)

    # 2. PIL Rendering (The Font Handler)
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # This grabs the specific .ttf for the language you typed in the sidebar
    f_head = get_dynamic_font(state.lang, 24)
    f_body = get_dynamic_font(state.lang, 20)

    # UI Elements
    header_txt = f"{d.get('eng_name')} | {d.get('local_name', '...')}"
    draw.rectangle([xmin, max(0, ymin-40), xmax, ymin], fill=(0,0,0,200))
    draw.text((xmin + 5, ymin - 35), header_txt, font=f_head, fill=(255, 255, 255))

    draw.rectangle([xmin, ymax, xmax, ymax + 120], fill=(0,0,0,200), outline=rgb)
    draw.text((xmin + 10, ymax + 10), f"STATUS: {safe_str}", font=f_head, fill=rgb)
    
    # This is the translated reasoning
    draw.text((xmin + 10, ymax + 45), d.get('contents', ''), font=f_body, fill=(255,255,255))
    draw.text((xmin + 10, ymax + 90), f"REQ: {d.get('request_phrase')}", font=f_body, fill=(0, 255, 255))

    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)