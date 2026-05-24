import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID

from app.llm.base import ChatTurn, LLMProvider, ProviderUsage
from app.schemas.ingestion import InferenceLogPayload, TokenUsage
from app.sdk.logger import InferenceLogger
from app.utils.redaction import preview

logger = logging.getLogger(__name__)


class InferenceCancelled(Exception):
    pass


class LoggedLLMClient:
    def __init__(self, *, provider: LLMProvider, logger: InferenceLogger) -> None:
        self.provider = provider
        self.logger = logger

    async def stream_chat(
        self,
        *,
        conversation_id: UUID,
        model: str,
        messages: Sequence[ChatTurn],
        should_cancel: Callable[[], Awaitable[bool]] | None = None,
    ) -> AsyncIterator[str]:
        started_at = datetime.now(UTC)
        started = perf_counter()
        output_parts: list[str] = []
        usage = ProviderUsage()
        status = "success"
        error_type = None
        error_message = None
        try:
            async for chunk in self.provider.stream_chat(model=model, messages=messages):
                if chunk.usage is not None:
                    usage = chunk.usage
                if chunk.content:
                    if should_cancel is not None and await should_cancel():
                        raise InferenceCancelled("Conversation cancelled")
                    output_parts.append(chunk.content)
                    yield chunk.content
        except asyncio.CancelledError:
            status = "cancelled"
            error_type = "CancelledError"
            error_message = "Client cancelled the stream"
            raise
        except InferenceCancelled as exc:
            status = "cancelled"
            error_type = exc.__class__.__name__
            error_message = str(exc)
            raise
        except Exception as exc:
            status = "error"
            error_type = exc.__class__.__name__
            error_message = str(exc)
            raise
        finally:
            completed_at = datetime.now(UTC)
            payload = InferenceLogPayload(
                conversation_id=conversation_id,
                provider=self.provider.name,
                model=model,
                status=status,
                latency_ms=max(0, round((perf_counter() - started) * 1000)),
                usage=TokenUsage(
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                ),
                started_at=started_at,
                completed_at=completed_at,
                input_preview=preview(_last_user_message(messages), limit=500) or "",
                output_preview=preview("".join(output_parts), limit=500),
                error_type=error_type,
                error_message=error_message,
                metadata={"message_count": len(messages)},
            )
            try:
                await self.logger.capture(payload)
            except Exception:
                logger.exception("failed to capture inference log")


def _last_user_message(messages: Sequence[ChatTurn]) -> str:
    return next((turn.content for turn in reversed(messages) if turn.role == "user"), "")
