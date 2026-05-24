import json
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AppError
from app.db.models import Conversation, ConversationStatus, MessageRole
from app.ingestion.service import IngestionService
from app.llm.base import ChatTurn
from app.llm.factory import ProviderFactory
from app.repositories.conversations import ConversationRepository
from app.schemas.chat import ChatRequest
from app.schemas.ingestion import InferenceLogOut, InferenceLogPayload
from app.sdk.logger import InferenceLogger
from app.services.logged_llm import InferenceCancelled, LoggedLLMClient

SYSTEM_PROMPT = (
    "You are a concise assistant inside a demo LLM observability product. "
    "Answer helpfully while keeping responses focused."
)


class DirectIngestionSink:
    def __init__(self, session: AsyncSession) -> None:
        self.service = IngestionService(session)

    async def capture(self, payload: InferenceLogPayload) -> InferenceLogOut:
        return await self.service.ingest(payload)


class ChatService:
    def __init__(self, *, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.conversations = ConversationRepository(session)
        self.provider_factory = ProviderFactory(settings)

    async def stream(self, request: ChatRequest) -> AsyncIterator[str]:
        conversation = await self._get_or_create_conversation(request)
        if conversation.status == ConversationStatus.cancelled:
            raise AppError(
                "Resume the conversation before sending another message", status_code=409
            )

        history = await self.conversations.list_messages(
            conversation.id, limit=self.settings.context_message_limit
        )
        await self.conversations.add_message(
            conversation_id=conversation.id, role=MessageRole.user, content=request.message
        )
        await self.session.commit()

        provider = self.provider_factory.get(request.provider)
        model = request.model or self.provider_factory.default_model_for(provider.name)
        logger = InferenceLogger(DirectIngestionSink(self.session))
        client = LoggedLLMClient(provider=provider, logger=logger)
        turns = [ChatTurn(role="system", content=SYSTEM_PROMPT)]
        turns.extend(
            ChatTurn(role=message.role.value, content=message.content) for message in history
        )
        turns.append(ChatTurn(role="user", content=request.message))

        yield sse("conversation", {"conversation_id": str(conversation.id)})

        assistant_parts: list[str] = []
        try:
            async for token in client.stream_chat(
                conversation_id=conversation.id,
                model=model,
                messages=turns,
                should_cancel=lambda: self.conversations.is_cancelled(conversation.id),
            ):
                assistant_parts.append(token)
                yield sse("token", {"content": token})
        except InferenceCancelled:
            await self.session.commit()
            yield sse("error", {"message": "Conversation cancelled"})
            return
        except Exception as exc:
            await self.session.commit()
            yield sse("error", {"message": _safe_error(exc)})
            return

        message = await self.conversations.add_message(
            conversation_id=conversation.id,
            role=MessageRole.assistant,
            content="".join(assistant_parts).strip(),
        )
        await self.session.commit()
        yield sse("done", {"message_id": str(message.id)})

    async def _get_or_create_conversation(self, request: ChatRequest) -> Conversation:
        if request.conversation_id is None:
            conversation = await self.conversations.create(request.message)
            await self.session.flush()
            return conversation
        existing = await self.conversations.get(request.conversation_id)
        if existing is None:
            raise AppError("Conversation not found", status_code=404, code="conversation_not_found")
        return existing


def sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _safe_error(exc: Exception) -> str:
    if isinstance(exc, AppError):
        return exc.message
    return "The model request failed. Please try again."
