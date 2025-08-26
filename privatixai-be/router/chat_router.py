"""
Chat Router - New RAG chat flow with CQR + anchoring + history (single path)
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
import logging
import json
import re
from pathlib import Path

from model.chat_models import (
    ChatRequest,
    ChatAskResponse,
)
from llm import llm_service
from service.retrieval_service import retrieve, classify_query, classify_query_complex
from service.cqr_service import rewrite_question, summarize_turn
from service.conversation_state import (
    get_state,
    update_citations,
    update_rolling_summary,
)
from config.settings import settings
from utils.telemetry import emit_event

logger = logging.getLogger(__name__)
router = APIRouter()

 # License checks are out of scope for v1.0

@router.post("/ask", response_model=ChatAskResponse)
async def ask_question(request: ChatRequest):
    """
    Retrieval-augmented chat with CQR and anchoring:
    - Rewrites question using short history
    - Applies optional anchors (request + pinned state)
    - Retrieves diversified citations
    - Builds context with system preamble + rolling summary + <sources>
    - Calls hosted LLM and returns { content, citations }
    """
    try:
        logger.info({
            "event": "chat_requested",
        })
        emit_event("chat_requested", {})

        # Step 0: Prepare state, history, and standalone question
        conv_id: Optional[str] = request.conversation_id
        state = get_state(conv_id) if conv_id else None
        standalone_question = await rewrite_question(request.history or [], request.prompt)
        


        # Helper: map filenames mentioned in prompt to file_ids
        def _extract_filenames(text: str) -> list[str]:
            if not text:
                return []
            pattern = re.compile(r"([\w\-. ]+\.(?:pdf|docx|txt|md))", re.IGNORECASE)
            return [m.group(1).strip() for m in pattern.finditer(text)]

        def _map_filenames_to_ids(names: list[str]) -> set[str]:
            file_ids: set[str] = set()
            if not names:
                return file_ids
            try:
                meta_dir: Path = settings.UPLOAD_PATH
                if meta_dir.exists():
                    lower_names = {n.lower() for n in names}
                    for meta_file in meta_dir.glob("*.meta"):
                        try:
                            data = json.loads(meta_file.read_text())
                            original = str(data.get("original_filename", "")).lower()
                            storage = str(data.get("storage_filename", "")).lower()
                            if original in lower_names or storage in lower_names:
                                fid = str(data.get("file_id", "")).strip()
                                if fid:
                                    file_ids.add(fid)
                        except Exception:
                            continue
            except Exception:
                pass
            return file_ids

        # Step 1: Build filters/boosts from anchors and pinned state
        anchor = request.anchor or {}
        req_file_ids = set(anchor.get("file_ids", []) or [])
        req_chunk_ids = set(anchor.get("chunk_ids", []) or [])
        pinned_files = set(state.pinned_file_ids) if state else set()
        pinned_chunks = set(state.pinned_chunk_ids) if state else set()
        # Request anchors take precedence; fallback to pinned if empty
        filter_file_ids = req_file_ids or pinned_files
        filter_chunk_ids = req_chunk_ids or pinned_chunks
        file_filter: Optional[Dict[str, list[str]]] = None
        if filter_file_ids or filter_chunk_ids:
            file_filter = {
                "file_ids": list(filter_file_ids),
                "chunk_ids": list(filter_chunk_ids),
            }
        # Boost pinned/request-anchored files modestly
        file_boosts: Dict[str, float] = {fid: 1.5 for fid in (filter_file_ids or [])}

        # Filename hinting: if the user mentioned a specific filename, prefer soft boosting over hard filter
        mentioned = _extract_filenames(request.prompt) + _extract_filenames(standalone_question)
        hinted_ids = _map_filenames_to_ids(mentioned)
        if hinted_ids:
            # Do NOT constrain; just boost hinted files so global search can still find content
            for fid in hinted_ids:
                file_boosts[fid] = max(file_boosts.get(fid, 0.0), 2.0)



        # Step 2: Retrieve top-k snippets (allow override via request.k)
        top_k_default = settings.RETRIEVAL_TOPK
        top_k = request.k if isinstance(request.k, int) and request.k > 0 else top_k_default
        
        # Enhanced query classification
        query_type = classify_query(standalone_question)  # For backward compatibility
        
        # Determine targeted docs for complex classification
        targeted_docs = 1
        if filter_file_ids:
            targeted_docs = len(filter_file_ids)
        elif not file_filter:
            targeted_docs = None  # No filter = all docs
            
        complex_query_type = classify_query_complex(standalone_question, bool(request.history), targeted_docs or 1)
        
        # Use simple retrieve like memory search API (fixed)
        citations = retrieve(standalone_question, k=top_k)
        logger.info({"event": "debug_citations_found", "count": len(citations), "has_content": bool(citations)})

        # Fallback: if CQR rewrite gets no results, try original question
        if not citations and standalone_question != request.prompt:
            logger.info({
                "event": "cqr_fallback",
                "rewritten_failed": standalone_question,
                "trying_original": request.prompt,
            })
            # Use simple retrieve like memory search API (fixed)
            citations = retrieve(request.prompt, k=top_k)
            # Use original question for LLM context if fallback worked
            if citations:
                standalone_question = request.prompt

        # If no citations found, we'll still answer conversationally below; no strict filename gating

        # If no citations found, fall back to a general conversational answer (no sources)
        if not citations:
            system_preamble_no_sources = (
                "You are a helpful private assistant. No private memory sources matched this question. "
                "Answer conversationally and helpfully without citing sources."
            )
            rolling = state.rolling_summary if state and state.rolling_summary else ""
            rolling_block = f"\n<rolling_summary>\n{rolling}\n</rolling_summary>\n" if rolling else ""
            no_sources_context = f"{system_preamble_no_sources}{rolling_block}"

            emit_event("chat_llm_call", {"citations": 0})
            response = await llm_service.ask_llm(
                prompt=standalone_question,
                context=no_sources_context,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )

            return {
                "content": response.content,
                "citations": [],
                "query_type": complex_query_type,
                "retrieval_stats": {
                    "total_citations": 0,
                    "k_used": top_k,
                    "query_classification": query_type,
                    "complex_query_classification": complex_query_type,
                    "has_retry": False,
                    "targeted_docs": targeted_docs
                }
            }

        # Step 3: Auto-anchoring: lightly boost last citations if enabled and no explicit anchors were provided
        if settings.ENABLE_AUTO_ANCHORING and not (request.anchor and (request.anchor.get("file_ids") or request.anchor.get("chunk_ids"))):
            try:
                if state and state.last_citations:
                    auto_chunk_ids = [c.get("chunk_id") for c in state.last_citations[: settings.ANCHOR_MAX_CHUNKS] if c.get("chunk_id")]
                    if auto_chunk_ids:
                        # merge into file_filter and re-retrieve with bias
                        filter_chunk_ids = set(filter_chunk_ids) | set(auto_chunk_ids) if filter_chunk_ids else set(auto_chunk_ids)
                        file_filter = {"file_ids": list(filter_file_ids), "chunk_ids": list(filter_chunk_ids)} if (filter_file_ids or filter_chunk_ids) else None
                        citations = retrieve(standalone_question, k=top_k, file_filter=file_filter)
            except Exception:
                pass

        # Step 4: Build prompt with transient snippets and optional rolling summary
        snippets_block = "\n\n".join(
            [
                f"<source id=\"{c['chunk_id']}\" file=\"{c['file_name']}\">\n{c['snippet']}\n</source>"
                for c in citations if c.get("snippet")
            ]
        )
        # Cap total context size to avoid slow hosted calls
        if len(snippets_block) > settings.MAX_CONTEXT_CHARS:
            snippets_block = snippets_block[: settings.MAX_CONTEXT_CHARS]

        system_preamble = (
            "You are a helpful private memory assistant. Use the information from the provided sources to answer the user's question thoroughly and accurately. "
            "Always cite the sources by file name when you use information from them. "
            "If the sources contain relevant information, provide a comprehensive answer based on that content. "
            "Only say 'I couldn't find that in your memory' if the sources truly contain no relevant information to answer the question."
        )
        rolling = state.rolling_summary if state and state.rolling_summary else ""
        rolling_block = f"\n<rolling_summary>\n{rolling}\n</rolling_summary>\n" if rolling else ""
        context = f"{system_preamble}{rolling_block}\n<sources>\n{snippets_block}\n</sources>"

        # Step 4: Call LLM with context
        emit_event("chat_llm_call", {"citations": len(citations)})
        response = await llm_service.ask_llm(
            prompt=standalone_question,
            context=context,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        result = {
            "content": response.content,
            "citations": [
                {
                    "chunk_id": c.get("chunk_id"),
                    "file_id": c.get("file_id"),
                    "file_name": c.get("file_name"),
                    "start": c.get("start"),
                    "end": c.get("end"),
                    "score": c.get("score"),
                    "snippet": c.get("snippet"),
                }
                for c in citations
            ],
            "query_type": complex_query_type,
            "retrieval_stats": {
                "total_citations": len(citations),
                "k_used": top_k,
                "query_classification": query_type,
                "complex_query_classification": complex_query_type,
                "has_retry": len(citations) > top_k,  # Simple heuristic
                "targeted_docs": targeted_docs
            }
        }

        # Step 5: Update ephemeral conversation state
        try:
            update_citations(conv_id, result["citations"])  # type: ignore[arg-type]
            summary = await summarize_turn(request.history or [], result["content"])
            update_rolling_summary(conv_id, summary)
        except Exception:
            # Do not fail the request on state updates
            pass

        return result

    except Exception as e:
        # In development, print full stack trace to the terminal without logging user content
        logger.exception("Chat request failed")
        emit_event("chat_error", {"error": str(e)[:200]})
        # Map secure transport failures to a clear UX message without leaking details
        if str(e) == "secure_transport_failed":
            raise HTTPException(status_code=503, detail="Nothing was sent: secure transport unavailable")
        raise HTTPException(status_code=500, detail="Chat failed")

@router.post("/ask/stream")
async def ask_question_stream(request: ChatRequest):
    """
    Streaming retrieval-augmented chat with CQR and anchoring.
    Returns Server-Sent Events stream with { type: "citations" | "content" | "done", data: ... }
    """
    try:
        logger.info({
            "event": "chat_stream_requested",
        })
        emit_event("chat_stream_requested", {})

        async def generate_stream():
            try:
                # Step 0: Prepare state, history, and standalone question
                conv_id: Optional[str] = request.conversation_id
                state = get_state(conv_id) if conv_id else None
                standalone_question = await rewrite_question(request.history or [], request.prompt)
                


                # Step 1: Build filters/boosts
                anchor = request.anchor or {}
                req_file_ids = set(anchor.get("file_ids", []) or [])
                req_chunk_ids = set(anchor.get("chunk_ids", []) or [])
                pinned_files = set(state.pinned_file_ids) if state else set()
                pinned_chunks = set(state.pinned_chunk_ids) if state else set()
                filter_file_ids = req_file_ids or pinned_files
                filter_chunk_ids = req_chunk_ids or pinned_chunks
                file_filter: Optional[Dict[str, list[str]]] = None
                if filter_file_ids or filter_chunk_ids:
                    file_filter = {
                        "file_ids": list(filter_file_ids),
                        "chunk_ids": list(filter_chunk_ids),
                    }
                file_boosts: Dict[str, float] = {fid: 1.5 for fid in (filter_file_ids or [])}

                # Filename hinting: if the user mentioned a specific filename, constrain retrieval
                def _extract_filenames(text: str) -> list[str]:
                    import re
                    return re.findall(r'\b\S+\.(?:docx?|pdf|txt|md)\b', text)

                def _map_filenames_to_ids(names: list[str]) -> set[str]:
                    if not names:
                        return set()
                    file_ids = set()
                    try:
                        from pathlib import Path
                        import json
                        from config.settings import settings
                        meta_dir = Path(settings.DATA_PATH) / "uploads"
                        if meta_dir.exists():
                            lower_names = {n.lower() for n in names}
                            for meta_file in meta_dir.glob("*.meta"):
                                try:
                                    data = json.loads(meta_file.read_text())
                                    original = str(data.get("original_filename", "")).lower()
                                    storage = str(data.get("storage_filename", "")).lower()
                                    if original in lower_names or storage in lower_names:
                                        fid = str(data.get("file_id", "")).strip()
                                        if fid:
                                            file_ids.add(fid)
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    return file_ids

                mentioned = _extract_filenames(request.prompt) + _extract_filenames(standalone_question)
                hinted_ids = _map_filenames_to_ids(mentioned)
                if hinted_ids:
                    filter_file_ids = set(filter_file_ids) | hinted_ids if filter_file_ids else hinted_ids
                    file_filter = {"file_ids": list(filter_file_ids), "chunk_ids": list(filter_chunk_ids)} if filter_chunk_ids else {"file_ids": list(filter_file_ids)}
                    # Light boost to hinted files
                    for fid in hinted_ids:
                        file_boosts[fid] = max(file_boosts.get(fid, 0.0), 2.0)

                # Step 2: Retrieve
                top_k = request.k if isinstance(request.k, int) and request.k > 0 else 8
                
                # Enhanced query classification
                query_type = classify_query(standalone_question)  # For backward compatibility
                
                # Determine targeted docs for complex classification
                targeted_docs = 1
                if filter_file_ids:
                    targeted_docs = len(filter_file_ids)
                elif not file_filter:
                    targeted_docs = None  # No filter = all docs
                    
                complex_query_type = classify_query_complex(standalone_question, bool(request.history), targeted_docs or 1)
                
                # Use simple retrieve like memory search API (fixed)
                citations = retrieve(standalone_question, k=top_k)

                # Fallback: if CQR rewrite gets no results, try original question
                if not citations and standalone_question != request.prompt:
                    logger.info({
                        "event": "cqr_fallback_stream",
                        "rewritten_failed": standalone_question,
                        "trying_original": request.prompt,
                    })
                    # Use simple retrieve like memory search API (fixed)
                    citations = retrieve(request.prompt, k=top_k)
                    # Use original question for LLM context if fallback worked
                    if citations:
                        standalone_question = request.prompt

                # Send citations first with metadata
                citations_data = {
                    "citations": [
                        {
                            "chunk_id": c.get("chunk_id"),
                            "file_id": c.get("file_id"),
                            "file_name": c.get("file_name"),
                            "start": c.get("start"),
                            "end": c.get("end"),
                            "score": c.get("score"),
                            "snippet": c.get("snippet"),
                        }
                        for c in citations
                    ],
                    "query_type": complex_query_type,
                    "retrieval_stats": {
                        "total_citations": len(citations),
                        "k_used": top_k,
                        "query_classification": query_type,
                        "complex_query_classification": complex_query_type,
                        "has_retry": len(citations) > top_k,  # Simple heuristic
                        "targeted_docs": targeted_docs
                    }
                }
                
                yield f"data: {json.dumps({'type': 'citations', 'data': citations_data})}\n\n"

                # If no citations found and a filename was mentioned, do not hallucinate — return a clear message
                # No strict filename gating; fall through to no-sources conversational answer

                # If no citations found, fall back to a general conversational answer (no sources)
                if not citations:
                    system_preamble_no_sources = (
                        "You are a helpful private assistant. No private memory sources matched this question. "
                        "Answer conversationally and helpfully without citing sources."
                    )
                    rolling = state.rolling_summary if state and state.rolling_summary else ""
                    rolling_block = f"\n<rolling_summary>\n{rolling}\n</rolling_summary>\n" if rolling else ""
                    no_sources_context = f"{system_preamble_no_sources}{rolling_block}"

                    emit_event("chat_llm_stream", {"citations": 0})
                    collected: list[str] = []
                    async for chunk in llm_service.stream_completion(
                        prompt=standalone_question,
                        context=no_sources_context,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                    ):
                        if chunk:
                            collected.append(chunk)
                            yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"

                    # Signal completion
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
                    # Update state after streaming completes
                    try:
                        update_citations(conv_id, [])  # type: ignore[arg-type]
                        summary = await summarize_turn(request.history or [], "".join(collected))
                        update_rolling_summary(conv_id, summary)
                    except Exception:
                        pass
                    return

                # Step 3: Build prompt with transient snippets and optional rolling summary
                snippets_block = "\n\n".join(
                    [
                        f"<source id=\"{c['chunk_id']}\" file=\"{c['file_name']}\">\n{c['snippet']}\n</source>"
                        for c in citations if c.get("snippet")
                    ]
                )
                # Cap total context size to avoid slow hosted calls
                if len(snippets_block) > settings.MAX_CONTEXT_CHARS:
                    snippets_block = snippets_block[: settings.MAX_CONTEXT_CHARS]

                system_preamble = (
                    "You are a helpful private memory assistant. Use the information from the provided sources to answer the user's question thoroughly and accurately. "
                    "Always cite the sources by file name when you use information from them. "
                    "If the sources contain relevant information, provide a comprehensive answer based on that content. "
                    "Only say 'I couldn't find that in your memory' if the sources truly contain no relevant information to answer the question."
                )
                rolling = state.rolling_summary if state and state.rolling_summary else ""
                rolling_block = f"\n<rolling_summary>\n{rolling}\n</rolling_summary>\n" if rolling else ""
                context = f"{system_preamble}{rolling_block}\n<sources>\n{snippets_block}\n</sources>"

                # Step 3: Stream LLM response
                emit_event("chat_llm_stream", {"citations": len(citations)})
                collected: list[str] = []
                async for chunk in llm_service.stream_completion(
                    prompt=standalone_question,
                    context=context,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                ):
                    if chunk:  # Only send non-empty chunks
                        collected.append(chunk)
                        yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"

                # Signal completion
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                # Update state after streaming completes
                try:
                    update_citations(conv_id, citations_data)  # type: ignore[arg-type]
                    summary = await summarize_turn(request.history or [], "".join(collected))
                    update_rolling_summary(conv_id, summary)
                except Exception:
                    pass

            except Exception as e:
                logger.exception("Chat stream failed")
                emit_event("chat_stream_error", {"error": str(e)[:200]})
                # Send error in the stream
                error_msg = "Chat failed"
                if str(e) == "secure_transport_failed":
                    error_msg = "Nothing was sent: secure transport unavailable"
                yield f"data: {json.dumps({'type': 'error', 'data': error_msg})}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",  # Allow CORS for streaming
            }
        )

    except Exception as e:
        logger.exception("Chat stream setup failed")
        emit_event("chat_stream_setup_error", {"error": str(e)[:200]})
        raise HTTPException(status_code=500, detail="Chat stream setup failed")

@router.get("/health")
async def chat_health():
    """Check chat service health"""
    try:
        health = await llm_service.health_check()
        return {
            "status": "healthy" if health["overall"] else "unhealthy",
            "providers": health
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
