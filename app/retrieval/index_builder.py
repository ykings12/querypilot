"""Build vector index from introspected catalog."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.rag.embeddings import embed_texts
from app.rag.faiss_store import TableVectorIndex
from app.retrieval.table_cards import build_table_card


def build_table_vector_index(catalog: dict[str, Any], settings: Settings) -> TableVectorIndex:
    tables = catalog.get("tables", [])
    names = [table["name"] for table in tables]
    cards = [build_table_card(table) for table in tables]
    vectors = embed_texts(cards, settings)
    return TableVectorIndex(table_names=names, vectors=vectors)
