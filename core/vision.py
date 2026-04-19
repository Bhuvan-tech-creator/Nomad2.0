import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

def smart_wrap(text, draw, font, max_width):
    lines = []
    words = str(text).split(' ')
    curr = []
    for w in words:
        test = ' '.join(curr + [w])
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            curr.append(w)
        else:
            lines.append(' '.join(curr))
            curr = [w]
    lines.append(' '.join(curr))
    return [l for l in lines if l.strip()]

def get_font(lang, size):
    path = f"font_{str(lang).lower().strip()}.ttf"
    if os.path.exists(path):
        try: return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

def render_ar(img, state):
    h, w = img.shape[:2]
    cx, cy = w//2, h//2
    
    # Scale based on device
    box_s = 0.5 if w < 600 else 0.35
    xmin, ymin = int(cx - (w*box_s//2)), int(cy - (h*box_s//2))
    xmax, ymax = int(cx + (w*box_s//2)), int(cy + (h*box_s//2))
    
    # Tactical Crosshair
    ret_col = (0, 242, 255) if state.is_stable else (0, 0, 255)
    cv2.line(img, (cx-10, cy), (cx+10, cy), ret_col, 1)
    cv2.line(img, (cx, cy-10), (cx, cy+10), ret_col, 1)

    if not state.is_analyzing and not state.current_data:
        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), ret_col, 1)
        return img

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img, "RGBA") # Enable transparency
    f_h = get_font(state.lang, 20)
    f_b = get_font(state.lang, 16)

    if state.is_analyzing:
        draw.rectangle([xmin, ymin, xmax, ymax], outline=(255, 165, 0, 255), width=2)
        draw.text((xmin+10, ymin+10), "PROCESSING...", font=f_h, fill=(255, 165, 0, 255))
    elif state.current_data:
        d = state.current_data
        safe = str(d.get("safety", "YELLOW")).upper()
        rgb = (0, 255, 0, 255) if "GREEN" in safe else (255, 0, 0, 255) if "RED" in safe else (255, 165, 0, 255)
        
        # 1. Main Bounding Box
        draw.rectangle([xmin, ymin, xmax, ymax], outline=rgb, width=3)
        
        # 2. Header Panel
        header = f"{d.get('eng_name')} // {d.get('local_name', '')}"
        draw.rectangle([xmin, ymin-30, xmax, ymin], fill=(0,0,0,240))
        draw.text((xmin+5, ymin-25), header.upper(), font=f_h, fill=(255,255,255,255))
        
        # 3. Floating Info Tray (Bottom-Locked)
        w_c = smart_wrap(d.get('contents', ''), draw, f_b, (xmax-xmin)-20)
        w_p = smart_wrap(f"REQ: {d.get('consumer_phrase', '')}", draw, f_b, (xmax-xmin)-20)
        
        tray_h = (len(w_c) + len(w_p)) * 22 + 50
        # Check for bottom overflow
        t_ymin = ymax if (ymax + tray_h < h-10) else (ymin - tray_h - 40)
        if t_ymin < 5: t_ymin = 5

        # Glass Panel Effect
        draw.rectangle([xmin, t_ymin, xmax, t_ymin+tray_h], fill=(0,0,0,220), outline=rgb)
        draw.text((xmin+10, t_ymin+5), f"STATUS: {safe}", font=f_h, fill=rgb)
        
        y_ptr = t_ymin + 30
        for line in w_c:
            draw.text((xmin+10, y_ptr), line, font=f_b, fill=(230,230,230,255))
            y_ptr += 22
        y_ptr += 5
        for line in w_p:
            draw.text((xmin+10, y_ptr), line, font=f_b, fill=(0, 242, 255, 255))
            y_ptr += 22

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)