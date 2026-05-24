import asyncio
from collections.abc import AsyncIterator, Sequence

from app.llm.base import ChatTurn, ProviderChunk, ProviderUsage


class MockProvider:
    name = "mock"

    async def stream_chat(
        self, *, model: str, messages: Sequence[ChatTurn]
    ) -> AsyncIterator[ProviderChunk]:
        last_user = next((turn.content for turn in reversed(messages) if turn.role == "user"), "")
        response = (
            "Mock response: I received your message and logged this inference path. "
            f"You said, {last_user[:180]}"
        )
        words = response.split(" ")
        for word in words:
            await asyncio.sleep(0.02)
            yield ProviderChunk(content=f"{word} ")
        prompt_tokens = sum(len(turn.content.split()) for turn in messages)
        completion_tokens = len(words)
        yield ProviderChunk(
            usage=ProviderUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )
        )
