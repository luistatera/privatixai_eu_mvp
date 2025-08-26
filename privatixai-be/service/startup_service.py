"""
Startup Service - preload and warm critical components at app startup
This service ensures embedder and vector store are ready before first user request
"""

import logging
import time
from typing import Dict, Any
from pathlib import Path

from config.settings import settings, get_local_embedding_model_dir
from utils.telemetry import emit_event

logger = logging.getLogger(__name__)

# Global state to track warmup completion
_warmup_state = {
    "embedder_loaded": False,
    "index_warmed": False,
    "collection_docs_count": 0,
    "warmup_duration_seconds": 0.0,
    "warmup_completed_at": None
}

def get_warmup_state() -> Dict[str, Any]:
    """Return current warmup state for health checks"""
    return _warmup_state.copy()

def _preload_embedder() -> bool:
    """Preload the SentenceTransformer model and run a warmup encode"""
    try:
        logger.info({"event": "embedder_preload_started"})
        start_time = time.time()
        
        # Force model to load by importing and using _get_model
        from ingestion.embed import _get_model, is_model_loaded
        
        # Check if already loaded (in case of multiple startup calls)
        if is_model_loaded():
            logger.info({"event": "embedder_already_loaded"})
            _warmup_state["embedder_loaded"] = True
            return True
            
        model = _get_model()
        
        # Run warmup encode using the exact same code path as retrieval
        logger.info({"event": "embedder_warmup_encode_started"})
        from ingestion.embed import embed_texts
        
        # Use a more representative warmup text that exercises the model fully
        warmup_texts = [
            "hello world",
            "This is a longer test sentence to ensure the model is fully warmed up and ready for production queries with various lengths and complexities."
        ]
        # Use the same embed_texts function that retrieval_service uses
        embeddings = embed_texts(warmup_texts)
        
        # Also warm up the retrieval service cache by calling embed_query directly
        from service.retrieval_service import embed_query
        _ = embed_query("warmup query")
        
        logger.info({
            "event": "embedder_warmup_encode_completed",
            "warmup_texts_count": len(warmup_texts),
            "embedding_dimension": len(embeddings[0]) if embeddings and embeddings[0] else 0
        })
        
        duration = time.time() - start_time
        logger.info({
            "event": "embedder_preload_completed", 
            "duration_seconds": round(duration, 2)
        })
        emit_event("embedder_preloaded", {"duration_seconds": duration})
        
        _warmup_state["embedder_loaded"] = True
        return True
        
    except Exception as e:
        logger.error({
            "event": "embedder_preload_failed",
            "error": str(e),
            "message": "Embedder will be loaded on first request"
        })
        emit_event("embedder_preload_failed", {"error": str(e)[:200]})
        return False

def _warm_vector_store() -> bool:
    """Initialize Chroma client and collection, run dummy query to warm index"""
    try:
        logger.info({"event": "vectorstore_warmup_started"})
        start_time = time.time()
        
        # Force client and collection to initialize
        from vectorstore.chroma_store import _get_client, _get_collection, is_client_loaded, is_collection_loaded
        
        # Check if already loaded (in case of multiple startup calls)
        if is_client_loaded() and is_collection_loaded():
            logger.info({"event": "vectorstore_already_loaded"})
            # Still need to get docs count
            collection = _get_collection()
            _warmup_state["collection_docs_count"] = collection.count()
            _warmup_state["index_warmed"] = True
            return True
        
        client = _get_client()
        collection = _get_collection()
        
        # Get collection stats
        docs_count = collection.count()
        _warmup_state["collection_docs_count"] = docs_count
        
        # Run dummy query to warm index pages if we have documents
        if docs_count > 0:
            logger.info({"event": "vectorstore_warmup_query_started", "docs_count": docs_count})
            
            # Create a dummy embedding vector (BGE-m3 has 1024 dimensions)
            dummy_embedding = [0.0] * 1024
            _ = collection.query(
                query_embeddings=[dummy_embedding], 
                n_results=min(1, docs_count),
                include=["metadatas", "distances"]
            )
            
        duration = time.time() - start_time
        logger.info({
            "event": "vectorstore_warmup_completed",
            "duration_seconds": round(duration, 2),
            "docs_count": docs_count
        })
        emit_event("vectorstore_warmed", {
            "duration_seconds": duration,
            "docs_count": docs_count
        })
        
        _warmup_state["index_warmed"] = True
        return True
        
    except Exception as e:
        logger.error({
            "event": "vectorstore_warmup_failed",
            "error": str(e),
            "message": "Vector store will be initialized on first request"
        })
        emit_event("vectorstore_warmup_failed", {"error": str(e)[:200]})
        return False

async def startup_warmup():
    """Main startup warmup routine - preload embedder and warm vector store"""
    logger.info({"event": "startup_warmup_initiated"})
    emit_event("startup_warmup_initiated", {})
    
    total_start_time = time.time()
    
    # Step 1: Preload embedder
    embedder_success = _preload_embedder()
    
    # Step 2: Warm vector store  
    vectorstore_success = _warm_vector_store()
    
    # Record completion
    total_duration = time.time() - total_start_time
    _warmup_state["warmup_duration_seconds"] = round(total_duration, 2)
    _warmup_state["warmup_completed_at"] = time.time()
    
    success_count = sum([embedder_success, vectorstore_success])
    logger.info({
        "event": "startup_warmup_completed",
        "total_duration_seconds": _warmup_state["warmup_duration_seconds"],
        "embedder_loaded": _warmup_state["embedder_loaded"],
        "index_warmed": _warmup_state["index_warmed"],
        "collection_docs_count": _warmup_state["collection_docs_count"],
        "components_warmed": f"{success_count}/2"
    })
    
    emit_event("startup_warmup_completed", {
        "total_duration_seconds": _warmup_state["warmup_duration_seconds"],
        "components_warmed": success_count,
        "embedder_loaded": _warmup_state["embedder_loaded"],
        "index_warmed": _warmup_state["index_warmed"]
    })
