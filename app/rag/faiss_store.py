"""Per-connection vector index for table cards."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.rag.embeddings import cosine_similarity


@dataclass
class TableVectorIndex:
    table_names: list[str]
    vectors: np.ndarray

    def search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[str, float]]:
        if not self.table_names:
            return []
        scores = cosine_similarity(query_vector, self.vectors)
        order = np.argsort(-scores)[:top_k]
        return [(self.table_names[i], float(scores[i])) for i in order]


class FaissTableIndexStore:
    """In-memory index keyed by connection_id:schema_version."""

    def __init__(self) -> None:
        self._indexes: dict[str, TableVectorIndex] = {}

    def key(self, connection_id: str, schema_version: str) -> str:
        return f"{connection_id}:{schema_version}"

    def put(self, connection_id: str, schema_version: str, index: TableVectorIndex) -> None:
        self._indexes[self.key(connection_id, schema_version)] = index

    def get(self, connection_id: str, schema_version: str) -> TableVectorIndex | None:
        return self._indexes.get(self.key(connection_id, schema_version))

    def clear_connection(self, connection_id: str) -> None:
        prefix = f"{connection_id}:"
        for key in list(self._indexes):
            if key.startswith(prefix):
                del self._indexes[key]


table_index_store = FaissTableIndexStore()
