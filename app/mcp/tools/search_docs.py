"""Search business-rule documents (untrusted chunks for prompts)."""

from __future__ import annotations

from typing import Any

from app.config import Settings, get_settings
from app.rag.doc_store import get_document_index, load_documents_from_dir


async def search_docs(
    *,
    query: str,
    k: int = 5,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    cfg = settings or get_settings()
    index = get_document_index()
    if not index.chunks:
        load_documents_from_dir(cfg.docs_dir_path, cfg)

    hits = index.search(query, k=cfg.docs_top_k, settings=cfg)
    return [
        {
            "chunk": hit.chunk,
            "source": hit.source,
            "score": hit.score,
            "untrusted": hit.untrusted,
        }
        for hit in hits
    ]
