"""Text embeddings for schema retrieval (§13.2)."""

from __future__ import annotations

import hashlib
import math
import os
from functools import lru_cache

import numpy as np

from app.config import Settings, get_settings


def _hash_embedding(text: str, dim: int = 384) -> np.ndarray:
    """Deterministic fallback when sentence-transformers is not installed."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = [digest[i % len(digest)] / 255.0 for i in range(dim)]
    vec = np.array(values, dtype=np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


@lru_cache(maxsize=1)
def _sentence_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def _use_hash_embeddings_only() -> bool:
    flag = os.getenv("QUERYPILOT_HASH_EMBEDDINGS", "").lower()
    return flag in {"1", "true", "yes", "on"}


def embed_texts(texts: list[str], settings: Settings | None = None) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)

    if _use_hash_embeddings_only():
        return np.stack([_hash_embedding(text) for text in texts])

    cfg = settings or get_settings()
    try:
        model = _sentence_model(cfg.embedding_model)
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vectors, dtype=np.float32)
    except ImportError:
        return np.stack([_hash_embedding(text) for text in texts])
    except Exception:
        return np.stack([_hash_embedding(text) for text in texts])


def embed_query(question: str, settings: Settings | None = None) -> np.ndarray:
    return embed_texts([question], settings=settings)[0]


def cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return np.array([], dtype=np.float32)
    return matrix @ query.astype(np.float32)


def min_max_normalize(scores: np.ndarray) -> np.ndarray:
    if scores.size == 0:
        return scores
    lo = float(scores.min())
    hi = float(scores.max())
    if math.isclose(lo, hi):
        return np.ones_like(scores)
    return (scores - lo) / (hi - lo)
