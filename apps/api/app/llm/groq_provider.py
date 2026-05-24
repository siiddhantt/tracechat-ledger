from collections.abc import AsyncIterator, Sequence

from app.llm.base import ChatTurn, ProviderChunk
from app.llm.openai_compatible_provider import OpenAICompatibleProvider


class GroqProvider:
    name = "groq"

    def __init__(self, *, api_key: str, base_url: str, timeout_seconds: float) -> None:
        self.client = OpenAICompatibleProvider(
            api_key=api_key,
            base_url=base_url,
            provider_name=self.name,
            timeout_seconds=timeout_seconds,
            extra_headers={"X-Title": "TraceChat Ledger"},
        )

    def stream_chat(
        self, *, model: str, messages: Sequence[ChatTurn]
    ) -> AsyncIterator[ProviderChunk]:
        return self.client.stream_chat(model=model, messages=messages)
