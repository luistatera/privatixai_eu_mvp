from __future__ import annotations

"""
ChromaDB Direct Embedding Module
Uses ChromaDB's built-in default embeddings instead of external BGE model.
This provides a simpler, dependency-free embedding solution.
"""

from typing import List
import logging

logger = logging.getLogger(__name__)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    This function is a placeholder for compatibility.
    ChromaDB will handle embeddings automatically when using add_documents().
    Returns empty embeddings as ChromaDB will generate them.
    """
    logger.info({"event": "chromadb_direct_embedding_requested", "texts_count": len(texts)})
    # ChromaDB will handle embeddings automatically
    # Return empty embeddings for compatibility
    return []


def embed_passages(texts: List[str]) -> List[List[float]]:
    """
    This function is a placeholder for compatibility.
    ChromaDB will handle passage embeddings automatically.
    """
    logger.info({"event": "chromadb_direct_passage_embedding_requested", "texts_count": len(texts)})
    # ChromaDB will handle embeddings automatically
    return []


def embed_queries(texts: List[str]) -> List[List[float]]:
    """
    This function is a placeholder for compatibility.
    ChromaDB will handle query embeddings automatically.
    """
    logger.info({"event": "chromadb_direct_query_embedding_requested", "texts_count": len(texts)})
    # ChromaDB will handle embeddings automatically
    return []


def is_model_loaded() -> bool:
    """Always returns True since ChromaDB handles embeddings automatically"""
    return True


def _get_model():
    """Returns None since we don't need an external model"""
    return None

