"""
PrivatixAI Backend - FastAPI Main Application
MVP 1.0 Hybrid: local ingestion/embeddings/vector search + hosted LLM (Germany)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

from config.settings import settings, validate_paths
from router import chat_router, memory_router, upload_router
from utils.telemetry import get_recent_events
from router import privacy_router
from service.startup_service import startup_warmup, get_warmup_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Add rotating file handler (operational logs only)
try:
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=str(settings.LOG_DIR / "app.log"),
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
except Exception:
    pass

logger = logging.getLogger(__name__)

# Ensure required directories exist early
try:
    validate_paths()
except Exception as e:
    logging.getLogger(__name__).error(f"Failed to validate/create data paths: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="PrivatixAI Backend",
    description="Fully offline AI assistant backend",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "file://"],  # Electron and dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
app.include_router(memory_router.router, prefix="/api/memory", tags=["memory"])
app.include_router(upload_router.router, prefix="/api/upload", tags=["upload"])

# Basic health endpoint for Electron bootstrap
@app.get("/api/health/basic")
async def api_health():
    try:
        return {"status": "ok"}
    except Exception:
        # Should not fail; return unhealthy if any unexpected error occurs
        return {"status": "unhealthy"}

# Development-only diagnostics endpoint (no user content)
@app.get("/api/diagnostics/events")
async def diagnostics_events(limit: int = 200):
    import os
    if not (settings.DEBUG or os.environ.get("PRIVATIXAI_DEV_TELEMETRY") in {"1", "true", "True"}):
        raise HTTPException(status_code=404, detail="Not found")
    return {"events": get_recent_events(limit)}
app.include_router(privacy_router.router, prefix="/api/privacy", tags=["privacy"])
# License routes are out of scope for v1.0

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info({
        "event": "startup_initiated",
        "version": "1.0.0",
        "debug_mode": settings.DEBUG,
        "data_path": str(settings.DATA_PATH),
        "model_path": str(settings.MODEL_PATH)
    })
    # Ensure data directories exist
    validate_paths()
    # No external embedding model required when using Chroma text embeddings
    
    # Preload and warm critical components
    await startup_warmup()
    
    logger.info({"event": "startup_completed"})

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "PrivatixAI Backend",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check with warmup state"""
    warmup_state = get_warmup_state()
    return {
        "status": "healthy",
        "data_path": str(settings.DATA_PATH),
        "vectorstore_path": str(settings.VECTORSTORE_PATH),
        "embedder_loaded": warmup_state["embedder_loaded"],
        "index_warmed": warmup_state["index_warmed"],
        "collection_docs_count": warmup_state["collection_docs_count"],
        "warmup_duration_seconds": warmup_state["warmup_duration_seconds"]
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",  # Local only for privacy
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
