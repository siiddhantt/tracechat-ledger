from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import httpx

from app.main import app


async def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the FastAPI app in process")
    parser.add_argument("--provider", default="groq", choices=["mock", "openrouter", "groq"])
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver", timeout=30.0
        ) as client:
            health = expect_json(await client.get("/health"))
            assert_equal(health["status"], "ok", "health status")

            before = expect_json(await client.get("/v1/dashboard/summary"))
            before_requests = int(before["total_requests"])

            direct_log = await ingest_direct_log(client)
            assert_equal(direct_log["provider"], "smoke", "direct log provider")
            assert "[email]" in direct_log["input_preview"], "PII was not redacted in direct log"

            stream = await stream_chat(client, provider=args.provider, model=args.model)
            conversation_id = stream["conversation_id"]
            assert stream["assistant_text"], "missing streamed assistant text"

            conversation = expect_json(await client.get(f"/v1/conversations/{conversation_id}"))
            assert_equal(conversation["id"], conversation_id, "conversation id")
            assert_equal(len(conversation["messages"]), 2, "conversation message count")
            assert_equal(conversation["messages"][0]["role"], "user", "first message role")
            assert_equal(conversation["messages"][1]["role"], "assistant", "second message role")

            cancelled = expect_json(
                await client.patch(f"/v1/conversations/{conversation_id}/cancel")
            )
            assert_equal(cancelled["status"], "cancelled", "cancel status")

            resumed = expect_json(await client.patch(f"/v1/conversations/{conversation_id}/resume"))
            assert_equal(resumed["status"], "active", "resume status")

            conversations = expect_json(await client.get("/v1/conversations"))
            assert any(row["id"] == conversation_id for row in conversations), (
                "conversation missing from list"
            )

            after = expect_json(await client.get("/v1/dashboard/summary"))
            assert int(after["total_requests"]) >= before_requests + 2, (
                "dashboard did not include new logs"
            )
            assert any(model["provider"] == args.provider for model in after["models"]), (
                f"{args.provider} provider missing from dashboard"
            )

    print(
        json.dumps(
            {
                "status": "ok",
                "provider": args.provider,
                "conversation_id": conversation_id,
                "logged_requests": int(after["total_requests"]) - before_requests,
                "assistant_preview": stream["assistant_text"][:120],
            },
            indent=2,
        )
    )
    return 0


async def ingest_direct_log(client: httpx.AsyncClient) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    response = await client.post(
        "/v1/ingest/inference",
        json={
            "provider": "smoke",
            "model": "smoke/check",
            "status": "success",
            "latency_ms": 7,
            "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
            "started_at": now,
            "completed_at": now,
            "input_preview": "contact me at smoke@example.com",
            "output_preview": "ok",
            "metadata": {"test_run_id": str(uuid4())},
        },
    )
    return cast(dict[str, Any], expect_json(response))


async def stream_chat(
    client: httpx.AsyncClient, *, provider: str, model: str | None
) -> dict[str, str]:
    conversation_id = ""
    assistant_parts: list[str] = []
    payload = {
        "message": "Reply in six words: why log LLM inference?",
        "provider": provider,
    }
    if model:
        payload["model"] = model

    async with client.stream("POST", "/v1/chat/stream", json=payload) as response:
        response.raise_for_status()
        buffer = ""
        async for chunk in response.aiter_text():
            buffer += chunk
            while "\n\n" in buffer:
                raw, buffer = buffer.split("\n\n", 1)
                event, data = parse_sse(raw)
                if event == "conversation":
                    conversation_id = str(data["conversation_id"])
                if event == "token":
                    assistant_parts.append(str(data["content"]))
                if event == "error":
                    raise AssertionError(data.get("message", "stream error"))
                if event == "done":
                    return {
                        "conversation_id": conversation_id,
                        "assistant_text": "".join(assistant_parts).strip(),
                    }
    raise AssertionError("stream ended without done event")


def parse_sse(raw: str) -> tuple[str, dict[str, Any]]:
    event = ""
    data = ""
    for line in raw.splitlines():
        if line.startswith("event:"):
            event = line.removeprefix("event:").strip()
        if line.startswith("data:"):
            data = line.removeprefix("data:").strip()
    if not event or not data:
        raise AssertionError(f"invalid SSE frame: {raw}")
    return event, json.loads(data)


def expect_json(response: httpx.Response) -> Any:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise AssertionError(response.text) from exc
    return response.json()


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
