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
        /* ─── FONTS ─────────────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');

        /* ─── CSS VARIABLES ──────────────────────────────────────── */
        :root {
            --cyan:      #00f2ff;
            --cyan-dim:  rgba(0, 242, 255, 0.15);
            --cyan-glow: rgba(0, 242, 255, 0.45);
            --blue:      #0047ff;
            --blue-dim:  rgba(0, 71, 255, 0.12);
            --red:       #ff003c;
            --bg:        #010407;
            --bg2:       #040d14;
            --border:    rgba(0, 242, 255, 0.25);
            --text:      #a8d8e8;
            --text-dim:  rgba(168, 216, 232, 0.5);
            --mono:      'Share Tech Mono', monospace;
            --display:   'Orbitron', monospace;
        }

        /* ─── GLOBAL RESET ───────────────────────────────────────── */
        html, body, [class*="css"] {
            background-color: var(--bg) !important;
            color: var(--text) !important;
            font-family: var(--mono) !important;
        }

        /* ─── ANIMATED GRID BACKGROUND ──────────────────────────── */
        .main::before {
            content: '';
            position: fixed;
            inset: 0;
            background-image:
                linear-gradient(rgba(0,242,255,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,242,255,0.03) 1px, transparent 1px);
            background-size: 40px 40px;
            pointer-events: none;
            z-index: 0;
            animation: gridDrift 60s linear infinite;
        }

        @keyframes gridDrift {
            0%   { background-position: 0 0; }
            100% { background-position: 40px 40px; }
        }

        /* ─── SCANLINES OVERLAY ──────────────────────────────────── */
        .main::after {
            content: '';
            position: fixed;
            inset: 0;
            background: repeating-linear-gradient(
                0deg,
                transparent,
                transparent 2px,
                rgba(0,0,0,0.18) 2px,
                rgba(0,0,0,0.18) 4px
            );
            pointer-events: none;
            z-index: 1;
        }

        /* ─── MAIN CONTENT AREA ──────────────────────────────────── */
        .main {
            background-color: var(--bg) !important;
            position: relative;
        }

        section[data-testid="stMain"] > div {
            padding-top: 1.5rem !important;
        }

        /* ─── PAGE TITLE ─────────────────────────────────────────── */
        h1 {
            font-family: var(--display) !important;
            color: var(--cyan) !important;
            font-size: clamp(1.4rem, 4vw, 2.2rem) !important;
            font-weight: 900 !important;
            letter-spacing: 6px !important;
            text-transform: uppercase !important;
            text-shadow:
                0 0 8px var(--cyan),
                0 0 24px var(--cyan-glow),
                0 0 60px rgba(0,242,255,0.2) !important;
            border-bottom: 1px solid var(--border) !important;
            padding-bottom: 0.6rem !important;
            margin-bottom: 1.2rem !important;
            position: relative;
        }

        h1::after {
            content: '_';
            animation: blink 1.1s step-end infinite;
            color: var(--cyan);
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0; }
        }

        h2, h3 {
            font-family: var(--display) !important;
            color: var(--cyan) !important;
            letter-spacing: 3px !important;
            font-size: 0.95rem !important;
            text-transform: uppercase !important;
            text-shadow: 0 0 10px var(--cyan-glow) !important;
        }

        /* ─── SIDEBAR ────────────────────────────────────────────── */
        [data-testid="stSidebar"] {
            background: var(--bg2) !important;
            border-right: 1px solid var(--border) !important;
            box-shadow: 4px 0 30px rgba(0,242,255,0.08) !important;
            position: relative;
        }

        [data-testid="stSidebar"]::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--cyan), transparent);
            animation: scanH 3s ease-in-out infinite;
        }

        @keyframes scanH {
            0%   { opacity: 0.3; }
            50%  { opacity: 1; }
            100% { opacity: 0.3; }
        }

        [data-testid="stSidebar"] h1 {
            font-size: 1.1rem !important;
            letter-spacing: 8px !important;
        }

        /* ─── INPUTS & TEXTAREAS ─────────────────────────────────── */
        .stTextInput > label,
        .stTextArea > label {
            font-family: var(--mono) !important;
            color: var(--text-dim) !important;
            font-size: 0.72rem !important;
            letter-spacing: 2px !important;
            text-transform: uppercase !important;
        }

        .stTextInput input,
        .stTextArea textarea {
            background: var(--blue-dim) !important;
            border: 1px solid var(--border) !important;
            border-radius: 0 !important;
            color: var(--cyan) !important;
            font-family: var(--mono) !important;
            font-size: 0.85rem !important;
            caret-color: var(--cyan) !important;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: var(--cyan) !important;
            box-shadow: 0 0 12px var(--cyan-glow), inset 0 0 8px rgba(0,242,255,0.05) !important;
            outline: none !important;
        }

        /* ─── STATUS ALERTS ──────────────────────────────────────── */
        /* Warning — analyzing */
        div[data-testid="stAlert"][class*="stWarning"],
        .stAlert > div[class*="warning"] {
            background: rgba(255, 160, 0, 0.08) !important;
            border: 1px solid rgba(255, 160, 0, 0.45) !important;
            border-radius: 0 !important;
            color: #ffa000 !important;
            font-family: var(--mono) !important;
            font-size: 0.78rem !important;
            letter-spacing: 1.5px !important;
            box-shadow: 0 0 14px rgba(255,160,0,0.2) !important;
            animation: pulse-warn 1.4s ease-in-out infinite;
        }

        @keyframes pulse-warn {
            0%, 100% { box-shadow: 0 0 14px rgba(255,160,0,0.2); }
            50%       { box-shadow: 0 0 28px rgba(255,160,0,0.45); }
        }

        /* Success — locked */
        div[data-testid="stAlert"][class*="stSuccess"],
        .stAlert > div[class*="success"] {
            background: rgba(0, 255, 136, 0.06) !important;
            border: 1px solid rgba(0, 255, 136, 0.35) !important;
            border-radius: 0 !important;
            color: #00ff88 !important;
            font-family: var(--mono) !important;
            font-size: 0.78rem !important;
            letter-spacing: 1.5px !important;
            box-shadow: 0 0 14px rgba(0,255,136,0.15) !important;
        }

        /* ─── PHRASE CARD ─────────────────────────────────────────── */
        .phrase-card {
            font-family: var(--mono) !important;
            color: var(--cyan) !important;
            font-size: 0.82rem !important;
            line-height: 1.7 !important;
            background: var(--cyan-dim) !important;
            border-left: 3px solid var(--cyan) !important;
            border-bottom: 1px solid var(--border) !important;
            padding: 10px 14px !important;
            margin: 10px 0 !important;
            box-shadow:
                inset 2px 0 12px rgba(0,242,255,0.07),
                0 0 18px rgba(0,242,255,0.08) !important;
            position: relative;
            overflow: hidden;
        }

        .phrase-card::before {
            content: '>> ';
            color: rgba(0,242,255,0.45);
        }

        /* ─── WEBRTC / VIDEO CONTAINER ───────────────────────────── */
        div[data-testid="stVideo"],
        .stVideo,
        video {
            border: 1px solid var(--border) !important;
            box-shadow:
                0 0 0 1px rgba(0,242,255,0.08),
                0 0 40px rgba(0,242,255,0.12),
                inset 0 0 20px rgba(0,0,0,0.6) !important;
            background: #000 !important;
        }

        /* Target the webrtc streamer wrapper */
        .element-container:has(video),
        .element-container:has(iframe) {
            border: 1px solid var(--border) !important;
            box-shadow: 0 0 30px rgba(0,242,255,0.1) !important;
            background: #000 !important;
        }

        /* ─── BUTTONS ────────────────────────────────────────────── */
        .stButton > button {
            background: transparent !important;
            border: 1px solid var(--cyan) !important;
            border-radius: 0 !important;
            color: var(--cyan) !important;
            font-family: var(--display) !important;
            font-size: 0.72rem !important;
            letter-spacing: 3px !important;
            text-transform: uppercase !important;
            transition: all 0.2s ease;
            box-shadow: 0 0 10px rgba(0,242,255,0.15) !important;
        }

        .stButton > button:hover {
            background: var(--cyan-dim) !important;
            box-shadow: 0 0 24px var(--cyan-glow) !important;
            transform: translateY(-1px);
        }

        /* ─── SCROLLBAR ──────────────────────────────────────────── */
        ::-webkit-scrollbar { width: 4px; background: var(--bg); }
        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 0;
        }
        ::-webkit-scrollbar-thumb:hover { background: var(--cyan); }

        /* ─── DIVIDER / HR ───────────────────────────────────────── */
        hr {
            border-color: var(--border) !important;
            margin: 0.8rem 0 !important;
        }

        /* ─── TOP CORNER DECORATION ──────────────────────────────── */
        .corner-decor {
            position: fixed;
            top: 14px;
            right: 18px;
            font-family: var(--mono);
            font-size: 0.65rem;
            color: var(--text-dim);
            letter-spacing: 2px;
            z-index: 9999;
            pointer-events: none;
        }

        .corner-decor .dot {
            display: inline-block;
            width: 6px; height: 6px;
            border-radius: 50%;
            background: var(--cyan);
            box-shadow: 0 0 8px var(--cyan);
            animation: pulse-dot 1.8s ease-in-out infinite;
            vertical-align: middle;
            margin-right: 6px;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 0.4; transform: scale(0.8); }
            50%       { opacity: 1;   transform: scale(1.2); }
        }

        /* ─── METRIC STRIP ───────────────────────────────────────── */
        .metric-strip {
            display: flex;
            gap: 12px;
            margin: 0 0 14px 0;
            flex-wrap: wrap;
        }

        .metric-chip {
            font-family: var(--mono);
            font-size: 0.68rem;
            color: var(--text-dim);
            border: 1px solid var(--border);
            padding: 4px 10px;
            letter-spacing: 1.5px;
            background: var(--blue-dim);
        }

        .metric-chip span {
            color: var(--cyan);
            font-weight: bold;
        }

        /* ─── SECTION LABELS ─────────────────────────────────────── */
        .sys-label {
            font-family: var(--display);
            font-size: 0.6rem;
            color: var(--text-dim);
            letter-spacing: 4px;
            text-transform: uppercase;
            border-bottom: 1px solid var(--border);
            padding-bottom: 4px;
            margin-bottom: 10px;
        }

        /* ─── HIDE STREAMLIT CHROME ──────────────────────────────── */
        #MainMenu, footer, header { visibility: hidden !important; }

        /* ─── EXPANDER ───────────────────────────────────────────── */
        details {
            background: var(--blue-dim) !important;
            border: 1px solid var(--border) !important;
            border-radius: 0 !important;
        }

        details summary {
            font-family: var(--mono) !important;
            color: var(--cyan) !important;
            font-size: 0.8rem !important;
            letter-spacing: 2px !important;
        }

        /* ─── GENERAL ELEMENT CONTAINERS ────────────────────────── */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--border) !important;
            background: rgba(4,13,20,0.7) !important;
            box-shadow: 0 0 20px rgba(0,242,255,0.05) !important;
        }

        </style>

        <!-- Live clock + corner decor -->
        <div class="corner-decor">
            <span class="dot"></span>
            <span id="nomad-clock"></span>
        </div>
        <script>
            function nomadTick() {
                const el = document.getElementById('nomad-clock');
                if (el) {
                    const now = new Date();
                    const t = now.toTimeString().split(' ')[0];
                    el.textContent = 'SYS:' + t;
                }
                setTimeout(nomadTick, 1000);
            }
            nomadTick();
        </script>
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
        pil_copy = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).copy()
        hud.trigger_scan(pil_copy)
        
    # 3. Render AR Overlay
    processed_img = render_ar(img, hud)
    
    return av.VideoFrame.from_ndarray(processed_img, format="bgr24")

