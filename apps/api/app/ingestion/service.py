from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.inference_logs import InferenceLogRepository
from app.schemas.ingestion import InferenceLogOut, InferenceLogPayload


class IngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = InferenceLogRepository(session)

    async def ingest(self, payload: InferenceLogPayload) -> InferenceLogOut:
        log = await self.repository.create(payload)
        return InferenceLogOut(
            id=log.id,
            conversation_id=log.conversation_id,
            provider=log.provider,
            model=log.model,
            status=log.status.value,
            latency_ms=log.latency_ms,
            prompt_tokens=log.prompt_tokens,
            completion_tokens=log.completion_tokens,
            total_tokens=log.total_tokens,
            input_preview=log.input_preview,
            output_preview=log.output_preview,
            error_type=log.error_type,
            error_message=log.error_message,
            started_at=log.started_at,
            completed_at=log.completed_at,
            metadata=log.metadata_,
        )
