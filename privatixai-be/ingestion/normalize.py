from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    """Normalize text for chunking and embedding."""
    if not text:
        return ""
    # Fix common hyphenated line breaks: e.g., "exam-
    # ple" -> "example"
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse excessive whitespace
    text = re.sub(r"[\t\x0b\x0c\r]+", " ", text)
    # Strip trailing spaces on lines
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


