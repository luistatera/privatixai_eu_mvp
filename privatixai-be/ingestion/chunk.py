from __future__ import annotations

from typing import List, Tuple
import re


# TODO: Use a better chunking strategy.
def fixed_size_chunk(text: str, size: int, overlap: int) -> List[Tuple[int, int, str]]:
    """
    Create fixed-size chunks with character offsets.
    Returns list of (start, end, chunk_text).
    """
    if size <= 0:
        raise ValueError("size must be > 0")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")
    text = text or ""
    result: List[Tuple[int, int, str]] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        chunk_text = text[start:end]
        result.append((start, end, chunk_text))
        if end == n:
            break
        start = end - overlap
    return result


def token_chunk(text: str, target_tokens: int, min_tokens: int, overlap_tokens: int) -> List[Tuple[int, int, str]]:
    """
    Token-based chunking using whitespace tokens with overlap.
    Returns list of (start_char, end_char, chunk_text).

    - target_tokens: desired number of tokens per chunk
    - min_tokens: minimum tokens for the final chunk; if the last window is below
      min_tokens and there is at least one prior chunk, merge it with the previous
    - overlap_tokens: number of tokens to overlap between consecutive chunks
    """
    if target_tokens <= 0:
        raise ValueError("target_tokens must be > 0")
    if overlap_tokens < 0 or overlap_tokens >= target_tokens:
        raise ValueError("overlap_tokens must be >= 0 and < target_tokens")

    text = text or ""
    if not text:
        return []

    # Find whitespace-delimited tokens and their char spans
    tokens: List[Tuple[int, int]] = [
        (m.start(), m.end()) for m in re.finditer(r"\S+", text)
    ]
    n_tokens = len(tokens)
    if n_tokens == 0:
        return []

    chunks: List[Tuple[int, int, str]] = []
    step = max(1, target_tokens - overlap_tokens)
    i = 0
    while i < n_tokens:
        j = min(i + target_tokens, n_tokens)
        start_char = tokens[i][0]
        end_char = tokens[j - 1][1]
        chunk_text = text[start_char:end_char]
        chunks.append((start_char, end_char, chunk_text))
        if j >= n_tokens:
            break
        i = i + step

    # If the last chunk is too small, and there is a previous chunk, merge into previous
    if len(chunks) >= 2:
        last_tokens = len([1 for _ in re.finditer(r"\S+", chunks[-1][2])])
        if last_tokens < max(1, min_tokens):
            prev_start, _, _ = chunks[-2]
            _, last_end, _ = chunks[-1]
            merged_text = text[prev_start:last_end]
            chunks[-2] = (prev_start, last_end, merged_text)
            chunks.pop()

    return chunks


