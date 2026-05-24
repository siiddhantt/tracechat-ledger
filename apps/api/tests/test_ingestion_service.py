from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.ingestion.service import IngestionService
from app.schemas.ingestion import InferenceLogPayload, TokenUsage


@pytest.mark.asyncio
async def test_ingestion_stores_redacted_processed_log() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        now = datetime.now(UTC)
        payload = InferenceLogPayload(
            provider="mock",
            model="mock/local-chat",
            status="success",
            latency_ms=42,
            usage=TokenUsage(prompt_tokens=2, completion_tokens=3, total_tokens=5),
            started_at=now,
            completed_at=now,
            input_preview="reach me at sid@example.com",
            output_preview="done",
        )

        result = await IngestionService(session).ingest(payload)
        await session.commit()

    await engine.dispose()

    assert result.provider == "mock"
    assert result.total_tokens == 5
    assert "sid@example.com" not in result.input_preview
    assert "[email]" in result.input_preview
