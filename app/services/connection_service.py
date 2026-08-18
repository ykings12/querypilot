"""Connection registration and listing — secrets write-only on the API."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ConnectionCreate, ConnectionResponse
from app.config import Settings
from app.db.models import Connection
from app.db.repositories.connections import ConnectionRepository
from app.security.encryption import EncryptionError, encrypt_credentials


class ConnectionService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.repo = ConnectionRepository(session)
        self.settings = settings

    async def register(self, payload: ConnectionCreate) -> ConnectionResponse:
        if not self.settings.kek_secret:
            raise ValueError("KEK_SECRET is not configured")

        try:
            encrypted = encrypt_credentials(payload.password, self.settings.kek_secret)
        except EncryptionError as exc:
            raise ValueError(str(exc)) from exc

        connection = Connection(
            name=payload.name,
            host=payload.host,
            port=payload.port,
            database=payload.database,
            username=payload.username,
            encrypted_credentials=encrypted,
        )
        saved = await self.repo.create(connection)
        return ConnectionResponse.model_validate(saved)

    async def list_connections(self) -> list[ConnectionResponse]:
        connections = await self.repo.list_all()
        return [ConnectionResponse.model_validate(item) for item in connections]

    async def get_connection(self, connection_id: uuid.UUID) -> Connection | None:
        return await self.repo.get(connection_id)
