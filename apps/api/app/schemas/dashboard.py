from app.schemas.common import ApiModel


class ModelMetric(ApiModel):
    provider: str
    model: str
    requests: int
    errors: int
    avg_latency_ms: float
    total_tokens: int


class ThroughputPoint(ApiModel):
    minute: str
    requests: int
    errors: int


class DashboardSummary(ApiModel):
    total_requests: int
    error_rate: float
    avg_latency_ms: float
    total_tokens: int
    requests_per_minute: float
    models: list[ModelMetric]
    throughput: list[ThroughputPoint]
    recent_errors: list[str]
