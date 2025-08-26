"""
Ephemeral Conversation State Service

Maintains in-memory, per-conversation state with TTL. Never persisted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any

from config.settings import settings


_DEFAULT_TTL_SECONDS: int = 2 * 60 * 60  # 2 hours


@dataclass
class ConversationState:
    conversation_id: str
    pinned_file_ids: Set[str] = field(default_factory=set)
    pinned_chunk_ids: Set[str] = field(default_factory=set)
    last_citations: List[Dict[str, Any]] = field(default_factory=list)
    rolling_summary: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()


_store: Dict[str, ConversationState] = {}
_ttl: int = _DEFAULT_TTL_SECONDS


def _expired(state: ConversationState) -> bool:
    return (datetime.utcnow() - state.updated_at) > timedelta(seconds=_ttl)


def get_state(conversation_id: Optional[str]) -> Optional[ConversationState]:
    if not conversation_id:
        return None
    state = _store.get(conversation_id)
    if state and _expired(state):
        _store.pop(conversation_id, None)
        return None
    if not state:
        state = ConversationState(conversation_id=conversation_id)
        _store[conversation_id] = state
    state.touch()
    return state


def pin_files(conversation_id: str, file_ids: List[str]) -> ConversationState:
    state = get_state(conversation_id)
    if not state:
        state = ConversationState(conversation_id=conversation_id)
        _store[conversation_id] = state
    for fid in file_ids:
        if isinstance(fid, str) and fid:
            state.pinned_file_ids.add(fid)
    state.touch()
    return state


def unpin_files(conversation_id: str, file_ids: List[str]) -> ConversationState:
    state = get_state(conversation_id)
    if not state:
        state = ConversationState(conversation_id=conversation_id)
        _store[conversation_id] = state
    for fid in file_ids:
        state.pinned_file_ids.discard(fid)
    state.touch()
    return state


def pin_chunks(conversation_id: str, chunk_ids: List[str]) -> ConversationState:
    state = get_state(conversation_id)
    if not state:
        state = ConversationState(conversation_id=conversation_id)
        _store[conversation_id] = state
    for cid in chunk_ids:
        if isinstance(cid, str) and cid:
            state.pinned_chunk_ids.add(cid)
    state.touch()
    return state


def unpin_chunks(conversation_id: str, chunk_ids: List[str]) -> ConversationState:
    state = get_state(conversation_id)
    if not state:
        state = ConversationState(conversation_id=conversation_id)
        _store[conversation_id] = state
    for cid in chunk_ids:
        state.pinned_chunk_ids.discard(cid)
    state.touch()
    return state


def update_citations(conversation_id: Optional[str], citations: List[Dict[str, Any]]) -> None:
    if not conversation_id:
        return
    state = get_state(conversation_id)
    if not state:
        return
    state.last_citations = citations
    state.touch()


def update_rolling_summary(conversation_id: Optional[str], summary: str) -> None:
    if not conversation_id:
        return
    state = get_state(conversation_id)
    if not state:
        return
    state.rolling_summary = summary or ""
    state.touch()


def set_ttl(seconds: int) -> None:
    global _ttl
    _ttl = max(60, int(seconds))



