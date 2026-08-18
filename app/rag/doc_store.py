"""In-memory document index for business-rule search."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.config import Settings
from app.rag.chunker import DocChunk, chunk_markdown
from app.rag.embeddings import embed_query, embed_texts


@dataclass
class DocSearchHit:
    chunk: str
    source: str
    score: float
    untrusted: bool = True


class DocumentIndex:
    def __init__(self) -> None:
        self.chunks: list[DocChunk] = []
        self.vectors: np.ndarray = np.zeros((0, 384), dtype=np.float32)

    def build(self, chunks: list[DocChunk], settings: Settings) -> None:
        self.chunks = chunks
        if not chunks:
            self.vectors = np.zeros((0, 384), dtype=np.float32)
            return
        self.vectors = embed_texts([chunk.text for chunk in chunks], settings)

    def search(self, query: str, *, k: int, settings: Settings) -> list[DocSearchHit]:
        if not self.chunks:
            return []
        query_vec = embed_query(query, settings)
        scores = self.vectors @ query_vec.astype(np.float32)
        order = np.argsort(-scores)[:k]
        hits: list[DocSearchHit] = []
        for idx in order:
            chunk = self.chunks[int(idx)]
            hits.append(
                DocSearchHit(
                    chunk=chunk.text,
                    source=chunk.source,
                    score=float(scores[int(idx)]),
                )
            )
        return hits


_doc_index: DocumentIndex | None = None


def get_document_index() -> DocumentIndex:
    global _doc_index
    if _doc_index is None:
        _doc_index = DocumentIndex()
    return _doc_index


def load_documents_from_dir(docs_dir: Path, settings: Settings) -> DocumentIndex:
    index = get_document_index()
    all_chunks: list[DocChunk] = []
    if docs_dir.is_dir():
        for path in sorted(docs_dir.glob("**/*.md")):
            text = path.read_text(encoding="utf-8")
            all_chunks.extend(chunk_markdown(text, source=path.name))
    index.build(all_chunks, settings)
    return index
