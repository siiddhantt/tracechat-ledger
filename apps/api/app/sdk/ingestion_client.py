import httpx

from app.schemas.ingestion import InferenceLogOut, InferenceLogPayload


class HttpInferenceLogClient:
    def __init__(self, *, endpoint: str, timeout_seconds: float = 5.0) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def capture(self, payload: InferenceLogPayload) -> InferenceLogOut:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.endpoint}/v1/ingest/inference",
                json=payload.model_dump(mode="json"),
            )
            response.raise_for_status()
            return InferenceLogOut.model_validate(response.json())
