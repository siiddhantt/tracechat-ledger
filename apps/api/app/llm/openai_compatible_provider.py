import json
from collections.abc import AsyncIterator, Mapping, Sequence

import httpx

from app.llm.base import ChatTurn, LLMProviderError, ProviderChunk, ProviderUsage


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        provider_name: str,
        timeout_seconds: float,
        extra_headers: Mapping[str, str] | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        self.extra_headers = dict(extra_headers or {})

    async def stream_chat(
        self, *, model: str, messages: Sequence[ChatTurn]
    ) -> AsyncIterator[ProviderChunk]:
        payload = {
            "model": model,
            "messages": [{"role": turn.role, "content": turn.content} for turn in messages],
            "stream": True,
            "temperature": 0.2,
            "max_tokens": 512,
            "stream_options": {"include_usage": True},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            async with client.stream(
                "POST", f"{self.base_url}/chat/completions", json=payload, headers=headers
            ) as response:
                if response.status_code >= 400:
                    body = (await response.aread()).decode("utf-8", errors="replace")
                    raise LLMProviderError(body[:500], status_code=response.status_code)

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        break
                    try:
                        yield _parse_chunk(json.loads(data))
                    except json.JSONDecodeError:
                        continue


def _parse_chunk(chunk: dict[str, object]) -> ProviderChunk:
    choices = chunk.get("choices")
    content = ""
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            delta = first.get("delta")
            if isinstance(delta, dict):
                content_value = delta.get("content")
                content = content_value if isinstance(content_value, str) else ""

    usage_value = chunk.get("usage")
    usage = None
    if isinstance(usage_value, dict):
        usage = ProviderUsage(
            prompt_tokens=_int_or_none(usage_value.get("prompt_tokens")),
            completion_tokens=_int_or_none(usage_value.get("completion_tokens")),
            total_tokens=_int_or_none(usage_value.get("total_tokens")),
        )
    return ProviderChunk(content=content, usage=usage)


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None
