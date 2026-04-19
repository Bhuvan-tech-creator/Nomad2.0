import streamlit as st
import av, cv2, os
from PIL import Image
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from core.engine import NomadEngine
from core.hud_state import hud
from core.vision import render_ar
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(layout="wide", page_title="NOMAD HUD")

def apply_tactical_theme():
    st.markdown("""
        <style>
        body { background-color: #050a0f; color: #00f2ff; }
        [data-testid="stSidebar"] { background-color: rgba(10, 20, 30, 0.9) !important; border-right: 1px solid #00f2ff; }
        .stTextInput, .stTextArea { background: #000 !important; border: 1px solid #00f2ff !important; color: #00f2ff !important; }
        .st-emotion-cache-1vt4y65 { border: 1px solid #00f2ff; background: rgba(0, 242, 255, 0.05); }
        @keyframes pulse { 0% {opacity: 1;} 50% {opacity: 0.2;} 100% {opacity: 1;} }
        .analyzing { color: #ffaa00; font-family: monospace; animation: pulse 1s infinite; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

apply_tactical_theme()

if "engine" not in st.session_state:
    st.session_state.engine = NomadEngine()

hud.engine = st.session_state.engine

def video_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    hud.update_stability(img)
    if hud.is_stable and not hud.is_analyzing:
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        hud.trigger_scan(pil)
    img = render_ar(img, hud)
    return av.VideoFrame.from_ndarray(img, format="bgr24")

st.title("NOMAD // TACTICAL ANALYSIS HUD")

# Sidebar Config
st.sidebar.title("SYSTEM CONFIG")
hud.lang = st.sidebar.text_input("Active Language", "Tamil")
hud.allergies = st.sidebar.text_area("Restriction List", "Menthol, Peanuts")

st.sidebar.markdown("---")
if hud.is_analyzing:
    st.sidebar.markdown("<p class='analyzing'>SCANNING TARGET...</p>", unsafe_allow_html=True)
elif hud.is_stable:
    st.sidebar.success("LENS STABLE // READY")
else:
    st.sidebar.info("POSITIONING...")

webrtc_streamer(
    key="nomad_tactical",
    mode=WebRtcMode.SENDRECV,
    video_frame_callback=video_callback,
    async_processing=True,
    media_stream_constraints={"video": True, "audio": False}
)