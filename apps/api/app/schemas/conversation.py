from datetime import datetime
from uuid import UUID

from app.db.models import ConversationStatus, MessageRole
from app.schemas.common import ApiModel


class ChatMessageOut(ApiModel):
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    preview: str
    created_at: datetime


class ConversationSummary(ApiModel):
    id: UUID
    title: str
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    last_message_preview: str | None = None


class ConversationDetail(ConversationSummary):
    messages: list[ChatMessageOut]
