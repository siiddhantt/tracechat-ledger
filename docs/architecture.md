# Architecture Notes

## Ingestion Flow

1. The frontend posts a message to `POST /v1/chat/stream`.
2. The API creates or resumes a conversation and stores the user message after PII redaction.
3. `ProviderFactory` selects `groq`, `openrouter`, or `mock`.
4. `LoggedLLMClient` streams provider chunks to the caller while measuring latency, status, token usage, and previews.
5. When the stream ends, errors, or is cancelled, the lightweight logger emits an `InferenceLogPayload`.
6. The ingestion service validates and normalizes the payload, redacts previews and errors, and stores `inference_logs`.
7. Dashboard endpoints read processed logs and return latency, throughput, token, and error aggregates.

## Logging Strategy

The logging wrapper sits around provider calls instead of inside route handlers. That keeps metadata capture consistent across Groq, OpenRouter, mock, and future providers. The wrapper records:

- provider and model
- conversation ID
- started/completed timestamps
- latency
- token usage when the provider returns it
- request status
- redacted input/output previews
- sanitized error details

The app includes both a direct sink and an HTTP ingestion client. The direct sink avoids self-HTTP in the demo process, while the HTTP client shows how the same payload can be emitted by another service.

## Scaling Considerations

- API instances are stateless except for database access.
- UUIDs make conversation and log writes safe across replicas.
- The ingestion endpoint is append-heavy and can be split into its own service.
- At higher volume, provider logs should be written to a queue first, then processed by idempotent consumers.
- Dashboard metrics should move from row scans to periodic rollups or a columnar analytics store.

## Failure Handling Assumptions

- If the provider fails, the chat request returns a structured stream error and logs an `error` inference row.
- If a browser aborts a stream, the app marks the inference as `cancelled` when cancellation reaches the server.
- If ingestion fails after the model response succeeds, the API surfaces the chat response and logs the ingestion failure server-side. A production version should use an outbox table or durable queue for retry.
- The demo stores redacted messages only; raw prompts are transient request data.
