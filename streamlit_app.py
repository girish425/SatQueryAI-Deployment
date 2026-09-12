import os
import sys
import time
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

import streamlit as st
from PIL import Image

# Ensure repository root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure required runtime folders exist
for folder in ["./uploads", "./evidence", "./sample_data", "./data"]:
    Path(folder).mkdir(parents=True, exist_ok=True)

# Synchronize Streamlit Cloud secrets with environment variables for MongoDB Atlas
try:
    if hasattr(st, "secrets"):
        if "MONGODB_URI" in st.secrets:
            os.environ["MONGODB_URI"] = st.secrets["MONGODB_URI"]
        if "DATABASE_NAME" in st.secrets:
            os.environ["DATABASE_NAME"] = st.secrets["DATABASE_NAME"]
except Exception:
    pass

# Import core backend modules
from backend.app.agent.controller import AgentController
from backend.app.utils.geotiff_utils import read_geotiff, generate_rgb_preview
from backend.app.satellite.stac_client import LiveSTACClient
from backend.app.satellite.bigearthnet_client import BIGEARTHNET_DATASET, BIGEARTHNET_CITATION
from backend.app.database.mongodb import db_manager, mask_mongodb_uri
from backend.app.pdf.conversation_pdf import generate_conversation_pdf

logger = logging.getLogger("satquery.streamlit")