# ── Page Header ────────────────────────────────────────────────────────────
st.title("NOMAD // CORE")

st.markdown("""
    <div class="metric-strip">
        <div class="metric-chip">MODE <span>AR-SCAN</span></div>
        <div class="metric-chip">NET <span>ONLINE</span></div>
        <div class="metric-chip">ENGINE <span>LLAMA-4</span></div>
    </div>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("SYSTEM")

    st.markdown("<div class='sys-label'>// CONFIG</div>", unsafe_allow_html=True)
    hud.lang = st.text_input("Language", "Tamil")
    hud.allergies = st.text_area("Allergies", "Menthol")

    st.markdown("<div class='sys-label' style='margin-top:18px'>// STATUS</div>", unsafe_allow_html=True)

    if hud.is_analyzing:
        st.warning("⚡ ANALYZING PAYLOAD...")
    elif hud.current_data:
        st.success(f"LOCKED: {hud.current_data.get('eng_name')}")
        st.markdown(
            f"<div class='phrase-card'>{hud.current_data.get('consumer_phrase')}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div class='metric-chip' style='margin-top:6px'>AWAITING TARGET</div>",
            unsafe_allow_html=True
        )

# ── WebRTC Stream ────────────────────────────────────────────────────────────
webrtc_streamer(
    key="nomad_v15_fixed",
    mode=WebRtcMode.SENDRECV,
    video_frame_callback=video_callback,
    async_processing=True,
    media_stream_constraints={
        "video": {
            "width": {"max": 1280},
            "height": {"max": 720},
            "facingMode": "environment",
            "frameRate": {"max": 24}
        },
        "audio": False
    },
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)