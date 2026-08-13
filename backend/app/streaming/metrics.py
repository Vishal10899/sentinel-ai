from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StreamMetrics:
    """Telemetry and performance metrics recorded for an active or completed AI stream."""

    stream_id: str
    conversation_id: str
    workspace_id: str
    provider: str
    model: str
    routing_strategy: str = "balanced"
    start_time: datetime = field(default_factory=datetime.utcnow)
    first_token_time: datetime | None = None
    end_time: datetime | None = None
    first_token_latency_ms: int = 0
    total_latency_ms: int = 0
    stream_duration_sec: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tokens_per_second: float = 0.0
    estimated_cost: float = 0.0
    retry_count: int = 0
    cache_hit: bool = False
    cancelled: bool = False
    timeout: bool = False
    failover: bool = False
    failover_provider: str | None = None

    def mark_first_token(self) -> None:
        if self.first_token_time is None:
            self.first_token_time = datetime.utcnow()
            self.first_token_latency_ms = int(
                (self.first_token_time - self.start_time).total_seconds() * 1000
            )

    def finalize(self) -> None:
        self.end_time = datetime.utcnow()
        self.total_latency_ms = int(
            (self.end_time - self.start_time).total_seconds() * 1000
        )
        self.stream_duration_sec = (self.end_time - self.start_time).total_seconds()
        self.total_tokens = self.prompt_tokens + self.completion_tokens
        if self.stream_duration_sec > 0 and self.completion_tokens > 0:
            self.tokens_per_second = round(
                self.completion_tokens / self.stream_duration_sec, 2
            )
