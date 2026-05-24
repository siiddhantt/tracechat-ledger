from uuid import UUID

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SessionDep
from app.core.errors import AppError
from app.db.models import ConversationStatus
from app.repositories.conversations import ConversationRepository
from app.schemas.conversation import ConversationDetail, ConversationSummary

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    session: SessionDep,
) -> list[ConversationSummary]:
    repository = ConversationRepository(session)
    conversations = await repository.list()
    result: list[ConversationSummary] = []
    for conversation in conversations:
        result.append(
            ConversationSummary(
                id=conversation.id,
                title=conversation.title,
                status=conversation.status,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                last_message_preview=await repository.last_message_preview(conversation.id),
            )
        )
    return result


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    session: SessionDep,
) -> ConversationDetail:
    repository = ConversationRepository(session)
    conversation = await repository.get_with_messages(conversation_id)
    if conversation is None:
        raise AppError("Conversation not found", status_code=404, code="conversation_not_found")
    messages = sorted(conversation.messages, key=lambda message: message.created_at)
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_message_preview=messages[-1].preview if messages else None,
        messages=messages,
    )


@router.patch("/{conversation_id}/cancel")
async def cancel_conversation(
    conversation_id: UUID,
    session: SessionDep,
) -> ConversationSummary:
    return await _set_status(conversation_id, ConversationStatus.cancelled, session)


@router.patch("/{conversation_id}/resume")
async def resume_conversation(
    conversation_id: UUID,
    session: SessionDep,
) -> ConversationSummary:
    return await _set_status(conversation_id, ConversationStatus.active, session)


async def _set_status(
    conversation_id: UUID, status: ConversationStatus, session: AsyncSession
) -> ConversationSummary:
    repository = ConversationRepository(session)
    conversation = await repository.set_status(conversation_id, status)
    if conversation is None:
        raise AppError("Conversation not found", status_code=404, code="conversation_not_found")
    await session.commit()
    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        status=conversation.status,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_message_preview=await repository.last_message_preview(conversation.id),
    )
