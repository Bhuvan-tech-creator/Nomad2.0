import streamlit as st
import av, cv2, os
from PIL import Image
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from core.engine import NomadEngine
from core.hud_state import hud
from core.vision import render_ar
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(layout="wide", page_title="NOMAD HUD", initial_sidebar_state="collapsed")

def apply_mobile_theme():
    st.markdown("""
        <style>
        .main { background-color: #010203; }
        [data-testid="stSidebar"] { background: rgba(0,0,0,0.9) !important; border-right: 1px solid #00f2ff; }
        .st-emotion-cache-1vt4y65 { border: 1px solid #00f2ff; background: rgba(0,242,255,0.05); }
        h1 { color: #00f2ff; font-family: monospace; letter-spacing: 2px; }
        .phrase-card { color: #00f2ff; border-left: 2px solid #00f2ff; padding: 10px; background: rgba(0,242,255,0.1); margin: 10px 0; }
        </style>
    """, unsafe_allow_html=True)

apply_mobile_theme()

if "engine" not in st.session_state:
    st.session_state.engine = NomadEngine()

hud.engine = st.session_state.engine

def video_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    
    # 1. Faster Stability Update
    hud.update_stability(img)
    
    # 2. Non-blocking AI trigger
    if hud.is_stable and not hud.is_analyzing:
        # Pass a COPY of the image to the thread to prevent frame corruption
        pil_copy = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).copy()
        hud.trigger_scan(pil_copy)
        
    # 3. Render AR Overlay
    processed_img = render_ar(img, hud)
    
    return av.VideoFrame.from_ndarray(processed_img, format="bgr24")

st.title("NOMAD // CORE")

with st.sidebar:
    st.title("SYSTEM")
    hud.lang = st.text_input("Language", "Tamil")
    hud.allergies = st.text_area("Allergies", "Menthol")
    
    if hud.is_analyzing:
        st.warning("⚡ ANALYZING PAYLOAD...")
    elif hud.current_data:
        st.success(f"LOCKED: {hud.current_data.get('eng_name')}")
        st.markdown(f"<div class='phrase-card'>{hud.current_data.get('consumer_phrase')}</div>", unsafe_allow_html=True)

# Optimized WebRTC for Mobile Performance
webrtc_streamer(
    key="nomad_v15_fixed",
    mode=WebRtcMode.SENDRECV,
    video_frame_callback=video_callback,
    async_processing=True, # Allows the video to keep playing even if Python is slow
    media_stream_constraints={
        "video": {
            "width": {"max": 1280},
            "height": {"max": 720},
            "facingMode": "environment",
            "frameRate": {"max": 24} # Dropping to 24fps helps stability
        },
        "audio": False
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)