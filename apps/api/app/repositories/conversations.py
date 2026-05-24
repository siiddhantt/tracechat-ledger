import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ChatMessage, Conversation, ConversationStatus, MessageRole
from app.utils.redaction import preview, redact_text, title_from_message


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, first_message: str) -> Conversation:
        conversation = Conversation(title=title_from_message(first_message))
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get(self, conversation_id: uuid.UUID) -> Conversation | None:
        return await self.session.get(Conversation, conversation_id)

    async def get_with_messages(self, conversation_id: uuid.UUID) -> Conversation | None:
        statement = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def list(self) -> Sequence[Conversation]:
        statement = select(Conversation).order_by(Conversation.updated_at.desc()).limit(50)
        return (await self.session.execute(statement)).scalars().all()

    async def list_messages(
        self, conversation_id: uuid.UUID, *, limit: int = 50
    ) -> Sequence[ChatMessage]:
        statement = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        rows = (await self.session.execute(statement)).scalars().all()
        return list(reversed(rows))

    async def add_message(
        self, *, conversation_id: uuid.UUID, role: MessageRole, content: str
    ) -> ChatMessage:
        redacted = redact_text(content)
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=redacted,
            preview=preview(redacted, limit=280) or "",
        )
        self.session.add(message)
        await self.touch(conversation_id)
        await self.session.flush()
        return message

    async def set_status(
        self, conversation_id: uuid.UUID, status: ConversationStatus
    ) -> Conversation | None:
        conversation = await self.get(conversation_id)
        if conversation is None:
            return None
        conversation.status = status
        await self.touch(conversation_id)
        await self.session.flush()
        return conversation

    async def is_cancelled(self, conversation_id: uuid.UUID) -> bool:
        statement = select(Conversation.status).where(Conversation.id == conversation_id)
        status = (await self.session.execute(statement)).scalar_one_or_none()
        return status == ConversationStatus.cancelled

    async def last_message_preview(self, conversation_id: uuid.UUID) -> str | None:
        statement = (
            select(ChatMessage.preview)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(statement)).scalar_one_or_none()

    async def touch(self, conversation_id: uuid.UUID) -> None:
        conversation = await self.get(conversation_id)
        if conversation is not None:
            conversation.updated_at = await self._database_now()

    async def _database_now(self) -> datetime:
        return (await self.session.execute(select(func.now()))).scalar_one()


def context_messages(messages: Sequence[ChatMessage]) -> list[dict[str, str]]:
    return [{"role": message.role.value, "content": message.content} for message in messages]


def conversation_query() -> Select[tuple[Conversation]]:
    return select(Conversation)