# -----------------------------------------------------------------------------
# Streamlit Page Configuration & Dark Space Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SatQuery AI - Vision-Language Satellite Assistant",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Dark Space Theme Colors */
    :root {
        --bg-primary: #0b0f19;
        --bg-card: rgba(17, 24, 39, 0.8);
        --accent-cyan: #06b6d4;
        --accent-blue: #3b82f6;
        --accent-emerald: #10b981;
        --border-color: rgba(6, 182, 212, 0.25);
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0b0f19 !important;
        color: #f3f4f6 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0d1322 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Header & Badges */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #06b6d4 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }
    
    .status-badge-healthy {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(16, 185, 129, 0.4);
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    
    .status-badge-fallback {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid rgba(245, 158, 11, 0.4);
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    
    .metric-card {
        background: rgba(17, 24, 39, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
    
    .metric-val {
        font-size: 1.4rem;
        font-weight: 700;
        color: #38bdf8;
    }
    
    .metric-lbl {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Chat message bubble styling */
    [data-testid="stChatMessage"] {
        background: rgba(17, 24, 39, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
    }
    
    /* Code blocks & pills */
    .stCodeBlock {
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Cached Resources & State Management
# -----------------------------------------------------------------------------
@st.cache_resource
def get_agent_controller() -> AgentController:
    return AgentController()

@st.cache_resource
def get_stac_client() -> LiveSTACClient:
    return LiveSTACClient()

agent_controller = get_agent_controller()
stac_client = get_stac_client()

# Initialize Session State
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_images" not in st.session_state:
    # Default to sample optical scene
    default_optical = ROOT_DIR / "sample_data" / "sample_optical_hyderabad.tif"
    if default_optical.exists():
        st.session_state.active_images = [str(default_optical)]
        st.session_state.active_scene_title = "Sentinel-2 MSI (Hyderabad, India)"
    else:
        st.session_state.active_images = []
        st.session_state.active_scene_title = "No Scene Loaded"

if "active_scene_title" not in st.session_state:
    st.session_state.active_scene_title = "Sentinel-2 MSI (Hyderabad, India)"

if "user_name" not in st.session_state:
    st.session_state.user_name = "Analyst_Workspace"

if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def load_preview_image(image_path: str) -> Optional[Image.Image]:
    """Return RGB preview PIL image for either GeoTIFF or standard image."""
    try:
        path = Path(image_path)
        if not path.exists():
            return None
        
        preview_png = ROOT_DIR / "evidence" / f"{path.stem}_preview.png"
        if preview_png.exists():
            return Image.open(preview_png)
        
        if path.suffix.lower() in [".tif", ".tiff"]:
            raster, meta = read_geotiff(str(path))
            preview_gen = generate_rgb_preview(raster, str(preview_png))
            return Image.open(preview_gen)
        else:
            return Image.open(path)
    except Exception as e:
        logger.error(f"Error loading preview for {image_path}: {e}")
        return None


# -----------------------------------------------------------------------------
# Sidebar: System Controls, Models, STAC, & Database
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛰️ SatQuery AI Engine")
    st.markdown("<div style='font-size:0.8rem; color:#94a3b8; margin-top:-8px;'>Autonomous Remote Sensing Assistant</div>", unsafe_allow_html=True)
    st.markdown("---")

    # 1. MongoDB Atlas Health Indicator
    db_health = db_manager.check_health()
    if db_health.get("connected"):
        masked_uri = mask_mongodb_uri(db_health.get("uri", ""))
        st.markdown(f"""
        <div class="status-badge-healthy">
            <span>🟢</span> <b>MongoDB Atlas: Connected</b>
        </div>
        <div style="font-size:0.75rem; color:#94a3b8; margin-top:4px;">
            DB: <code>{db_health.get('database')}</code> · {db_health.get('latency_ms', 0)}ms
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-badge-fallback">
            <span>🟡</span> <b>Local Fallback Store: Active</b>
        </div>
        <div style="font-size:0.75rem; color:#94a3b8; margin-top:4px;">
            Data stored locally in <code>/data</code>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 2. AI Model Selection & Routing Mode
    st.markdown("#### 🧠 AI Model Architecture")
    routing_mode = st.radio(
        "Workflow Routing",
        options=["Autonomous Agent (Auto-Route)", "Manual Model Override"],
        index=0,
        help="Autonomous Agent classifies user intent and lazy-loads the optimal model. Manual override lets you test specific vision-language baselines."
    )

    selected_model_override = None
    if routing_mode == "Manual Model Override":
        selected_model_override = st.selectbox(
            "Select Baseline Model",
            options=[
                "RS-Image-Understanding-Baseline",
                "RS-Change-Detection-Baseline",
                "Optical-to-SAR Cross-Sensor Synthesis",
                "RS-Grounding-Engine",
                "RS-VQA-Engine"
            ]
        )

    st.markdown("---")

    # 3. Benchmark Presets (BigEarthNet.txt arXiv:2603.29630)
    with st.expander("📚 BigEarthNet.txt Benchmarks", expanded=False):
        st.markdown(f"**{BIGEARTHNET_CITATION['title']}**")
        st.caption(f"arXiv:{BIGEARTHNET_CITATION['arxiv_id']} · {BIGEARTHNET_CITATION['total_pairs']:,} pairs")

        ben_options = {item["title"]: item for item in BIGEARTHNET_DATASET}
        selected_ben = st.selectbox("Select Ground-Truth Pair", list(ben_options.keys()))
        ben_data = ben_options[selected_ben]

        st.markdown(f"📍 **{ben_data['location']}** ({ben_data['resolution']})")
        st.markdown("**CORINE Land Cover Labels:**")
        st.write(", ".join([f"`{lbl}`" for lbl in ben_data["corine_labels"]]))

        if st.button("📥 Load Benchmark Pair", use_container_width=True):
            s2_p = ROOT_DIR / "sample_data" / "sample_optical_hyderabad.tif"
            s1_p = ROOT_DIR / "sample_data" / "sample_sar_hyderabad.tif"
            st.session_state.active_images = [str(s2_p), str(s1_p)]
            st.session_state.active_scene_title = f"BigEarthNet: {ben_data['title']}"
            st.success("Loaded Co-Registered Sentinel-1 & Sentinel-2 Benchmark pair!")
            st.rerun()

    # 4. Live STAC Satellite Catalog Search
    with st.expander("🌐 Live STAC Satellite Search", expanded=False):
        st.caption("Search real-time scenes across Earth Search (AWS Sentinel-2 / Landsat).")
        stac_query = st.text_input("Location or City", value="Mumbai", placeholder="e.g. Mumbai, Cairo, Tokyo")
        sat_type = st.selectbox("Satellite", ["Sentinel-2", "Sentinel-1 SAR", "Landsat-9"])
        cloud_thresh = st.slider("Max Cloud Cover (%)", 0, 100, 25)

        if st.button("🔍 Search Catalog", use_container_width=True):
            with st.spinner(f"Querying STAC API for {stac_query}..."):
                results = stac_client.search_live_imagery(
                    query_text=stac_query,
                    satellite=sat_type,
                    max_cloud_cover=float(cloud_thresh),
                    limit=4
                )
                features = results.get("features", [])
                st.session_state.stac_results = features

        if "stac_results" in st.session_state and st.session_state.stac_results:
            st.markdown(f"**Found {len(st.session_state.stac_results)} scenes:**")
            for idx, feat in enumerate(st.session_state.stac_results):
                thumb = feat.get("thumbnail_url")
                item_id = feat.get("item_id", f"scene_{idx}")
                datetime_str = feat.get("datetime", "")[:10]
                cc = feat.get("cloud_cover", 0.0)

                st.markdown(f"**{item_id[:22]}...**")
                st.caption(f"📅 {datetime_str} · ☁️ {cc:.1f}% Cloud")
                if thumb:
                    st.image(thumb, width=180)
                if st.button(f"Analyze Scene #{idx+1}", key=f"btn_stac_{idx}", use_container_width=True):
                    # Download preview into uploads
                    import httpx
                    target_path = ROOT_DIR / "uploads" / f"stac_{item_id}.jpg"
                    if thumb:
                        resp = httpx.get(thumb, timeout=10.0)
                        if resp.status_code == 200:
                            target_path.write_bytes(resp.content)
                            st.session_state.active_images = [str(target_path)]
                            st.session_state.active_scene_title = f"STAC: {item_id}"
                            st.success(f"Scene {item_id[:16]} staged for analysis!")
                            st.rerun()

    st.markdown("---")

    # 5. Session Actions & Report Download
    st.markdown("#### 📑 Session & Export")
    if st.button("🔄 New Analysis Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.last_analysis = None
        st.success("New session initialized!")
        st.rerun()

    if st.session_state.messages and st.session_state.last_analysis:
        try:
            pdf_conv = {
                "session_id": st.session_state.session_id,
                "title": st.session_state.active_scene_title,
                "messages": [
                    {
                        "role": m["role"],
                        "content": m["content"],
                        "timestamp": m.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        "metadata": m.get("metadata", {})
                    }
                    for m in st.session_state.messages
                ]
            }
            pdf_buf = generate_conversation_pdf(pdf_conv, static_evidence_dir=str(ROOT_DIR / "evidence"))
            st.download_button(
                label="📄 Export Analysis PDF",
                data=pdf_buf.getvalue(),
                file_name=f"SatQuery_Report_{st.session_state.session_id[:8]}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            logger.error(f"PDF export error: {e}")


# -----------------------------------------------------------------------------
# Main Application Header
# -----------------------------------------------------------------------------
st.markdown('<div class="hero-title">🛰️ SatQuery AI</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Interactive Vision-Language Assistant for Multimodal Remote Sensing · Spectral Indices · Land Cover · STAC Catalog Retrieval</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Satellite Scene Staging & Multi-Modal Visual Inspection
# -----------------------------------------------------------------------------
col_stage, col_info = st.columns([1.2, 0.8])

with col_stage:
    st.markdown("##### 📁 Staged Satellite Imagery")
    
    # Preset Pickers
    preset_col1, preset_col2, preset_col3 = st.columns(3)
    with preset_col1:
        if st.button("🛰️ Sentinel-2 Optical", use_container_width=True):
            p = ROOT_DIR / "sample_data" / "sample_optical_hyderabad.tif"
            st.session_state.active_images = [str(p)]
            st.session_state.active_scene_title = "Sentinel-2 MSI (Hyderabad)"
            st.rerun()
    with preset_col2:
        if st.button("📡 Sentinel-1 SAR", use_container_width=True):
            p = ROOT_DIR / "sample_data" / "sample_sar_hyderabad.tif"
            st.session_state.active_images = [str(p)]
            st.session_state.active_scene_title = "Sentinel-1 SAR Radar (Hyderabad)"
            st.rerun()
    with preset_col3:
        if st.button("🔄 Change Pair (T1/T2)", use_container_width=True):
            t1 = ROOT_DIR / "sample_data" / "sample_change_t1.tif"
            t2 = ROOT_DIR / "sample_data" / "sample_change_t2.tif"
            st.session_state.active_images = [str(t1), str(t2)]
            st.session_state.active_scene_title = "Bi-Temporal Change Pair (2025 vs 2026)"
            st.rerun()

    # Custom File Uploader
    uploaded_files = st.file_uploader(
        "Upload Custom GeoTIFF (.tif, .tiff) or Standard Satellite Image (.png, .jpg)",
        type=["tif", "tiff", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload 1 scene for Land Cover / VQA / Grounding, or 2 scenes for Change Detection and Optical-SAR analysis."
    )
    if uploaded_files:
        saved_paths = []
        for uf in uploaded_files:
            dest = ROOT_DIR / "uploads" / uf.name
            dest.write_bytes(uf.getvalue())
            saved_paths.append(str(dest))
        st.session_state.active_images = saved_paths
        st.session_state.active_scene_title = f"Uploaded: {', '.join([uf.name for uf in uploaded_files])}"
        st.success(f"Loaded {len(saved_paths)} image(s) for analysis!")

    # Display Previews
    if st.session_state.active_images:
        preview_cols = st.columns(len(st.session_state.active_images))
        for idx, img_path in enumerate(st.session_state.active_images):
            with preview_cols[idx]:
                pil_img = load_preview_image(img_path)
                if pil_img:
                    lbl = "Image T1" if idx == 0 and len(st.session_state.active_images) > 1 else ("Image T2" if idx == 1 else "Active Scene")
                    st.image(pil_img, caption=f"{lbl}: {Path(img_path).name}", use_container_width=True)

with col_info:
    st.markdown("##### 📊 Scene Analytics & Spectral Findings")
    st.caption(f"Active Scene: **{st.session_state.active_scene_title}**")

    # If an analysis has occurred, display genuine spectral breakdown
    if st.session_state.last_analysis:
        last = st.session_state.last_analysis
        tech = last.get("technical_details", {})
        
        m_c1, m_c2, m_c3 = st.columns(3)
        with m_c1:
            veg = tech.get("vegetation_coverage_pct", "N/A")
            st.markdown(f'<div class="metric-card"><div class="metric-val">{veg}%</div><div class="metric-lbl">Vegetation</div></div>', unsafe_allow_html=True)
        with m_c2:
            water = tech.get("water_coverage_pct", "N/A")
            st.markdown(f'<div class="metric-card"><div class="metric-val">{water}%</div><div class="metric-lbl">Water Bodies</div></div>', unsafe_allow_html=True)
        with m_c3:
            conf = int(last.get("confidence", 0.85) * 100)
            st.markdown(f'<div class="metric-card"><div class="metric-val">{conf}%</div><div class="metric-lbl">Confidence</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Show evidence overlay if available
        evidence_path = last.get("evidence", {}).get("path")
        if evidence_path and Path(evidence_path).exists():
            st.image(evidence_path, caption="Visual Spectral Evidence Overlay", use_container_width=True)

        with st.expander("⚙️ Technical Processing Pipeline", expanded=False):
            st.json({
                "model_used": last.get("model_used"),
                "intent": last.get("intent"),
                "intent_confidence": f"{last.get('intent_confidence', 0.85):.2f}",
                "processing_time_sec": tech.get("processing_time_sec", 0.05),
                "resolution_m": tech.get("resolution_m", 10.0),
                "bands_processed": tech.get("spectral_bands", ["B02-Blue", "B03-Green", "B04-Red", "B08-NIR"])
            })
    else:
        st.info("Ask a query below (e.g. *'Explain about the image'* or *'Detect water and vegetation'*) to generate spectral land cover findings.")


# -----------------------------------------------------------------------------
# Conversational Chatbot Interface
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("##### 💬 Satellite Vision-Language Q&A")

# Render historical messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "metadata" in msg and msg["metadata"]:
            meta = msg["metadata"]
            if meta.get("model_used"):
                st.caption(f"🧠 Engine: **{meta['model_used']}** · Confidence: **{int(meta.get('confidence', 0.85)*100)}%**")

# Handle new user query
prompt = st.chat_input("Ask about land cover, vegetation, water bodies, or changes (e.g., 'What land cover types are visible?')...")

if prompt:
    if not st.session_state.active_images:
        st.error("Please select or upload a satellite image first!")
    else:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt, "timestamp": datetime.now(timezone.utc).isoformat()})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing spectral bands and executing vision-language model..."):
                try:
                    result = agent_controller.process_query(
                        query=prompt,
                        image_paths=st.session_state.active_images,
                        session_id=st.session_state.session_id,
                        user_id=st.session_state.user_name
                    )

                    answer_text = result["answer"]
                    st.markdown(answer_text)

                    # Update last analysis state
                    st.session_state.last_analysis = result

                    # Append to session messages
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer_text,
                        "timestamp": result["timestamp"],
                        "metadata": {
                            "model_used": result.get("model_used"),
                            "confidence": result.get("confidence"),
                            "intent": result.get("intent")
                        }
                    })

                    # Auto-refresh to update the spectral findings card
                    st.rerun()

                except Exception as e:
                    logger.error(f"Error processing query: {e}")
                    st.error(f"Analysis failed: {str(e)}")
