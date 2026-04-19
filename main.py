import streamlit as st
import av, cv2, os
from PIL import Image
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from core.engine import NomadEngine
from core.hud_state import hud
from core.vision import render_ar
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="NOMAD HUD v8.5", layout="wide")

if "engine" not in st.session_state:
    st.session_state.engine = NomadEngine()

def video_callback(frame):
    
    img = frame.to_ndarray(format="bgr24")
    hud.update_stability(img)
    if hud.is_stable and not hud.is_analyzing:
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        hud.trigger_scan(pil)
    img = render_ar(img, hud)
    return av.VideoFrame.from_ndarray(img, format="bgr24")

st.title("NOMAD // OPTICAL SAFETY SYSTEM")
hud.engine = st.session_state.engine
hud.lang = st.sidebar.text_input("Local Language", "Tamil")
hud.allergies = st.sidebar.text_area("Dietary Restrictions / Allergies", "Menthol, Peanuts")

webrtc_streamer(key="nomad", mode=WebRtcMode.SENDRECV, video_frame_callback=video_callback, async_processing=True)