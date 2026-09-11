import os
import sys
import subprocess
import time
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# Ensure repository root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure unified server on port 8000 is active
try:
    import urllib.request
    urllib.request.urlopen("http://localhost:8000/health", timeout=1)
except Exception:
    # Start unified backend & React frontend daemon on port 8000
    backend_script = ROOT_DIR / "backend" / "run_backend.py"
    subprocess.Popen([sys.executable, str(backend_script)], cwd=str(ROOT_DIR))
    time.sleep(2)

# Page configuration
st.set_page_config(
    page_title="SatQuery AI - Vision-Language Satellite Assistant",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Full-Bleed CSS: hides all Streamlit chrome and renders the exact original React interface
st.markdown("""
<style>
    /* Remove all Streamlit UI chrome, paddings, toolbars, and margins */
    #MainMenu, header, footer, 
    [data-testid="stToolbar"], 
    [data-testid="stDecoration"], 
    [data-testid="stStatusWidget"],
    [data-testid="stSidebarCollapseButton"], 
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
    }
    
    html, body, .stApp {
        background-color: #0b0f19 !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        overflow: hidden !important;
    }
    
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100vw !important;
        width: 100vw !important;
        height: 100vh !important;
    }
    
    iframe {
        border: none !important;
        width: 100vw !important;
        height: 100vh !important;
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        z-index: 999999 !important;
    }
</style>
""", unsafe_allow_html=True)

# Render the exact original React web interface seamlessly via Streamlit
components.iframe(src="http://localhost:8000", scrolling=True)
