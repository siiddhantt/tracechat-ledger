from fastapi import APIRouter

from app.api.deps import SessionDep
from app.repositories.inference_logs import InferenceLogRepository
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    session: SessionDep,
) -> DashboardSummary:
    return await InferenceLogRepository(session).dashboard_summary()
