from __future__ import annotations

from pathlib import Path
from typing import Optional

from config.settings import settings


MIME_TO_SUFFIX = {
    "text/plain": ".txt",
    "text/markdown": ".md",
    "text/x-markdown": ".md",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    # Audio (MVP 1.0: MP3 only)
    "audio/mpeg": ".mp3",
}


def guess_supported_suffix(filename: str, content: bytes, content_type: Optional[str]) -> Optional[str]:
    """
    Try to resolve a supported text suffix using filename, provided content_type, and magic-based detection.
    Returns a suffix like ".txt" if supported, otherwise None.
    """
    # 1) Use filename extension if supported
    suffix = Path(filename).suffix.lower()
    if suffix in settings.SUPPORTED_TEXT_FORMATS or suffix in settings.SUPPORTED_AUDIO_FORMATS:
        return suffix

    # 2) Use provided content_type mapping
    if content_type and content_type in MIME_TO_SUFFIX:
        mapped = MIME_TO_SUFFIX[content_type]
        if mapped in settings.SUPPORTED_TEXT_FORMATS or mapped in settings.SUPPORTED_AUDIO_FORMATS:
            return mapped

    # 3) Use python-magic to detect mime (optional)
    try:
        # Import lazily to avoid hard dependency at module import
        import magic  # type: ignore
        mime = magic.from_buffer(content, mime=True)
        mapped = MIME_TO_SUFFIX.get(mime)
        if mapped in settings.SUPPORTED_TEXT_FORMATS or mapped in settings.SUPPORTED_AUDIO_FORMATS:
            return mapped
    except Exception:
        pass

    return None


