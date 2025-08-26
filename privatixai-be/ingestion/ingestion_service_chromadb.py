"""
Ingestion Service - Orchestrates text ingestion pipeline and encrypted storage
Modified to use ChromaDB's built-in embeddings instead of external BGE model.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from config.settings import settings
from ingestion.extract_text import extract_text
from ingestion.normalize import normalize_text
from ingestion.chunk import fixed_size_chunk
# Import the ChromaDB direct embedding module instead of BGE
from ingestion.embed_chromadb import embed_passages
from service.encryption_service import encrypt_to_file
from vectorstore.chroma_store import add_documents  # Use add_documents instead of upsert_embeddings
from service.retrieval_service import invalidate_retrieval_cache
from ingestion.transcribe import transcribe_audio
from utils.telemetry import emit_event


logger = logging.getLogger(__name__)


class IngestionStage:
    RECEIVED = "received"
    EXTRACTING = "extracting"
    TRANSCRIBING = "transcribing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    UPSERTING = "upserting"
    COMPLETE = "complete"
    ERROR = "error"


def ingest_text_file(file_path: Path, file_id: str, set_status) -> None:
    """
    Synchronous ingestion pipeline using ChromaDB's built-in embeddings.
    `set_status(stage, progress, error?)` updates status.
    """
    try:
        set_status(IngestionStage.EXTRACTING, 10)
        emit_event("ingestion_stage", {"file_id": file_id, "stage": IngestionStage.EXTRACTING})
        text, strategy = extract_text(file_path)
        normalized = normalize_text(text)

        set_status(IngestionStage.CHUNKING, 25)
        emit_event("ingestion_stage", {"file_id": file_id, "stage": IngestionStage.CHUNKING})
        
        # Token-based chunking with overlap, controlled by settings
        from ingestion.chunk import token_chunk
        chunks: List[Tuple[int, int, str]] = token_chunk(
            normalized,
            target_tokens=settings.CHUNK_TARGET_TOKENS,
            min_tokens=settings.CHUNK_MIN_TOKENS,
            overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
        )

        # Persist encrypted chunks and prepare metadata
        set_status(IngestionStage.EMBEDDING, 45)
        emit_event("ingestion_stage", {"file_id": file_id, "stage": IngestionStage.EMBEDDING})
        
        # Load original filename for better UX in citations
        import json
        meta_path = settings.UPLOAD_PATH / f"{file_id}.meta"
        original_filename: str = file_path.name
        try:
            if meta_path.exists():
                data = json.loads(meta_path.read_text())
                original_filename = str(data.get("original_filename") or original_filename)
        except Exception:
            pass
        
        from pathlib import Path as _Path
        original_ext = _Path(original_filename).suffix.lower() or file_path.suffix.lower()
        
        def _normalize_name(name: str) -> str:
            n = name.lower().strip()
            n = n.replace("_", " ").replace("-", " ")
            n = " ".join(n.split())
            return n
        
        chunk_texts = []
        chunk_ids: List[str] = []
        metadatas: List[Dict] = []
        
        for start, end, chunk_text in chunks:
            chunk_id = uuid.uuid4().hex
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk_text)
            
            # Encrypt and store the chunk text
            encrypt_to_file(settings.CHUNKS_PATH / f"{chunk_id}.enc", chunk_text.encode("utf-8"))
            
            metadatas.append({
                "chunk_id": chunk_id,
                "file_id": file_id,
                # Prefer original filename for display and matching
                "file_name": original_filename,
                "original_filename": original_filename,
                "normalized_filename": _normalize_name(original_filename),
                "storage_filename": file_path.name,
                "file_ext": original_ext,
                "start": start,
                "end": end,
                "extract_strategy": strategy,
            })

        # ChromaDB will handle embeddings automatically when using add_documents
        # No need to call external embedding model
        logger.info({"event": "chromadb_direct_ingestion", "chunks": len(chunk_ids)})

        set_status(IngestionStage.UPSERTING, 70)
        emit_event("ingestion_stage", {"file_id": file_id, "stage": IngestionStage.UPSERTING, "chunks": len(chunk_ids)})
        
        # Use add_documents instead of upsert_embeddings - ChromaDB handles embeddings automatically
        add_documents(documents=chunk_texts, metadatas=metadatas, ids=chunk_ids)

        set_status(IngestionStage.COMPLETE, 100)
        logger.info({"event": "ingestion_completed", "file_id": file_id, "chunks": len(chunk_ids)})
        invalidate_retrieval_cache()
        emit_event("ingestion_completed", {"file_id": file_id, "chunks": len(chunk_ids)})
        
    except Exception as e:
        logger.error(f"Ingestion failed for {file_id}: {e}")
        set_status(IngestionStage.ERROR, 100, str(e))
        emit_event("ingestion_error", {"file_id": file_id, "error": str(e)[:200]})


def ingest_file_any(file_path: Path, file_id: str, set_status) -> None:
    """
    Route to appropriate ingestion method based on file type.
    Uses ChromaDB's built-in embeddings for all file types.
    """
    suffix = file_path.suffix.lower()
    if suffix in settings.SUPPORTED_TEXT_FORMATS:
        return ingest_text_file(file_path, file_id, set_status)
    if suffix in settings.SUPPORTED_AUDIO_FORMATS:
        try:
            set_status(IngestionStage.TRANSCRIBING, 10)
            emit_event("ingestion_stage", {"file_id": file_id, "stage": IngestionStage.TRANSCRIBING})
            text, meta = transcribe_audio(file_path)
            
            # Save transcript encrypted
            encrypt_to_file(settings.TRANSCRIPTS_PATH / f"{file_id}.enc", text.encode("utf-8"))
            
            # Continue like text
            normalized = normalize_text(text)
            set_status(IngestionStage.CHUNKING, 25)
            emit_event("ingestion_stage", {"file_id": file_id, "stage": IngestionStage.CHUNKING})
            
            from ingestion.chunk import token_chunk
            chunks: List[Tuple[int, int, str]] = token_chunk(
                normalized,
                target_tokens=settings.CHUNK_TARGET_TOKENS,
                min_tokens=settings.CHUNK_MIN_TOKENS,
                overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
            )
            
            set_status(IngestionStage.EMBEDDING, 45)
            emit_event("ingestion_stage", {"file_id": file_id, "stage": IngestionStage.EMBEDDING})
            
            chunk_texts = []
            chunk_ids: List[str] = []
            metadatas: List[Dict] = []
            
            for start, end, chunk_text in chunks:
                chunk_id = uuid.uuid4().hex
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk_text)
                
                # Encrypt and store the chunk text
                encrypt_to_file(settings.CHUNKS_PATH / f"{chunk_id}.enc", chunk_text.encode("utf-8"))
                
                # Load original filename for display
                import json
                meta_path = settings.UPLOAD_PATH / f"{file_id}.meta"
                original_filename: str = file_path.name
                try:
                    if meta_path.exists():
                        data = json.loads(meta_path.read_text())
                        original_filename = str(data.get("original_filename") or original_filename)
                except Exception:
                    pass
                
                from pathlib import Path as _Path
                original_ext = _Path(original_filename).suffix.lower() or file_path.suffix.lower()
                
                def _normalize_name(name: str) -> str:
                    n = name.lower().strip()
                    n = n.replace("_", " ").replace("-", " ")
                    n = " ".join(n.split())
                    return n
                
                metadatas.append({
                    "chunk_id": chunk_id,
                    "file_id": file_id,
                    "file_name": original_filename,
                    "original_filename": original_filename,
                    "normalized_filename": _normalize_name(original_filename),
                    "storage_filename": file_path.name,
                    "file_ext": original_ext,
                    "start": start,
                    "end": end,
                    "extract_strategy": "audio_whisper",
                })
            
            # ChromaDB will handle embeddings automatically
            logger.info({"event": "chromadb_direct_audio_ingestion", "chunks": len(chunk_ids)})
            
            set_status(IngestionStage.UPSERTING, 70)
            emit_event("ingestion_stage", {"file_id": file_id, "stage": IngestionStage.UPSERTING, "chunks": len(chunk_ids)})
            
            # Use add_documents - ChromaDB handles embeddings automatically
            add_documents(documents=chunk_texts, metadatas=metadatas, ids=chunk_ids)
            
            set_status(IngestionStage.COMPLETE, 100)
            logger.info({"event": "ingestion_completed", "file_id": file_id, "chunks": len(chunk_ids)})
            invalidate_retrieval_cache()
            emit_event("ingestion_completed", {"file_id": file_id, "chunks": len(chunk_ids)})
            
        except Exception as e:
            logger.error(f"Audio ingestion failed for {file_id}: {e}")
            set_status(IngestionStage.ERROR, 100, str(e))
            emit_event("ingestion_error", {"file_id": file_id, "error": str(e)[:200]})
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

