"""Hybrid BM25 + vector retrieval over table cards (§13.2)."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from app.config import Settings
from app.rag.embeddings import embed_query, min_max_normalize
from app.rag.faiss_store import TableVectorIndex
from app.retrieval.fk_expand import fk_expand
from app.retrieval.table_cards import build_table_card


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


def hybrid_retrieve_tables(
    *,
    question: str,
    catalog: dict[str, Any],
    vector_index: TableVectorIndex | None,
    settings: Settings,
) -> list[str]:
    tables = catalog.get("tables", [])
    if not tables:
        return []

    cards = [(table["name"], build_table_card(table)) for table in tables]
    names = [name for name, _ in cards]
    corpus_tokens = [_tokenize(card) for _, card in cards]

    bm25 = BM25Okapi(corpus_tokens)
    question_tokens = _tokenize(question)
    bm25_scores = np.array(bm25.get_scores(question_tokens), dtype=np.float32)
    bm25_norm = min_max_normalize(bm25_scores)

    if vector_index is not None and vector_index.table_names:
        name_to_idx = {name: idx for idx, name in enumerate(names)}
        vector_scores = np.zeros(len(names), dtype=np.float32)
        query_vec = embed_query(question, settings)
        for table_name, score in vector_index.search(query_vec, top_k=len(names)):
            idx = name_to_idx.get(table_name)
            if idx is not None:
                vector_scores[idx] = score
        vector_norm = min_max_normalize(vector_scores)
    else:
        vector_norm = np.zeros(len(names), dtype=np.float32)

    fused = 0.4 * bm25_norm + 0.6 * vector_norm
    top_k = min(settings.retrieval_top_k, len(names))
    order = np.argsort(-fused)[:top_k]
    selected = [names[i] for i in order]

    return fk_expand(selected, catalog, max_tables=settings.retrieval_max_tables)


def build_subset_ddl(catalog: dict[str, Any], table_names: list[str]) -> str:
    selected = {name for name in table_names}
    subset = [table for table in catalog.get("tables", []) if table["name"] in selected]
    return "\n\n".join(build_table_card(table) for table in subset)
