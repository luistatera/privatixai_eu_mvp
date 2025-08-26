"""
Text extraction for supported formats: .txt, .md, .pdf, .docx
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import markdown as md
from bs4 import BeautifulSoup
from pypdf import PdfReader
from docx import Document  # type: ignore


def extract_text(file_path: Path) -> Tuple[str, str]:
    """
    Extract text and return (text, extract_strategy).
    """
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore"), "txt"
    if suffix == ".md":
        html = md.markdown(file_path.read_text(encoding="utf-8", errors="ignore"))
        text = BeautifulSoup(html, "html.parser").get_text("\n")
        return text, "markdown_html_strip"
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages), "pdf_text_layer"
    if suffix == ".docx":
        doc = Document(str(file_path))
        paras = [p.text for p in doc.paragraphs]
        return "\n".join(paras), "docx_paragraphs"
    raise ValueError(f"Unsupported file type: {suffix}")


