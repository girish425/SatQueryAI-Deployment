# SatQuery AI

**An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries**

SatQuery AI is a specialized, production-ready satellite image analysis chatbot. It combines an Agentic Controller with dedicated remote sensing analysis workflows, native GeoTIFF (.tif/.tiff) processing, STAC API imagery search, persistent conversation history, and publication-quality PDF export.

---

## 1. Project Overview

SatQuery AI enables users to upload or retrieve high-resolution satellite imagery and interact through natural-language conversation. Unlike generic chatbots that route everything through a single LLM or execute all computer-vision models simultaneously, SatQuery AI features a central **Agent Controller** that:
1. Analyzes the user's query and attached satellite imagery.
2. Identifies the specific remote sensing intent (`vqa`, `grounding`, `image_understanding`, `change_detection`, or `optical_sar`).
3. Selects and executes **only ONE** appropriate specialized AI model.
4. Dynamically calculates genuine radiometric statistics, indices, and uncertainty metrics (no hardcoded answers or fake confidence numbers).
5. Delivers structured findings, visual evidence maps, and collapsible raster metadata.
6. Persists conversations in MongoDB and exports them into PDF reports.

---

## 2. Features

- **Agentic Dynamic Model Routing**: Query-driven workflow selection executing only the required engine with lazy loading.
- **Genuine Image-Derived Analytics**: Land cover percentages, vegetative greenness, water masks, and change detection metrics calculated directly from raster pixels.
- **Native GeoTIFF Ingestion**: Reads `.tif` and `.tiff` formats with band extraction, CRS identification, and 2%-98% cumulative contrast-stretched RGB web previews.
- **Bi-Temporal Change Detection**: Aligns multi-temporal acquisitions, computes absolute difference maps, thresholded change masks, and changed-area percentages.
- **Optical & SAR Fusion**: Compares optical surface reflectance with microwave Synthetic Aperture Radar (SAR) backscatter, distinguishing specular water reflection from double-bounce urban structures.
- **Visual Grounding**: Localizes geographic features (rivers, vegetation, roads, buildings) with glowing bounding boxes and contour masks.
- **BigEarthNet.txt Benchmark Integration (arXiv:2603.29630)**: Multi-modal retrieval featuring co-registered Sentinel-1 SAR and Sentinel-2 Multispectral pairs with 9.6M text annotations (geographically anchored captions, multi-task VQA pairs, referring expressions for grounding, and CORINE Land Cover classes).
- **One-Click Multi-Modal Staging**: Stage Sentinel-2 optical, Sentinel-1 SAR, or both co-registered rasters together for instant multimodal analysis.
- **STAC Satellite Retrieval**: Natural-language satellite search querying STAC-compliant remote sensing catalogs (Sentinel-2, Sentinel-1 SAR, Landsat-9).
- **Session History & MongoDB**: Full conversational persistence with automatic local fallback if MongoDB is not running.
- **ReportLab PDF Export**: One-click download of the active conversation complete with session metadata, Q&A turns, and embedded evidence imagery.

---

## 3. Architecture

```
                      ┌─────────────────────────┐
                      │  React + Vite Chat UI   │
                      └────────────┬────────────┘
                                   │ HTTP / JSON
                                   ▼
                      ┌─────────────────────────┐
                      │     FastAPI Backend     │
                      └────────────┬────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │    Agent Controller     │
                      │  - Intent Classifier    │
                      │  - Model Selector       │
                      └────────────┬────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
┌───────────────────────┐┌───────────────────┐┌───────────────────────┐
│ Image Understanding   ││ Visual QA (VQA)   ││ Image Grounding       │
└───────────────────────┘└───────────────────┘└───────────────────────┘
            ▼                      ▼
┌───────────────────────┐┌───────────────────┐
│ Change Detection      ││ Optical-SAR Fusion│
└───────────────────────┘└───────────────────┘
                                   │
                      ┌────────────┴────────────┐
                      ▼                         ▼
            ┌───────────────────┐     ┌───────────────────┐
            │  Evidence & Preview│    │  MongoDB History  │
            │  Generators (PNG) │     │  & PDF Exporter   │
            └───────────────────┘     └───────────────────┘
```

---

## 4. Tech Stack

- **Frontend**:
  - React 19 / Vite
  - Lucide React (Icons)
  - Axios
  - Custom CSS Design System (Satellite/Dark AI theme)
- **Backend**:
  - Python 3.12+
  - FastAPI & Uvicorn
  - Pydantic v2
  - PyMongo & Python-dotenv
  - ReportLab (PDF Generation)
- **Remote Sensing & Computer Vision**:
  - NumPy & SciPy
  - Tifffile & Pillow (GeoTIFF processing)
  - STAC API Client (httpx)
