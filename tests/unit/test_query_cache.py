"""Query result cache behavior."""

from __future__ import annotations

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.cache.cache_keys import query_cache_key
from app.cache.memory_cache import QueryCacheEntry, SchemaCacheEntry, memory_cache
from app.services.query_service import QueryService


@pytest.fixture
def reset_memory_cache():
    memory_cache._schema_by_connection.clear()
    memory_cache._query_cache.clear()
    yield
    memory_cache._schema_by_connection.clear()
    memory_cache._query_cache.clear()


@pytest.mark.asyncio
async def test_query_cache_hit_skips_pipeline(kek_env, reset_memory_cache):
    from app.config import get_settings

    settings = get_settings()
    connection_id = uuid.uuid4()
    question = "How many customers are there?"
    schema_version = "sha256:test"

    memory_cache.set_schema(
        str(connection_id),
        SchemaCacheEntry(schema_version=schema_version, table_ddl="-- ddl", catalog={"tables": []}),
    )
    cache_key = query_cache_key(
        connection_id=str(connection_id),
        schema_version=schema_version,
        question=question,
    )
    memory_cache.set_query(
        cache_key,
        QueryCacheEntry(
            sql="SELECT COUNT(*) FROM customer",
            rationale={"tables": ["customer"], "joins": [], "filters": [], "aggregation": "count"},
            columns=["count"],
            rows=[[59]],
            truncated=False,
            expires_at=time.time() + 3600,
        ),
    )

    session = MagicMock()
    service = QueryService(session, settings)
    service.connections.get = AsyncMock(return_value=MagicMock(id=connection_id))

    fake_conv_id = uuid.uuid4()
    fake_conv = MagicMock(id=fake_conv_id, connection_id=connection_id, state_json={})

    with (
        patch("app.services.query_service.run_query_pipeline", new_callable=AsyncMock) as pipeline,
        patch("app.services.query_service.TraceRepository") as trace_repo_cls,
        patch("app.services.query_service.ConversationRepository") as conv_repo_cls,
    ):
        conv_repo_cls.return_value.get = AsyncMock(return_value=None)
        conv_repo_cls.return_value.create = AsyncMock(return_value=fake_conv)
        conv_repo_cls.return_value.update_state = AsyncMock()
        trace_repo_cls.return_value.save_spans = AsyncMock()
        response = await service.run_query(connection_id, question)

    pipeline.assert_not_called()
    assert response.from_cache is True
    assert response.rows == [[59]]
    assert response.conversation_id == fake_conv_id
