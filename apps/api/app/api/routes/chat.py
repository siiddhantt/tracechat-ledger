from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import SessionDep, SettingsDep
from app.schemas.chat import ChatRequest
from app.services.chat import ChatService

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    session: SessionDep,
    settings: SettingsDep,
) -> StreamingResponse:
    service = ChatService(session=session, settings=settings)
    return StreamingResponse(service.stream(request), media_type="text/event-stream")
