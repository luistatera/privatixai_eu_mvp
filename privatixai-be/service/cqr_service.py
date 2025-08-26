"""
Conversational Query Rewriting (CQR) and concise rolling summary helpers.

Uses hosted LLM via llm_service with strict, privacy-aware prompts.
"""

from __future__ import annotations

from typing import List

from llm import llm_service, LLMError
from model.chat_models import ChatMessage
from config.settings import settings


def _truncate_history(history: List[ChatMessage], max_chars: int = 1200) -> List[ChatMessage]:
    if not history:
        return []
    result: List[ChatMessage] = []
    total = 0
    # Walk from the end (most recent) backwards
    for m in reversed(history):
        c = m.content or ""
        total += len(c)
        result.append(m)
        if total >= max_chars:
            break
    return list(reversed(result))


async def rewrite_question(history: List[ChatMessage] | None, question: str) -> str:
    if not history:
        return question
    trimmed = _truncate_history(history)
    history_text = "\n".join([f"{m.role}: {m.content}" for m in trimmed])
    system = (
        "Rewrite the user's question to be standalone and searchable, using the conversation history for context. "
        "Keep it concise and use simple, searchable terms. "
        "Do not add extra context or explanations. "
        "Return only the rewritten question."
    )
    context = f"{system}\n\n<short_history>\n{history_text}\n</short_history>"
    try:
        resp = await llm_service.ask_llm(prompt=question, context=context, max_tokens=128, temperature=0.0)
        text = (resp.content or "").strip()
    except LLMError:
        # Fallback: return original question when LLM is unavailable
        return question
    # Remove any unwanted prefixes that the LLM might add
    if text.lower().startswith("rewritten question:"):
        text = text[len("rewritten question:"):].strip()
    # Safety: ensure single line result
    rewritten = " ".join(text.split())

    return rewritten


async def summarize_turn(history: List[ChatMessage] | None, answer: str, max_chars: int = 600) -> str:
    """Create a very short rolling summary for future turns (budget-limited)."""
    trimmed = _truncate_history(history or [], max_chars=600)
    history_text = "\n".join([f"{m.role}: {m.content}" for m in trimmed])
    system = (
        "Create a concise conversation summary focusing only on enduring facts and user intents relevant for future turns. "
        "Do not include stylistic chatter. 3-5 short bullet points or 1-2 sentences."
    )
    context = f"{system}\n\n<recent>\n{history_text}\nassistant: {answer}\n</recent>"
    try:
        resp = await llm_service.ask_llm(prompt="Summarize the above.", context=context, max_tokens=120, temperature=0.2)
        text = (resp.content or "").strip()
    except LLMError:
        # Fallback: return trimmed answer if LLM unavailable
        text = answer[:max_chars]
    # Budget summary for inclusion in context windows
    if len(text) > max_chars:
        text = text[:max_chars]
    return text


