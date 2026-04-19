import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def smart_wrap(text, draw, font, max_width):
    lines = []
    words = text.split(' ')
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        w = draw.textbbox((0, 0), test_line, font=font)[2]
        if w <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    return [l for l in lines if l.strip()]

def get_dynamic_font(language_name, size):
    lang_key = language_name.lower().strip()
    font_file = f"font_{lang_key}.ttf"
    if os.path.exists(font_file):
        try: return ImageFont.truetype(font_file, size)
        except: pass
    if os.path.exists("font_default.ttf"):
        return ImageFont.truetype("font_default.ttf", size)
    return ImageFont.load_default()

def render_ar(img, state):
    h, w = img.shape[:2]
    cx, cy = w//2, h//2
    
    # Static Box (Locked to Center for stability)
    box_s = 0.5
    xmin, ymin = int(cx - (w*box_s//2)), int(cy - (h*box_s//2))
    xmax, ymax = int(cx + (w*box_s//2)), int(cy + (h*box_s//2))
    
    # 1. RETICLE
    ret_col = (0, 255, 255) if state.is_stable else (0, 0, 255) # Cyan if stable, Red if moving
    cv2.circle(img, (cx, cy), 25, ret_col, 2)
    cv2.line(img, (cx-15, cy), (cx+15, cy), ret_col, 1)
    cv2.line(img, (cx, cy-15), (cx, cy+15), ret_col, 1)

    if not state.current_data:
        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), ret_col, 1)
        return img

    d = state.current_data
    safe_str = str(d.get("safety", "YELLOW")).upper()
    rgb = (0, 255, 0) if "GREEN" in safe_str else (255, 0, 0) if "RED" in safe_str else (255, 165, 0)
    
    # Main Boundary Box
    cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (rgb[2], rgb[1], rgb[0]), 3)

    # 2. PIL HUD OVERLAY
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    f_head = get_dynamic_font(state.lang, 24)
    f_body = get_dynamic_font(state.lang, 18)

    # Header Panel
    header_txt = f"{d.get('eng_name')} // {d.get('local_name', '')}"
    draw.rectangle([xmin, ymin-40, xmax, ymin], fill=(0,0,0,200))
    draw.text((xmin+10, ymin-35), header_txt.upper(), font=f_head, fill=(255,255,255))

    # Info Tray
    wrapped = smart_wrap(d.get('contents', ''), draw, f_body, (xmax-xmin)-20)
    tray_h = 50 + (len(wrapped)*24) + 40
    draw.rectangle([xmin, ymax, xmax, ymax+tray_h], fill=(0,0,0,200), outline=rgb)
    
    draw.text((xmin+10, ymax+10), f"STATUS: {safe_str}", font=f_head, fill=rgb)
    curr_y = ymax+40
    for line in wrapped:
        draw.text((xmin+10, curr_y), line, font=f_body, fill=(200,200,200))
        curr_y += 24
    
    draw.text((xmin+10, ymax+tray_h-30), f"PHRASE: {d.get('request_phrase')}", font=f_body, fill=(0, 242, 255))

    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)