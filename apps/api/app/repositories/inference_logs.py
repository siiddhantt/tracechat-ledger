from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import InferenceLog, InferenceStatus
from app.schemas.dashboard import DashboardSummary, ModelMetric, ThroughputPoint
from app.schemas.ingestion import InferenceLogPayload
from app.utils.redaction import preview


class InferenceLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, payload: InferenceLogPayload) -> InferenceLog:
        log = InferenceLog(
            conversation_id=payload.conversation_id,
            provider=payload.provider,
            model=payload.model,
            status=InferenceStatus(payload.status),
            latency_ms=payload.latency_ms,
            prompt_tokens=payload.usage.prompt_tokens,
            completion_tokens=payload.usage.completion_tokens,
            total_tokens=payload.usage.total_tokens,
            input_preview=preview(payload.input_preview) or "",
            output_preview=preview(payload.output_preview),
            error_type=payload.error_type,
            error_message=preview(payload.error_message),
            started_at=payload.started_at,
            completed_at=payload.completed_at,
            metadata_=payload.metadata,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def dashboard_summary(self) -> DashboardSummary:
        since = datetime.now(UTC) - timedelta(hours=24)
        statement = (
            select(InferenceLog)
            .where(InferenceLog.started_at >= since)
            .order_by(InferenceLog.started_at.desc())
            .limit(1_000)
        )
        logs = list((await self.session.execute(statement)).scalars().all())
        total = len(logs)
        errors = [log for log in logs if log.status == InferenceStatus.error]
        latency_total = sum(log.latency_ms for log in logs)
        token_total = sum(log.total_tokens or 0 for log in logs)

        by_model: dict[tuple[str, str], list[InferenceLog]] = defaultdict(list)
        by_minute: dict[datetime, list[InferenceLog]] = defaultdict(list)
        for log in logs:
            by_model[(log.provider, log.model)].append(log)
            minute = log.started_at.astimezone(UTC).replace(second=0, microsecond=0)
            by_minute[minute].append(log)

        models = [
            ModelMetric(
                provider=provider,
                model=model,
                requests=len(items),
                errors=sum(1 for item in items if item.status == InferenceStatus.error),
                avg_latency_ms=round(sum(item.latency_ms for item in items) / len(items), 2),
                total_tokens=sum(item.total_tokens or 0 for item in items),
            )
            for (provider, model), items in sorted(by_model.items())
        ]
        current_minute = datetime.now(UTC).replace(second=0, microsecond=0)
        throughput = []
        for offset in range(29, -1, -1):
            minute = current_minute - timedelta(minutes=offset)
            items = by_minute[minute]
            throughput.append(
                ThroughputPoint(
                    minute=minute.isoformat(),
                    requests=len(items),
                    errors=sum(1 for item in items if item.status == InferenceStatus.error),
                )
            )
        return DashboardSummary(
            total_requests=total,
            error_rate=round((len(errors) / total) * 100, 2) if total else 0.0,
            avg_latency_ms=round(latency_total / total, 2) if total else 0.0,
            total_tokens=token_total,
            requests_per_minute=round(total / (24 * 60), 4),
            models=models,
            throughput=throughput,
            recent_errors=[
                error.error_message or error.error_type or "Unknown error" for error in errors[:5]
            ],
        )

    async def get(self, log_id: UUID) -> InferenceLog | None:
        return await self.session.get(InferenceLog, log_id)
