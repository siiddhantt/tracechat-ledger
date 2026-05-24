from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class ChatRequest(ApiModel):
    conversation_id: UUID | None = None
    message: str = Field(min_length=1, max_length=20_000)
    provider: Literal["mock", "openrouter", "groq"] | None = None
    model: str | None = Field(default=None, max_length=120)


class StreamEvent(ApiModel):
    event: str
    data: dict[str, object]
