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

def get_dynamic_font(lang, size):
    path = f"font_{str(lang).lower().strip()}.ttf"
    if os.path.exists(path):
        try: return ImageFont.truetype(path, size)
        except: pass
    return ImageFont.load_default()

def render_ar(img, state):
    h, w = img.shape[:2]
    cx, cy = w//2, h//2
    
    # Scale for mobile (Target box)
    box_s = 0.55 if w < 600 else 0.4
    xmin, ymin = int(cx - (w*box_s//2)), int(cy - (h*box_s//2))
    xmax, ymax = int(cx + (w*box_s//2)), int(cy + (h*box_s//2))
    
    # Quick Reticle (OpenCV - Fast)
    ret_col = (0, 242, 255) if state.is_stable else (0, 0, 255)
    cv2.circle(img, (cx, cy), 15, ret_col, 1)

    # If no data and not analyzing, stay in low-power OpenCV mode
    if not state.is_analyzing and not state.current_data:
        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), ret_col, 1)
        return img

    # Enter High-Detail PIL Mode
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    f_h = get_dynamic_font(state.lang, 20)
    f_b = get_dynamic_font(state.lang, 16)

    if state.is_analyzing:
        draw.rectangle([xmin, ymin, xmax, ymax], outline=(255, 165, 0), width=2)
        draw.text((xmin+10, ymin+10), "SCANNING...", font=f_h, fill=(255, 165, 0))
    elif state.current_data:
        d = state.current_data
        safe = str(d.get("safety", "YELLOW")).upper()
        rgb = (0, 255, 0) if "GREEN" in safe else (255, 0, 0) if "RED" in safe else (255, 165, 0)
        
        # Draw Boundary
        draw.rectangle([xmin, ymin, xmax, ymax], outline=rgb, width=3)
        
        # Header
        header = f"{d.get('eng_name')} // {d.get('local_name', '')}"
        draw.rectangle([xmin, ymin-30, xmax, ymin], fill=(0,0,0,240))
        draw.text((xmin+5, ymin-25), header.upper(), font=f_h, fill=(255,255,255))
        
        # Info Tray
        w_c = smart_wrap(d.get('contents', ''), draw, f_b, (xmax-xmin)-15)
        w_p = smart_wrap(f"ASK: {d.get('consumer_phrase', '')}", draw, f_b, (xmax-xmin)-15)
        
        tray_h = (len(w_c) + len(w_p)) * 20 + 45
        t_ymin = ymax if (ymax+tray_h < h-10) else (ymin-tray_h-35)
        if t_ymin < 5: t_ymin = 5

        draw.rectangle([xmin, t_ymin, xmax, t_ymin+tray_h], fill=(0,0,0,240), outline=rgb)
        draw.text((xmin+10, t_ymin+5), f"STATUS: {safe}", font=f_h, fill=rgb)
        
        y = t_ymin + 28
        for l in w_c:
            draw.text((xmin+10, y), l, font=f_b, fill=(240,240,240))
            y += 20
        y += 5
        for l in w_p:
            draw.text((xmin+10, y), l, font=f_b, fill=(0, 242, 255))
            y += 20

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)