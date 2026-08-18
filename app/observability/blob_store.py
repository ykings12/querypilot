"""Write prompt/response blobs to disk for trace inspection."""

from __future__ import annotations

import uuid
from pathlib import Path


class BlobStore:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write_text(self, request_id: uuid.UUID, filename: str, content: str) -> str:
        directory = self.base_dir / str(request_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / filename
        path.write_text(content, encoding="utf-8")
        return str(path.relative_to(self.base_dir))
