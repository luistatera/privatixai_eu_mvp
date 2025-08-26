"""
Audio Transcription - local Whisper pipeline
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple, Dict
import logging

import whisper  # type: ignore

from config.settings import settings

logger = logging.getLogger(__name__)


def transcribe_audio(path: Path) -> Tuple[str, Dict]:
    """Transcribe an audio file using local Whisper.

    Returns:
        (text, metadata)
    """
    logger.info({"event": "transcription_started", "file": str(path)})
    model = whisper.load_model(settings.WHISPER_MODEL)
    result = model.transcribe(str(path))
    text = result.get("text", "").strip()
    meta = {
        "duration": result.get("duration"),
        "language": result.get("language"),
        "task": result.get("task"),
    }
    # Enforce max duration from settings (best-effort; skip if missing)
    dur = meta.get("duration")
    if isinstance(dur, (int, float)):
        max_seconds = settings.MAX_AUDIO_DURATION_MINUTES * 60
        if dur > max_seconds:
            raise ValueError("Audio duration exceeds limit")
    logger.info({"event": "transcription_completed"})
    return text, meta