- **Testing**:
  - Pytest & Starlette TestClient

---

## 5. Folder Structure

```
SatQueryAI/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── controller.py          # Central agent coordinator
│   │   │   ├── intent_classifier.py   # Intent classification & confidence
│   │   │   └── model_selector.py      # Model registry and single-model routing
│   │   ├── api/
│   │   │   ├── chat.py                # POST /chat/
│   │   │   ├── upload.py              # POST /upload/
│   │   │   ├── retrieve.py            # POST /retrieve/ & GET /retrieve/results
│   │   │   ├── history.py             # GET /history/ & GET /history/{session_id}
│   │   │   ├── pdf.py                 # GET /conversation/{session_id}/pdf
│   │   │   └── analysis.py            # GET /analysis/models
│   │   ├── database/
│   │   │   ├── mongodb.py             # MongoDB connection & local fallback store
│   │   │   └── schemas.py             # Pydantic schemas
│   │   ├── models/
│   │   │   ├── vqa.py                 # Question-aware RS VQA
│   │   │   ├── grounding.py           # Feature grounding & bounding boxes
│   │   │   ├── change_detection.py    # Multi-temporal difference mapping
│   │   │   ├── optical_sar.py         # Optical vs SAR fusion
│   │   │   └── image_understanding.py # Land cover & scene statistics
│   │   ├── pdf/
│   │   │   └── conversation_pdf.py    # ReportLab PDF generator
│   │   ├── satellite/
│   │   │   ├── preprocessing.py       # GeoTIFF contrast stretching & RGB previews
│   │   │   ├── stac_client.py         # STAC catalog client
│   │   │   └── image_retrieval.py     # NL query interpretation for STAC
│   │   ├── utils/
│   │   │   ├── file_validator.py      # GeoTIFF validation
│   │   │   ├── geotiff_utils.py       # Raster reading & stats
│   │   │   └── confidence.py          # Uncertainty & confidence metrics
│   │   └── main.py                    # FastAPI entrypoint
│   ├── tests/                         # Automated test suite
│   ├── sample_data/                   # Curated GeoTIFF test rasters
│   ├── requirements.txt
│   ├── .env.example
│   └── run_backend.py
├── frontend/
│   ├── src/
│   │   ├── components/                # Modular React components
│   │   ├── pages/                     # Chat page
│   │   ├── services/                  # Axios API service
│   │   ├── utils/                     # Client validation
│   │   ├── App.jsx                    # Root app
│   │   └── index.css                  # Modern UI styles
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 6. Installation & Prerequisites

Ensure Python 3.10+ and Node.js v18+ are installed on your machine.

### Backend Setup

1. Open a terminal in the project root:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Copy the environment configuration:
   ```bash
   cp .env.example .env
   ```

### Frontend Setup

1. Open a terminal in the `frontend` directory:
   ```bash
   cd frontend
   npm install
   ```

---

## 7. Environment Variables

Configure `backend/.env`:

```ini
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=satquery_ai
HOST=127.0.0.1
PORT=8000
DEBUG=True
UPLOAD_DIR=./uploads
EVIDENCE_DIR=./evidence
```

*Note: If MongoDB Atlas or local MongoDB is offline or not installed, the application automatically activates a resilient local file-backed store so you can test immediately without any database setup.*

---

## 8. Running the Application

### 1. Start the Backend API
In the project root or `backend` folder:
```bash
python backend/run_backend.py
```
- Backend starts at: `http://127.0.0.1:8000`
- Interactive Swagger API docs: `http://127.0.0.1:8000/docs`

### 2. Start the Frontend Dev Server
In the `frontend` directory:
```bash
cd frontend
npm run dev
```
- Frontend starts at: `http://localhost:5173`

---

## 9. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Backend health check |
| `POST` | `/upload/` | Upload & validate GeoTIFF satellite image |
| `POST` | `/chat/` | Submit query + attached images to Agent Controller |
| `GET` | `/history/` | List stored conversations |
| `GET` | `/history/{session_id}` | Fetch full session transcript |
| `DELETE` | `/history/{session_id}` | Remove a conversation session |
| `POST` | `/retrieve/` | Search satellite imagery via natural language |
| `GET` | `/retrieve/results` | List STAC satellite imagery catalog |
| `POST` | `/retrieve/select/{id}` | Stage a retrieved satellite image into the chat |
| `GET` | `/conversation/{id}/pdf` | Download formatted conversation PDF report |

---

## 10. Supported Image Formats

