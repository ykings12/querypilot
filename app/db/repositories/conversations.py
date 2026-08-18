"""Conversation persistence in metadata Postgres."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, connection_id: uuid.UUID) -> Conversation:
        conversation = Conversation(connection_id=connection_id, state_json={})
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def get(self, conversation_id: uuid.UUID) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def update_state(self, conversation_id: uuid.UUID, state_json: dict) -> None:
        conversation = await self.get(conversation_id)
        if conversation is None:
            raise LookupError("Conversation not found")
        conversation.state_json = state_json
        await self.session.commit()
