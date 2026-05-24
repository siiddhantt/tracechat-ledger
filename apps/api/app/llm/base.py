from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

ChatRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatTurn:
    role: ChatRole
    content: str


@dataclass(frozen=True)
class ProviderUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class ProviderChunk:
    content: str = ""
    usage: ProviderUsage | None = None


class LLMProviderError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class LLMProvider(Protocol):
    name: str

    def stream_chat(
        self, *, model: str, messages: Sequence[ChatTurn]
    ) -> AsyncIterator[ProviderChunk]:
        raise NotImplementedError
