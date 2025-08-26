"""
Retrieval Service - embeds queries, searches vector store, assembles snippets

Contracts:
- embed_query(query: str) -> List[float]
- search_top_k(query: str, k: int) -> List[Dict]
- assemble_snippet(hit: Dict) -> str
- retrieve(query: str, k: int) -> List[Dict]
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from pathlib import Path

from config.settings import settings
from functools import lru_cache
from datetime import timedelta, datetime
from ingestion.embed import embed_texts, embed_queries
from service.encryption_service import decrypt_file
from vectorstore.chroma_store import query as vs_query, get_stats
from utils.telemetry import emit_event
import math


logger = logging.getLogger(__name__)


# Query classification types
class QueryType:
    FACTOID = "factoid"
    SECTION_SUMMARY = "section_summary"
    BROAD_SUMMARY = "broad_summary"
    COMPARE = "compare"
    FILTERING = "filtering"
    MULTI_DOC = "multi_doc"
    DEFAULT = "default"


# Section terms for detecting structured document queries
SECTION_TERMS = {
    "timeline", "schedule", "goal", "goals", "requirements",
    "deliverables", "resources", "evaluation", "conclusion", 
    "benefits", "overview", "introduction", "summary",
    "methodology", "approach", "implementation", "results"
}


def classify_query_complex(query: str, has_history: bool = False, targeted_docs: int = 1) -> str:
    """
    Complexity-aware query classification with better intent detection.
    
    Returns: factoid, section_summary, broad_summary, compare, filtering, multi_doc, or default
    """
    query_lower = query.lower().strip()
    tokens = query_lower.split()
    
    # Basic complexity signals
    is_long = len(tokens) > 12
    has_sections = any(term in query_lower for term in SECTION_TERMS)
    has_compare = any(term in query_lower for term in ["compare", " vs ", "versus", "pros and cons", "difference"])
    has_operators = any(op in query_lower for op in [">", "<", " between ", "%", " since ", " before ", " after "]) or any(char.isdigit() for char in query_lower)
    is_multi_doc = targeted_docs is None or targeted_docs > 1
    
    # Multi-entity detection (≥2 capitalized terms)
    import re
    capitalized_terms = re.findall(r'\b[A-Z][a-zA-Z]+\b', query)
    multi_entity = len(capitalized_terms) >= 2
    
    # Classification logic (order matters - most specific first)
    if has_compare or multi_entity:
        return QueryType.COMPARE
    
    if has_sections and is_long:
        return QueryType.SECTION_SUMMARY
    
    if is_long and not has_operators and (has_sections or multi_entity):
        return QueryType.BROAD_SUMMARY
    
    if has_operators:
        return QueryType.FILTERING
    
    if is_multi_doc:
        return QueryType.MULTI_DOC
    
    # Factoid: short, specific, no complex indicators
    if len(tokens) <= 8 and not has_sections and not has_compare and not multi_entity:
        return QueryType.FACTOID
    
    return QueryType.DEFAULT


def classify_query(query: str) -> str:
    """
    Backward compatibility wrapper for simple classification.
    Maps complex types back to simple types for existing code.
    """
    complex_type = classify_query_complex(query)
    
    # Map complex types to simple types for backward compatibility
    mapping = {
        QueryType.FACTOID: "factoid",
        QueryType.SECTION_SUMMARY: "summary", 
        QueryType.BROAD_SUMMARY: "summary",
        QueryType.COMPARE: "summary",
        QueryType.FILTERING: "default",
        QueryType.MULTI_DOC: "summary",
        QueryType.DEFAULT: "default"
    }
    
    return mapping.get(complex_type, "default")


def get_section_boost_terms(query: str) -> List[str]:
    """
    Extract section terms from query for biasing retrieval.
    Returns list of section terms that should be boosted.
    """
    query_lower = query.lower()
    found_terms = []
    
    for term in SECTION_TERMS:
        if term in query_lower:
            found_terms.append(term)
    
    return found_terms


def calculate_dynamic_k_complex(corpus_size: int, query_class: str, targeted_docs: int = 1, requested_k: Optional[int] = None) -> Dict[str, Any]:
    """
    Complexity-aware k calculation with MMR lambda and reranking parameters.
    
    Returns dict with k, keep_top_m, mmr_lambda, per_doc_quota based on query complexity.
    """
    if requested_k is not None and requested_k > 0:
        # User explicitly requested k, respect it but apply bounds
        k = max(6, min(requested_k, 32))
        return {"k": k, "keep_top_m": 10, "mmr_lambda": 0.4, "per_doc_quota": None}
    
    if corpus_size <= 0:
        return {"k": 8, "keep_top_m": 8, "mmr_lambda": 0.4, "per_doc_quota": None}
    
    # Base calculation with updated bounds
    k_base = max(6, min(round(2 * math.sqrt(corpus_size)), 24))
    
    # Query class adjustments (following the feedback policy)
    if query_class == QueryType.FACTOID:
        k = max(k_base - 2, 6)
        m, lam = 8, 0.5
    elif query_class == QueryType.SECTION_SUMMARY:
        k = min(k_base + 4, 32)
        m, lam = 10, 0.4
    elif query_class == QueryType.BROAD_SUMMARY:
        k = min(k_base + 6, 32)
        m, lam = 12, 0.35
    elif query_class == QueryType.COMPARE:
        k = min(k_base + 6, 32)
        m, lam = 12, 0.35
    elif query_class == QueryType.FILTERING:
        k = k_base
        m, lam = 9, 0.45
    elif query_class == QueryType.MULTI_DOC:
        k = min(k_base + 4, 28)
        m, lam = 12, 0.35
    else:  # DEFAULT
        k = k_base
        m, lam = 10, 0.4
    
    # Ensure k doesn't exceed corpus size
    k = min(k, corpus_size)
    
    # Per-doc quota for multi-doc queries
    per_doc_quota = None
    if targeted_docs and targeted_docs > 1:
        per_doc_quota = max(2, (k + targeted_docs - 1) // targeted_docs)  # ceil division
        k = min(per_doc_quota * targeted_docs, k)  # Don't exceed original k
    
    result = {
        "k": k,
        "keep_top_m": m,
        "mmr_lambda": lam,
        "per_doc_quota": per_doc_quota,
        "base_k": k_base,
        "query_class": query_class
    }
    
    logger.info({
        "event": "complex_k_calculated",
        "corpus_size": corpus_size,
        "query_class": query_class,
        "targeted_docs": targeted_docs,
        **result
    })
    
    return result


def calculate_dynamic_k(corpus_size: int, query_type: str, requested_k: Optional[int] = None) -> int:
    """
    Backward compatibility wrapper for simple k calculation.
    """
    # Map simple types to complex types for calculation
    type_mapping = {
        "factoid": QueryType.FACTOID,
        "summary": QueryType.BROAD_SUMMARY,
        "default": QueryType.DEFAULT
    }
    
    complex_type = type_mapping.get(query_type, QueryType.DEFAULT)
    result = calculate_dynamic_k_complex(corpus_size, complex_type, 1, requested_k)
    
    return result["k"]


_EMBED_CACHE_TTL_SECONDS = settings.CACHE_TTL_SECONDS if settings.ENABLE_MEMORY_CACHE else 0
_embed_cache: Dict[str, tuple[datetime, List[float]]] = {}


def _cache_get(key: str) -> List[float] | None:
    if _EMBED_CACHE_TTL_SECONDS <= 0:
        return None
    item = _embed_cache.get(key)
    if not item:
        return None
    ts, vec = item
    if (datetime.utcnow() - ts).total_seconds() > _EMBED_CACHE_TTL_SECONDS:
        _embed_cache.pop(key, None)
        return None
    return vec


def _cache_put(key: str, value: List[float]) -> None:
    if _EMBED_CACHE_TTL_SECONDS <= 0:
        return
    _embed_cache[key] = (datetime.utcnow(), value)


def embed_query(query: str) -> List[float]:
    """Return a single embedding vector for the query string, with simple TTL cache."""
    cached = _cache_get(query)
    if cached is not None:
        return cached
    # Use BGE-m3 recommended query prefix and normalized embeddings
    vectors = embed_queries([query])
    vec = vectors[0] if vectors else []
    _cache_put(query, vec)
    return vec


def search_top_k(query: str, k: int = 8) -> List[Dict]:
    """Search vectorstore for top-k hits with metadata and scores."""
    embedding = embed_query(query)
    if not embedding:
        return []
    hits = vs_query(embedding=embedding, k=k)
    try:
        # Lightweight instrumentation for debug panels
        logger.info({
            "event": "vector_query_executed",
            "requested_k": k,
            "returned": len(hits),
            "query_norm": round(sum(x*x for x in embedding) ** 0.5, 4)
        })
    except Exception:
        pass
    return hits


def _safe_slice_text(text: str, start_idx: int, end_idx: int, window: int | None = None) -> str:
    """
    Build a snippet window around [start_idx, end_idx] within the given text.
    Indices are best-effort and may refer to original doc bounds; we clamp safely.
    """
    n = len(text)
    if n == 0:
        return ""
    # Effective window from settings when not provided
    w = window or settings.SNIPPET_WINDOW_CHARS
    # Clamp bounds
    start_idx = max(0, min(start_idx, n - 1))
    end_idx = max(start_idx + 1, min(end_idx, n))
    # Center window around the middle of [start_idx, end_idx]
    mid = (start_idx + end_idx) // 2
    left = max(0, mid - w)
    right = min(n, mid + w)
    snippet = text[left:right]
    # Add ellipses when truncated
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < n else ""
    return f"{prefix}{snippet}{suffix}"


def assemble_snippet(hit: Dict) -> str:
    """
    Given a hit with metadata including chunk_id/start/end, decrypt the chunk
    and return a bounded snippet string.
    """
    try:
        chunk_id = hit.get("chunk_id") or hit.get("metadata", {}).get("chunk_id")
        start = hit.get("start") if isinstance(hit.get("start"), int) else hit.get("metadata", {}).get("start", 0)
        end = hit.get("end") if isinstance(hit.get("end"), int) else hit.get("metadata", {}).get("end", 0)
        if not chunk_id:
            return ""
        path: Path = settings.CHUNKS_PATH / f"{chunk_id}.enc"
        blob = decrypt_file(path)
        text = blob.decode("utf-8", errors="ignore")
        return _safe_slice_text(text, 0, len(text)) if (start is None or end is None) else _safe_slice_text(text, start, end)
    except Exception:
        return ""


def _apply_filters_and_boosts(
    hits: List[Dict],
    *,
    file_boosts: Optional[Dict[str, float]] = None,
    file_filter: Optional[Dict[str, List[str]]] = None,
    section_boost_terms: Optional[List[str]] = None,
) -> List[Dict]:
    """Filter hits by file_ids/chunk_ids and apply boosts (file and section-based)."""
    file_boosts = file_boosts or {}
    section_boost_terms = section_boost_terms or []
    filtered: List[Dict] = []
    allowed_files = set((file_filter or {}).get("file_ids" or [], [])) if file_filter else set()
    allowed_chunks = set((file_filter or {}).get("chunk_ids" or [], [])) if file_filter else set()

    for h in hits:
        md = h.get("metadata", {})
        file_id = md.get("file_id")
        chunk_id = md.get("chunk_id")
        
        # Apply filters
        if allowed_files and file_id not in allowed_files:
            continue
        if allowed_chunks and chunk_id not in allowed_chunks:
            continue
        
        score = float(h.get("score", 0.0))
        
        # Apply file boosts
        file_boost = float(file_boosts.get(file_id, 1.0)) if file_id else 1.0
        score = score * file_boost
        
        # Apply section biasing if we have section terms
        if section_boost_terms:
            section_boost = _calculate_section_boost(md, section_boost_terms)
            score = score + section_boost  # Additive boost for sections
        
        h2 = dict(h)
        h2["score"] = score
        filtered.append(h2)
    
    return filtered


def _calculate_section_boost(metadata: Dict, section_terms: List[str]) -> float:
    """
    Calculate section boost score based on metadata and detected section terms.
    
    Boosts chunks that appear to be from relevant sections by +0.1 per matched term.
    """
    if not section_terms:
        return 0.0
    
    boost_score = 0.0
    
    # Check if chunk content contains section-like headers
    # This is a simple heuristic - in practice you might want to use 
    # document structure metadata if available
    chunk_text = ""
    
    # Try to get chunk text for analysis (this is lightweight)
    try:
        # We could load the chunk text here, but for performance,
        # let's use a simpler approach based on available metadata
        file_name = metadata.get("file_name", "").lower()
        
        # Simple heuristic: if filename contains section terms, boost it
        for term in section_terms:
            if term in file_name:
                boost_score += 0.05  # Smaller boost for filename matches
        
        # TODO: In a more sophisticated implementation, you could:
        # 1. Load the actual chunk text and check for header patterns
        # 2. Use document structure metadata if available
        # 3. Implement fuzzy matching for section headers
        
    except Exception:
        # If anything fails, no boost
        pass
    
    return min(boost_score, 0.15)  # Cap the boost to prevent over-boosting


def _diversify_by_file(hits: List[Dict], k: int) -> List[Dict]:
    """Greedy diversification favoring different files before filling remaining slots by score."""
    if k <= 0:
        return []
    # Sort by score desc
    sorted_hits = sorted(hits, key=lambda h: float(h.get("score", 0.0)), reverse=True)
    selected: List[Dict] = []
    used_files: set[str] = set()
    for h in sorted_hits:
        md = h.get("metadata", {})
        fid = md.get("file_id")
        if fid and fid not in used_files:
            selected.append(h)
            used_files.add(fid)
            if len(selected) >= k:
                return selected
    # Fill remaining by score
    for h in sorted_hits:
        if h in selected:
            continue
        selected.append(h)
        if len(selected) >= k:
            break
    return selected


def retrieve(
    query: str,
    k: int = 8,
    *,
    file_boosts: Optional[Dict[str, float]] = None,
    file_filter: Optional[Dict[str, List[str]]] = None,
    overfetch_k: int = 32,
    enable_smart_k: bool = True,
    enable_retry: bool = True,
) -> List[Dict]:
    """
    Enhanced retrieval with dynamic k and confidence-based retry.
    
    Args:
        query: Search query
        k: Requested k value (can be overridden by smart_k)
        file_boosts: Score boosts per file_id
        file_filter: Filter by file_ids/chunk_ids
        overfetch_k: Overfetch factor for diversification
        enable_smart_k: Whether to use dynamic k calculation
        enable_retry: Whether to retry with larger k if results are poor
    
    Returns normalized dicts with keys:
    { chunk_id, file_id, file_name, file_ext, start, end, score, snippet }
    """
    logger.info({"event": "retrieval_started", "original_k": k})
    emit_event("retrieval_started", {"k": k})
    
    # Step 1: Enhanced query analysis and k calculation
    actual_k = k
    query_type = QueryType.DEFAULT
    section_boost_terms = []
    per_doc_quota = None
    
    if enable_smart_k:
        try:
            # Get corpus size from vectorstore
            stats = get_stats()
            corpus_size = stats.get("chunks", 0)
            
            # Determine targeted docs count for multi-doc logic
            targeted_docs = 1
            if file_filter and file_filter.get("file_ids"):
                targeted_docs = len(file_filter["file_ids"])
            elif not file_filter:
                targeted_docs = None  # No filter = all docs
            
            # Use complex query classification
            complex_query_type = classify_query_complex(query, False, targeted_docs or 1)
            query_type = classify_query(query)  # For backward compatibility
            
            # Get section boost terms
            section_boost_terms = get_section_boost_terms(query)
            
            # Calculate complex k parameters
            k_params = calculate_dynamic_k_complex(
                corpus_size, complex_query_type, targeted_docs or 1, k if k != 8 else None
            )
            
            actual_k = k_params["k"]
            per_doc_quota = k_params.get("per_doc_quota")
            
            logger.info({
                "event": "smart_k_complex_applied",
                "original_k": k,
                "actual_k": actual_k,
                "query_type": query_type,
                "complex_query_type": complex_query_type,
                "corpus_size": corpus_size,
                "section_boost_terms": section_boost_terms,
                "per_doc_quota": per_doc_quota,
                "targeted_docs": targeted_docs
            })
            
        except Exception as e:
            logger.warning({"event": "smart_k_failed", "error": str(e), "fallback_k": k})
            actual_k = k
    
    # Step 2: Perform initial retrieval with enhanced features
    results = _perform_retrieval(
        query, actual_k, file_boosts, file_filter, overfetch_k,
        section_boost_terms, per_doc_quota
    )
    
    # Step 3: Check if retry is needed and beneficial
    # If strict filters led to zero hits, try a global search once as a safe fallback
    if not results and file_filter:
        logger.info({
            "event": "retrieval_global_fallback",
            "reason": "zero_hits_with_filter",
            "had_filter": True
        })
        results = _perform_retrieval(
            query, max(actual_k, settings.RETRIEVAL_TOPK), file_boosts, None, overfetch_k,
            section_boost_terms, per_doc_quota
        )

    if enable_retry and _should_retry(results, actual_k):
        logger.info({
            "event": "retrieval_retry_triggered",
            "initial_results": len(results),
            "initial_k": actual_k
        })
        emit_event("retrieval_retry", {"initial_results": len(results)})
        
        # Retry with increased k (max 1.5x, capped at 32)
        retry_k = min(int(actual_k * 1.5), 32)
        retry_results = _perform_retrieval(
            query, retry_k, file_boosts, file_filter, overfetch_k,
            section_boost_terms, per_doc_quota
        )
        
        # Use retry results if they're better
        if len(retry_results) > len(results):
            results = retry_results
            logger.info({
                "event": "retrieval_retry_improved",
                "retry_results": len(retry_results),
                "retry_k": retry_k
            })
    
    logger.info({"event": "retrieval_completed", "final_results": len(results)})
    emit_event("retrieval_completed", {"results": len(results)})
    return results


def _mmr_rerank(hits: List[Dict], keep_top_n: int, lambda_param: float) -> List[Dict]:
    """Apply simple MMR (Maximal Marginal Relevance) on scores/embeddings if available.
    Assumes hits contain optional 'embedding' vectors in metadata; if not present, falls back to score-only.
    """
    if keep_top_n <= 0 or not hits:
        return []
    # If embeddings are not present, just take top-N by score
    import math
    scored = [
        (float(h.get("score", 0.0)), h)
        for h in hits
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    selected: List[Dict] = []
    if not settings.ENABLE_RERANKER:
        return [h for _, h in scored[:keep_top_n]]
    # Basic MMR using scores as relevance proxy; diversity via file_id uniqueness
    used_files: set[str] = set()
    for _, h in scored:
        fid = (h.get("metadata") or {}).get("file_id")
        # Reward new files to improve diversity
        diversity_bonus = 0.0 if (fid in used_files or fid is None) else 0.05
        h2 = dict(h)
        h2["score"] = float(h2.get("score", 0.0)) * (lambda_param) + diversity_bonus
        selected.append(h2)
        if fid:
            used_files.add(fid)
        if len(selected) >= keep_top_n:
            break
    # Sort final selection by score desc
    selected.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return selected


def _perform_retrieval(
    query: str,
    k: int,
    file_boosts: Optional[Dict[str, float]],
    file_filter: Optional[Dict[str, List[str]]],
    overfetch_k: int,
    section_boost_terms: Optional[List[str]] = None,
    per_doc_quota: Optional[int] = None
) -> List[Dict]:
    """Internal function to perform the actual retrieval logic with section biasing."""
    # Overfetch to allow diversification/pruning
    hits = search_top_k(query, max(k, overfetch_k))
    
    # Apply filters/boosts including section biasing
    hits = _apply_filters_and_boosts(
        hits, 
        file_boosts=file_boosts, 
        file_filter=file_filter,
        section_boost_terms=section_boost_terms
    )
    
    # Filter out low-confidence hits to avoid nonsense results  
    min_score = settings.RETRIEVAL_MIN_SCORE
    hits = [h for h in hits if float(h.get("score", 0.0)) >= float(min_score)]
    
    # Apply per-document quota if specified (for multi-doc diversity)
    if per_doc_quota and per_doc_quota > 0:
        hits = _apply_per_doc_quota(hits, per_doc_quota)
    
    # Diversify by file and optionally rerank (MMR)
    hits = _diversify_by_file(hits, max(k, settings.RETRIEVAL_TOPK))
    if settings.ENABLE_RERANKER:
        hits = _mmr_rerank(hits, keep_top_n=settings.RERANK_KEEP_TOPN, lambda_param=settings.MMR_LAMBDA)
    
    results: List[Dict] = []
    for h in hits[:k]:
        md = h.get("metadata", {})
        norm = {
            "chunk_id": md.get("chunk_id"),
            "file_id": md.get("file_id"),
            "file_name": md.get("file_name"),
            "file_ext": md.get("file_ext"),
            "start": md.get("start"),
            "end": md.get("end"),
            "score": h.get("score"),
        }
        norm["snippet"] = assemble_snippet(norm)
        results.append(norm)
    
    return results


def _apply_per_doc_quota(hits: List[Dict], per_doc_quota: int) -> List[Dict]:
    """
    Apply per-document quota to ensure diversity across multiple documents.
    
    Groups hits by file_id and limits each file to per_doc_quota results,
    taking the highest scoring ones from each file.
    """
    if per_doc_quota <= 0:
        return hits
    
    # Group hits by file_id
    file_groups: Dict[str, List[Dict]] = {}
    for hit in hits:
        file_id = hit.get("metadata", {}).get("file_id", "unknown")
        if file_id not in file_groups:
            file_groups[file_id] = []
        file_groups[file_id].append(hit)
    
    # Sort each group by score (descending) and take top per_doc_quota
    limited_hits = []
    for file_id, file_hits in file_groups.items():
        # Sort by score descending
        file_hits.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
        # Take up to per_doc_quota from this file
        limited_hits.extend(file_hits[:per_doc_quota])
    
    # Sort final results by score
    limited_hits.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    
    return limited_hits


def _should_retry(results: List[Dict], k: int) -> bool:
    """
    Determine if retrieval should be retried based on result quality.
    
    Retry if:
    - Less than 3 results found
    - All results have low confidence scores (< 0.3)
    - No diversity in results (all from same file)
    """
    if len(results) < 3:
        return True
    
    # Check if all scores are low
    scores = [float(r.get("score", 0.0)) for r in results]
    if all(score < 0.3 for score in scores):
        return True
    
    # Check diversity - all results from same file is bad
    file_ids = set(r.get("file_id") for r in results)
    if len(file_ids) <= 1 and len(results) >= 3:
        return True
    
    return False


def invalidate_retrieval_cache():
    """Invalidate simple retrieval caches after ingestion events."""
    _embed_cache.clear()


