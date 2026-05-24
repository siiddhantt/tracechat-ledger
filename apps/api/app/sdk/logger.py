from typing import Protocol

from app.schemas.ingestion import InferenceLogOut, InferenceLogPayload


class InferenceLogSink(Protocol):
    async def capture(self, payload: InferenceLogPayload) -> InferenceLogOut:
        raise NotImplementedError


class InferenceLogger:
    def __init__(self, sink: InferenceLogSink) -> None:
        self.sink = sink

    async def capture(self, payload: InferenceLogPayload) -> InferenceLogOut:
        return await self.sink.capture(payload)
