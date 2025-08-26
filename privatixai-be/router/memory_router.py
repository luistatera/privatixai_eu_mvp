"""
Memory Router - API endpoints for memory/knowledge management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging
from vectorstore.chroma_store import get_stats
from service.retrieval_service import retrieve
from router import privacy_router

 # License checks are out of scope for v1.0

logger = logging.getLogger(__name__)
router = APIRouter()

 # License service dependency removed for v1.0

@router.get("/search")
async def search_memory(
    query: str,
    k: int = 8,
):
    """Search through stored memories and return top-k with snippets and citations."""
    try:
        logger.info({"event": "search_requested"})
        results = retrieve(query, k)
        logger.info({"event": "search_completed", "count": len(results)})
        return results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/stats")
async def get_memory_stats():
    """Get memory storage statistics"""
    stats = get_stats()
    return {
        "files": stats.get("files"),
        "chunks": stats.get("chunks", 0),
        "total_size_mb": stats.get("total_size_mb"),
        "last_updated": stats.get("last_updated"),
    }

@router.post("/export")
async def export_memory(background_tasks: BackgroundTasks):
    return await privacy_router.export_data(background_tasks)

@router.delete("/purge")
async def purge_memory():
    return await privacy_router.purge_vault()
