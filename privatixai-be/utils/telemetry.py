"""
Dev Telemetry (Operational Events)

Emits structured, privacy-safe operational events into an in-memory ring buffer
and to standard logging. Never include user content (prompts, snippets, or file
contents). Intended for local development debugging.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, asdict
from typing import Deque, Dict, Any, List
from datetime import datetime, timezone
import logging

from config.settings import settings
import os


logger = logging.getLogger(__name__)

_MAX_EVENTS = 500
_events: Deque[Dict[str, Any]] = deque(maxlen=_MAX_EVENTS)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def emit_event(name: str, data: Dict[str, Any] | None = None) -> None:
    """Record a telemetry event if DEBUG is enabled. Never log user content.

    name: short event key (e.g., "ingestion_stage", "retrieval_completed")
    data: small dict of metadata (ids, counts, durations). Avoid content.
    """
    dev_enabled = settings.DEBUG or os.environ.get("PRIVATIXAI_DEV_TELEMETRY") in {"1", "true", "True"}
    if not dev_enabled:
        # Do nothing when not in debug mode
        return
    payload = {
        "ts": _now_iso(),
        "event": name,
        "data": data or {},
    }
    _events.append(payload)
    try:
        logger.info({"telemetry": payload})
    except Exception:
        pass


def get_recent_events(limit: int = 200) -> List[Dict[str, Any]]:
    """Return the most recent events (up to limit)."""
    if limit <= 0:
        limit = 50
    items = list(_events)[-limit:]
    return items


