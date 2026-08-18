"""Unit tests for markdown chunker."""

from app.rag.chunker import chunk_markdown


def test_chunk_markdown_splits_paragraphs():
    text = "Para one.\n\nPara two is longer and should still be kept.\n\nPara three."
    chunks = chunk_markdown(text, source="rules.md", max_chars=50)
    assert len(chunks) >= 2
    assert all(chunk.source == "rules.md" for chunk in chunks)
    assert "Para one" in chunks[0].text
