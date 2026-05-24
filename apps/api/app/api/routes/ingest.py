from fastapi import APIRouter

from app.api.deps import SessionDep
from app.ingestion.service import IngestionService
from app.schemas.ingestion import InferenceLogOut, InferenceLogPayload

router = APIRouter(prefix="/v1/ingest", tags=["ingestion"])


@router.post("/inference")
async def ingest_inference_log(
    payload: InferenceLogPayload,
    session: SessionDep,
) -> InferenceLogOut:
    result = await IngestionService(session).ingest(payload)
    await session.commit()
    return result
