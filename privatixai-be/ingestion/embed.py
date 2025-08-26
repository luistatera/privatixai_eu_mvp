from __future__ import annotations

from typing import List
import logging

from config.settings import get_local_embedding_model_dir
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_model_instance = None


def _get_model():
    """Get the global SentenceTransformer model instance, loading if necessary"""
    global _model_instance
    if _model_instance is None:
        logger.info({"event": "embedder_loading_started", "trigger": "first_request"})
        # Lazy import to avoid heavy dependencies at app startup
        from sentence_transformers import SentenceTransformer  # type: ignore
        # Force offline/local-only: prevent any network attempts
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

        local_dir: Path = get_local_embedding_model_dir()
        if not local_dir.exists():
            raise RuntimeError(
                f"Local embedding model not found at {local_dir}. "
                "The installer must bundle BAAI/bge-m3 here."
            )
        _model_instance = SentenceTransformer(str(local_dir))
        logger.info({"event": "embedder_loading_completed"})
    return _model_instance


def is_model_loaded() -> bool:
    """Check if the model is already loaded in memory"""
    return _model_instance is not None


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = _get_model()
    return [vec.tolist() for vec in model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)]


# Specialized helpers to follow BGE-m3 best practices
def embed_passages(texts: List[str]) -> List[List[float]]:
    """Embed passages/chunks with the recommended "passage: " prefix and L2 normalization."""
    if not texts:
        return []
    prefixed = [f"passage: {t}" for t in texts]
    return embed_texts(prefixed)


def embed_queries(texts: List[str]) -> List[List[float]]:
    """Embed queries with the recommended "query: " prefix and L2 normalization."""
    if not texts:
        return []
    prefixed = [f"query: {t}" for t in texts]
    return embed_texts(prefixed)


