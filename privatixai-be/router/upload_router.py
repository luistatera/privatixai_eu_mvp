"""
Upload Router - API endpoints for file upload and processing
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import Dict, Any, Optional
import logging
import uuid
from pathlib import Path
import io

from config.settings import settings
from ingestion.detect import guess_supported_suffix
from service.ingestion_service import ingest_text_file, ingest_file_any, IngestionStage
from utils.telemetry import emit_event
try:
    from mutagen import File as MutagenFile  # type: ignore
except Exception:  # pragma: no cover - optional
    MutagenFile = None  # type: ignore

logger = logging.getLogger(__name__)
router = APIRouter()

 # License checks are out of scope for v1.0

_status_store: Dict[str, Dict[str, Any]] = {}


def _set_status(file_id: str):
    def setter(stage: str, progress: int, error: Optional[str] = None):
        _status_store[file_id] = {
            "file_id": file_id,
            "stage": stage,
            "progress": progress,
            "error": error,
        }
    return setter


@router.post("/file")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload and process a single file"""
    try:
        logger.info({"event": "upload_requested", "filename": file.filename})
        content = await file.read()
        suffix = guess_supported_suffix(file.filename or "", content, file.content_type)
        if not suffix:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail="File too large")

        file_id = uuid.uuid4().hex
        dest_path = settings.UPLOAD_PATH / f"{file_id}{suffix}"
        settings.UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(content)
        
        # Store file metadata for UI display
        import json
        from datetime import datetime
        metadata_path = settings.UPLOAD_PATH / f"{file_id}.meta"
        metadata = {
            "file_id": file_id,
            "original_filename": file.filename or "unknown",
            "storage_filename": f"{file_id}{suffix}",
            "file_extension": suffix,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "file_size": len(content),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2))

        _status_store[file_id] = {
            "file_id": file_id,
            "stage": IngestionStage.RECEIVED,
            "progress": 5,
            "error": None,
        }
        emit_event("ingestion_received", {"file_id": file_id, "suffix": suffix})

        # Enforce max audio duration pre-ingestion when possible
        if suffix in settings.SUPPORTED_AUDIO_FORMATS and suffix == ".mp3" and MutagenFile is not None:
            try:
                audio = MutagenFile(io.BytesIO(content))  # type: ignore
                duration = float(getattr(getattr(audio, "info", None), "length", 0.0)) if audio else 0.0
                max_seconds = settings.MAX_AUDIO_DURATION_MINUTES * 60
                if duration and duration > max_seconds:
                    _status_store[file_id] = {
                        "file_id": file_id,
                        "stage": IngestionStage.ERROR,
                        "progress": 100,
                        "error": "Audio duration exceeds limit",
                    }
                    emit_event("ingestion_rejected_audio_duration", {"file_id": file_id, "seconds": duration})
                    # Remove saved file as we reject it
                    try:
                        dest_path.unlink(missing_ok=True)  # type: ignore[attr-defined]
                    except Exception:
                        pass
                    raise HTTPException(status_code=413, detail="Audio duration exceeds limit")
            except HTTPException:
                raise
            except Exception:
                # If duration detection fails, proceed to ingestion where duration is enforced again
                pass

        def run_ingestion():
            set_status = _set_status(file_id)
            ingest_file_any(dest_path, file_id, set_status)

        background_tasks.add_task(run_ingestion)
        emit_event("ingestion_scheduled", {"file_id": file_id})

        return {"file_id": file_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{file_id}")
async def get_upload_status(
    file_id: str,
):
    """Get processing status of uploaded file"""
    status = _status_store.get(file_id)
    if not status:
        return {"file_id": file_id, "stage": "unknown", "progress": 0}
    emit_event("ingestion_status", {"file_id": file_id, "stage": status.get("stage"), "progress": status.get("progress")})
    return status

@router.get("/files")
async def list_uploaded_files():
    """List all uploaded files with original names and metadata"""
    import json
    from datetime import datetime
    
    files = []
    if not settings.UPLOAD_PATH.exists():
        return files
    
    # First, create missing metadata files for existing uploads
    _create_missing_metadata()
    
    # Find all .meta files
    for meta_file in settings.UPLOAD_PATH.glob("*.meta"):
        try:
            metadata = json.loads(meta_file.read_text())
            
            # Check if the actual file still exists
            storage_file = settings.UPLOAD_PATH / metadata["storage_filename"]
            if storage_file.exists():
                file_stat = storage_file.stat()
                files.append({
                    "file_id": metadata["file_id"],
                    "name": metadata["original_filename"],
                    "size": file_stat.st_size,
                    "mtimeMs": file_stat.st_mtime * 1000,  # Convert to milliseconds
                    "ext": metadata["file_extension"],
                    "upload_timestamp": metadata.get("upload_timestamp"),
                })
        except Exception as e:
            logger.warning(f"Failed to read metadata from {meta_file}: {e}")
            continue
    
    # Sort by upload time, newest first
    files.sort(key=lambda f: f["mtimeMs"], reverse=True)
    return files

def _create_missing_metadata():
    """Create metadata files for existing uploads that don't have them"""
    import json
    from datetime import datetime
    
    if not settings.UPLOAD_PATH.exists():
        return
    
    # Find uploaded files without metadata
    for file_path in settings.UPLOAD_PATH.iterdir():
        if file_path.is_file() and not file_path.name.endswith('.meta'):
            # Extract file_id from filename (hash part before extension)
            stem = file_path.stem  # filename without extension
            extension = file_path.suffix
            
            # Check if metadata already exists
            meta_path = settings.UPLOAD_PATH / f"{stem}.meta"
            if not meta_path.exists():
                # Create metadata with best-guess original filename
                file_stat = file_path.stat()
                upload_time = datetime.fromtimestamp(file_stat.st_ctime)
                fallback_name = f"Document_{upload_time.strftime('%Y%m%d_%H%M%S')}{extension}"
                
                metadata = {
                    "file_id": stem,
                    "original_filename": fallback_name,
                    "storage_filename": file_path.name,
                    "file_extension": extension,
                    "upload_timestamp": upload_time.isoformat(),
                    "file_size": file_stat.st_size,
                }
                
                # Try to get original filename from vector metadata
                try:
                    from vectorstore.chroma_store import get_file_metadata_by_id
                    original_name = get_file_metadata_by_id(stem)
                    if original_name:
                        metadata["original_filename"] = original_name
                except Exception as e:
                    logger.debug(f"Could not get original filename from vector metadata: {e}")
                    pass  # Use fallback name
                
                try:
                    meta_path.write_text(json.dumps(metadata, indent=2))
                    logger.info(f"Created missing metadata for {file_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to create metadata for {file_path.name}: {e}")
