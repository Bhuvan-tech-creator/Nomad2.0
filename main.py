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
    hud.update_stability(img)
    
    if hud.is_stable and not hud.is_analyzing:
        pil_copy = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).copy()
        hud.trigger_scan(pil_copy)
        
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

# Public STUN servers. If this fails, the issue is your network's NAT.
# There is no "code fix" for a blocked UDP port other than using TURN.
RTC_CONFIGURATION = {
    "iceServers": [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {"urls": ["stun:stun1.l.google.com:19302"]},
        {"urls": ["stun:stun2.l.google.com:19302"]},
        {"urls": ["stun:stun3.l.google.com:19302"]},
        {"urls": ["stun:stun4.l.google.com:19302"]},
    ]
}

webrtc_streamer(
    key="nomad_v15_no_twilio",
    mode=WebRtcMode.SENDRECV,
    video_frame_callback=video_callback,
    async_processing=True,
    media_stream_constraints={
        "video": {
            "width": {"max": 640}, # Lower resolution for better stability without TURN
            "height": {"max": 480},
            "facingMode": "environment",
            "frameRate": {"max": 20} 
        },
        "audio": False
    },
    rtc_configuration=RTC_CONFIGURATION,
    sendback_audio=False,
)