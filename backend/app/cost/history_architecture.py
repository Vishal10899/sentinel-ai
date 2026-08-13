"""Future-ready Cost History & Storage Architecture.

Defines DTOs, Repository interfaces, Projections, and Events for future database persistence
and observability dashboards without introducing runtime dependencies or DB schema changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CostRecordDTO:
    """Historical cost event record DTO."""

    record_id: str
    request_id: str
    user_id: str
    workspace_id: str
    provider_id: str
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cost_usd: Decimal
    completion_cost_usd: Decimal
    total_cost_usd: Decimal
    baseline_cost_usd: Decimal
    savings_usd: Decimal
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_cost_usd": float(self.prompt_cost_usd),
            "completion_cost_usd": float(self.completion_cost_usd),
            "total_cost_usd": float(self.total_cost_usd),
            "baseline_cost_usd": float(self.baseline_cost_usd),
            "savings_usd": float(self.savings_usd),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True, slots=True)
class MonthlyProjection:
    """Monthly workspace cost projection DTO."""

    workspace_id: str
    current_month_cost_usd: float
    projected_monthly_cost_usd: float
    daily_run_rate_usd: float
    total_requests: int
    average_cost_per_request_usd: float

    def to_dict(self) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "current_month_cost_usd": self.current_month_cost_usd,
            "projected_monthly_cost_usd": self.projected_monthly_cost_usd,
            "daily_run_rate_usd": self.daily_run_rate_usd,
            "total_requests": self.total_requests,
            "average_cost_per_request_usd": self.average_cost_per_request_usd,
        }


@dataclass(frozen=True, slots=True)
class CostRecordedEvent:
    """Domain Event emitted when request execution cost is recorded."""

    event_id: str
    request_id: str
    user_id: str
    workspace_id: str
    total_cost_usd: float
    savings_usd: float
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "event_type": "CostRecordedEvent",
            "event_id": self.event_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "total_cost_usd": self.total_cost_usd,
            "savings_usd": self.savings_usd,
            "timestamp": self.timestamp,
        }


class ICostRepository(ABC):
    """Abstract repository contract for future cost history persistence."""

    @abstractmethod
    async def record_cost(self, dto: CostRecordDTO) -> None:
        """Persist a cost record."""

    @abstractmethod
    async def get_monthly_projection(self, workspace_id: str) -> MonthlyProjection:
        """Calculate monthly cost projections."""

    @abstractmethod
    async def list_records(self, workspace_id: str, limit: int = 100) -> tuple[CostRecordDTO, ...]:
        """Fetch cost history records for a workspace."""
