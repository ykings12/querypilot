"""Chunk business-rule documents for RAG (Phase 4)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocChunk:
    text: str
    source: str
    chunk_index: int


def chunk_markdown(text: str, *, source: str, max_chars: int = 800) -> list[DocChunk]:
    """Split markdown into paragraph-sized chunks."""
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: list[DocChunk] = []
    buffer: list[str] = []
    size = 0
    index = 0

    def flush() -> None:
        nonlocal index, buffer, size
        if not buffer:
            return
        chunks.append(
            DocChunk(text="\n\n".join(buffer), source=source, chunk_index=index)
        )
        index += 1
        buffer = []
        size = 0

    for paragraph in paragraphs:
        if size + len(paragraph) > max_chars and buffer:
            flush()
        buffer.append(paragraph)
        size += len(paragraph)
    flush()
    return chunks
