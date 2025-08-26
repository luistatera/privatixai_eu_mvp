"""
Chat Models - Pydantic models for chat API (new flow: history + anchoring)
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class ChatRequest(BaseModel):
    """Request model for chat/ask endpoint (supports history and anchoring)."""
    prompt: str = Field(..., description="User's question or prompt")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Sampling temperature")
    k: Optional[int] = Field(None, description="Top-k retrieval results to include")
    conversation_id: Optional[str] = Field(None, description="Ephemeral conversation id")
    history: Optional[List[ChatMessage]] = Field(None, description="Recent chat history")
    anchor: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Anchoring filters: { file_ids: [], chunk_ids: [] }",
    )


class ChatAskResponse(BaseModel):
    """Response model for retrieval-augmented ask endpoint"""
    content: str = Field(..., description="LLM response content")
    citations: List[Dict[str, Any]] = Field(..., description="Citations metadata")
    query_type: Optional[str] = Field(None, description="Detected query type: factoid, summary, or default")
    retrieval_stats: Optional[Dict[str, Any]] = Field(None, description="Retrieval performance stats")
