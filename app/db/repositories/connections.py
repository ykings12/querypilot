"""Data access for stored DB connections."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Connection


class ConnectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, connection: Connection) -> Connection:
        self.session.add(connection)
        await self.session.commit()
        await self.session.refresh(connection)
        return connection

    async def list_all(self) -> list[Connection]:
        result = await self.session.execute(
            select(Connection).order_by(Connection.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, connection_id: uuid.UUID) -> Connection | None:
        return await self.session.get(Connection, connection_id)

    async def update_schema_version(self, connection_id: uuid.UUID, schema_version: str) -> None:
        connection = await self.get(connection_id)
        if connection is None:
            return
        connection.schema_version = schema_version
        await self.session.commit()
