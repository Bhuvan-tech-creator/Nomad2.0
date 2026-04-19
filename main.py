import streamlit as st
import av, cv2, os
from PIL import Image
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from core.engine import NomadEngine
from core.hud_state import hud
from core.vision import render_ar
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    layout="wide", 
    page_title="NOMAD // CORE", 
    initial_sidebar_state="expanded"
)

def apply_ui_overhaul():
    st.markdown("""
        <style>
        .main { background-color: #010203; }
        [data-testid="stSidebar"] { background: rgba(0,0,0,0.95) !important; border-right: 2px solid #00f2ff; }
        h1 { color: #00f2ff; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 3px; }
        .stAlert { background: rgba(0, 242, 255, 0.1); border: 1px solid #00f2ff; color: #00f2ff; }
        </style>
    """, unsafe_allow_html=True)

apply_ui_overhaul()

if "engine" not in st.session_state:
    st.session_state.engine = NomadEngine()

hud.engine = st.session_state.engine

def video_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    hud.update_stability(img)
    
    if hud.is_stable and not hud.is_analyzing:
        # High-speed buffer copy for threading safety
        pil_copy = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).copy()
        hud.trigger_scan(pil_copy)
        
    processed_img = render_ar(img, hud)
    return av.VideoFrame.from_ndarray(processed_img, format="bgr24")

st.title("NOMAD // CORE")

with st.sidebar:
    st.header("SENSORS")
    hud.lang = st.text_input("Translation Language", "Tamil")
    hud.allergies = st.text_area("Restriction Protocol", "Menthol, Peanuts")
    
    st.markdown("---")
    if hud.is_analyzing:
        st.info("⚡ ANALYZING TARGET...")
    elif hud.current_data:
        st.success(f"LOCKED: {hud.current_data.get('eng_name')}")
        st.code(hud.current_data.get('consumer_phrase'), language=None)

# CLOUD FIX: Robust STUN Configuration for NAT Traversal
webrtc_streamer(
    key="nomad_v16_deploy",
    mode=WebRtcMode.SENDRECV,
    video_frame_callback=video_callback,
    async_processing=True,
    media_stream_constraints={
        "video": {
            "width": {"ideal": 1280},
            "height": {"ideal": 720},
            "facingMode": "environment",
            "frameRate": {"ideal": 24}
        },
        "audio": False
    },
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
            {"urls": ["stun:stun3.l.google.com:19302"]},
            {"urls": ["stun:stun4.l.google.com:19302"]}
        ]
    }
)