from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class TokenUsage(ApiModel):
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class InferenceLogPayload(ApiModel):
    conversation_id: UUID | None = None
    provider: str = Field(min_length=1, max_length=60)
    model: str = Field(min_length=1, max_length=120)
    status: Literal["success", "error", "cancelled"]
    latency_ms: int = Field(ge=0)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    started_at: datetime
    completed_at: datetime
    input_preview: str = Field(default="", max_length=2_000)
    output_preview: str | None = Field(default=None, max_length=2_000)
    error_type: str | None = Field(default=None, max_length=120)
    error_message: str | None = Field(default=None, max_length=2_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InferenceLogOut(ApiModel):
    id: UUID
    conversation_id: UUID | None
    provider: str
    model: str
    status: str
    latency_ms: int
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    input_preview: str
    output_preview: str | None
    error_type: str | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime
    metadata: dict[str, Any]
