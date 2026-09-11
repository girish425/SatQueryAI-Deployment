import sys
from pathlib import Path

# Ensure workspace root and backend directory are always present in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
_workspace_dir = _backend_dir.parent
for _p in [str(_workspace_dir), str(_backend_dir)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.chat import router as chat_router
from backend.app.api.upload import router as upload_router
from backend.app.api.retrieve import router as retrieve_router
from backend.app.api.history import router as history_router
from backend.app.api.pdf import router as pdf_router
from backend.app.api.analysis import router as analysis_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("satquery.main")

# Ensure required directories exist
for folder in ["./uploads", "./evidence", "./sample_data", "./data"]:
    Path(folder).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SatQuery AI Backend starting up...")
    logger.info("Modular models configured for lazy loading.")
    yield
    logger.info("SatQuery AI Backend shutting down...")


app = FastAPI(
    title="SatQuery AI API",
    description="Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration: Support decoupled Render frontend, localhost, and custom domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file directories for browser image rendering
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")
app.mount("/evidence", StaticFiles(directory="./evidence"), name="evidence")
app.mount("/sample_data", StaticFiles(directory="./sample_data"), name="sample_data")

# Include API Routers
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(retrieve_router)
app.include_router(history_router)
app.include_router(pdf_router)
app.include_router(analysis_router)


from backend.app.database.mongodb import db_manager

@app.get("/health/db", tags=["health"])
async def database_health_check():
    """
    Dedicated MongoDB Atlas connection health-check endpoint.
    Reports connection state, masked URI, database name, collections,
    and clear diagnostic instructions if disconnected. Never exposes password.
    """
    return db_manager.check_health()


@app.get("/health", tags=["health"])
async def health_check():
    """Health status check endpoint for API and database connectivity."""
    db_health = db_manager.check_health()
    return {
        "status": "healthy",
        "service": "SatQuery AI Backend",
        "version": "1.0.0",
        "database": {
            "status": db_health["status"],
            "database_name": db_health["database"],
            "uri": db_health["uri"],
            "message": db_health["message"]
        }
    }


# Production Static Serving: Serve compiled React frontend if frontend/dist exists
from fastapi.responses import FileResponse
from fastapi import HTTPException

frontend_dist = _workspace_dir / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    logger.info(f"Mounting compiled production frontend from {frontend_dist}")
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Allow API routes, docs, and evidence mounts to pass through
        if full_path.startswith((
            "chat", "upload", "retrieve", "history", "conversation",
            "health", "evidence", "uploads", "sample_data", "docs", "openapi.json"
        )):
            raise HTTPException(status_code=404, detail="API route not found.")
        file_candidate = frontend_dist / full_path
        if file_candidate.is_file():
            return FileResponse(file_candidate)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/", tags=["root"])
    async def root():
        return {
            "message": "Welcome to SatQuery AI API - Multimodal Remote Sensing Vision-Language Assistant",
            "docs_url": "/docs",
            "health_url": "/health"
        }