- **Primary Supported**: `.tif`, `.tiff` (GeoTIFF)
- Multi-band (e.g. RGB, RGB+NIR, multispectral Sentinel-2/Landsat) and single-band (SAR backscatter, panchromatic).
- Uploading unsupported formats (such as `.png`, `.jpg`, `.exe`) returns a clear user-friendly error:
  `"Unsupported file type. Please upload a .tif or .tiff satellite image."`

---

## 11. Testing

Run the automated test suite covering intent classification, response variation, GeoTIFF validation, change detection, and API endpoints:

```bash
python -m pytest backend/tests -v
```

Output:
```
backend/tests/test_api.py::test_api_health PASSED
backend/tests/test_api.py::test_api_upload_geotiff PASSED
backend/tests/test_api.py::test_api_chat_flow PASSED
backend/tests/test_change_detection.py::test_change_detection_different_images PASSED
backend/tests/test_change_detection.py::test_change_detection_identical_images PASSED
backend/tests/test_change_detection.py::test_change_detection_missing_second_image PASSED
backend/tests/test_image_validation.py::test_valid_geotiff PASSED
backend/tests/test_image_validation.py::test_unsupported_extension PASSED
backend/tests/test_image_validation.py::test_corrupted_tif PASSED
backend/tests/test_intent.py::test_intent_image_understanding PASSED
backend/tests/test_intent.py::test_intent_vqa_presence PASSED
backend/tests/test_intent.py::test_intent_grounding PASSED
backend/tests/test_intent.py::test_intent_change_detection PASSED
backend/tests/test_intent.py::test_intent_optical_sar PASSED
backend/tests/test_response_variation.py::test_five_questions_produce_distinct_responses PASSED
======================= 15 passed in 4.14s =======================
```

---

## 12. Deployment Guide

SatQuery AI is designed for single-command production deployment using a unified full-stack architecture where the FastAPI backend serves both the API endpoints and the compiled React production SPA.

### Option A: 1-Click Cloud Deployment (Render.com)
1. Push your repository to GitHub or GitLab.
2. In [Render Dashboard](https://dashboard.render.com), click **New +** -> **Blueprint**.
3. Select your repository. Render automatically reads [`render.yaml`](file:///c:/Users/giris/Downloads/SatQueryAI/render.yaml) and provisions the Web Service using the multi-stage Dockerfile.
4. Set your `MONGODB_URI` environment variable in the Render Environment tab:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?appName=SatQueryAI
   DATABASE_NAME=satquery_ai
   ```
5. Click **Deploy**. Your app will be live at `https://<your-service>.onrender.com`.

### Option B: 1-Click Cloud Deployment (Railway.app)
1. In [Railway Dashboard](https://railway.app), click **New Project** -> **Deploy from GitHub repo**.
2. Select your SatQuery AI repository. Railway will detect [`railway.json`](file:///c:/Users/giris/Downloads/SatQueryAI/railway.json) and build the Docker container.
3. In the project **Variables** tab, add:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/?appName=SatQueryAI
   DATABASE_NAME=satquery_ai
   ```
4. Click **Generate Domain**. Your application is live!

### Option C: Docker & Docker Compose (Self-Hosted / VPS)
Run the entire production stack in a container on any Linux/Windows/macOS server:

```bash
# 1. Clone repository
git clone <repo-url>
cd SatQueryAI

# 2. Configure environment
cp backend/.env.example .env
# Edit .env with your MongoDB Atlas URI

# 3. Build and launch container
docker compose up -d --build
```
Access the application at `http://<server-ip>:8000`.

### Option D: Local / Bare-Metal Production Deployment
Run without Docker using the preconfigured scripts:

- **Windows**:
  ```cmd
  deploy.bat
  ```
- **Linux / macOS**:
  ```bash
  chmod +x deploy.sh
  ./deploy.sh
  ```

---

## 13. Troubleshooting & FAQ

- **Q: How do I resolve MongoDB Atlas TLS Alert errors (`SSL: TLSV1_ALERT_INTERNAL_ERROR`)?**  
  *A: In the MongoDB Atlas Console, navigate to **Security** -> **Network Access** -> click **Add IP Address** -> select **Allow Access from Anywhere** (`0.0.0.0/0`) or add your current IP address.*
- **Q: Does the app require an active internet connection to start?**  
  *A: No. Built-in sample datasets, resilient local storage fallback, and local preprocessing allow complete offline testing.*
- **Q: How does Change Detection work?**  
  *A: Attach two images using the '+' menu (or select two sample images like `sample_change_t1.tif` and `sample_change_t2.tif`) and ask "What changed between these images?". The agent detects the change detection intent and computes a difference map.*
- **Q: Why does the PDF download not print the webpage?**  
  *A: The backend uses ReportLab to assemble an official analysis document embedding the conversation transcript, metadata, and visual evidence images.*

