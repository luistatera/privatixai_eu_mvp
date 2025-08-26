"""
Privacy Router - GDPR endpoints for consent, export, and purge
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import tempfile
import zipfile
import logging

from config.settings import settings, validate_paths

logger = logging.getLogger(__name__)
router = APIRouter()


def _consent_file() -> Path:
    return settings.PRIVACY_PATH / "consent.json"


@router.get("/consent")
async def get_consent_status() -> Dict[str, Any]:
    """Return consent status if recorded."""
    try:
        path = _consent_file()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return {"consented_at": data.get("consented_at")}
        return {"consented_at": None}
    except Exception as e:
        logger.error(f"Consent status read failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to read consent status")


@router.post("/consent")
async def record_consent() -> Dict[str, Any]:
    """Record consent timestamp locally."""
    try:
        settings.PRIVACY_PATH.mkdir(parents=True, exist_ok=True)
        now = datetime.now(tz=timezone.utc).isoformat()
        payload = {"consented_at": now}
        _consent_file().write_text(json.dumps(payload), encoding="utf-8")
        logger.info({"event": "privacy_consent_recorded"})
        return payload
    except Exception as e:
        logger.error(f"Consent record failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to record consent")


def _add_tree_to_zip(zipf: zipfile.ZipFile, root: Path, arc_prefix: str, manifest: Dict[str, Any]):
    if not root.exists():
        return
    for p in root.rglob("*"):
        if p.is_file():
            arcname = f"{arc_prefix}/{p.relative_to(root).as_posix()}"
            try:
                zipf.write(p, arcname=arcname)
                manifest["files"].append({
                    "path": arcname,
                    "size": p.stat().st_size,
                })
            except Exception:
                continue


@router.post("/export")
async def export_data(background_tasks: BackgroundTasks):
    """Assemble a zip containing uploads, chunks, transcripts, vectorstore, and a manifest.

    Excludes keystore/secrets. Uses a temp file and schedules deletion after response is sent.
    """
    try:
        # Build temp zip
        tmp_dir = Path(tempfile.mkdtemp(prefix="privatixai_export_"))
        zip_path = tmp_dir / f"export_{int(datetime.now(tz=timezone.utc).timestamp())}.zip"

        manifest: Dict[str, Any] = {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "app_version": "1.0.0",
            "files": [],
        }

        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            # Include directories
            _add_tree_to_zip(zipf, settings.UPLOAD_PATH, "uploads", manifest)
            _add_tree_to_zip(zipf, settings.CHUNKS_PATH, "chunks", manifest)
            _add_tree_to_zip(zipf, settings.TRANSCRIPTS_PATH, "transcripts", manifest)
            _add_tree_to_zip(zipf, settings.VECTORSTORE_PATH, "vectorstore", manifest)
            # Include privacy artifacts except secrets/keys
            if _consent_file().exists():
                try:
                    zipf.write(_consent_file(), arcname="privacy/consent.json")
                    manifest["files"].append({
                        "path": "privacy/consent.json",
                        "size": _consent_file().stat().st_size,
                    })
                except Exception:
                    pass
            # Write manifest
            zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

        logger.info({"event": "privacy_export_ready"})

        def _cleanup():
            try:
                if zip_path.exists():
                    zip_path.unlink()
                if tmp_dir.exists():
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

        background_tasks.add_task(_cleanup)

        return FileResponse(
            path=str(zip_path),
            filename="privatixai_export.zip",
            media_type="application/zip",
            background=background_tasks,
        )
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.delete("/delete")
async def purge_vault() -> Dict[str, Any]:
    """Delete vault directories (uploads, chunks, transcripts, vectorstore). Idempotent."""
    try:
        # Reset vectorstore handles first to avoid open handles during deletion
        try:
            from vectorstore.chroma_store import reset as reset_vectorstore
            reset_vectorstore()
        except Exception:
            pass

        for p in [settings.UPLOAD_PATH, settings.CHUNKS_PATH, settings.TRANSCRIPTS_PATH, settings.VECTORSTORE_PATH]:
            try:
                if p.exists():
                    shutil.rmtree(p, ignore_errors=True)
            except Exception:
                continue
        # Recreate expected directory structure
        validate_paths()
        logger.info({"event": "privacy_purge_completed"})
        return {"ok": True}
    except Exception as e:
        logger.error(f"Purge failed: {e}")
        raise HTTPException(status_code=500, detail="Purge failed")


