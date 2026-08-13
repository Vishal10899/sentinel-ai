import time
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class WorkspaceBudget:
    """Workspace Monthly Budget governance configuration."""

    workspace_id: str
    monthly_budget_usd: float = 500.0
    current_spend_usd: float = 0.0
    alert_thresholds: list[float] = field(default_factory=lambda: [0.50, 0.75, 0.90, 0.95, 1.00])
    triggered_alerts: list[float] = field(default_factory=list)
    action_on_exceeded: str = "REJECT"  # REJECT, WARN, DOWNGRADE_MODEL
    is_active: bool = True

    def percentage_used(self) -> float:
        if self.monthly_budget_usd <= 0:
            return 0.0
        return round((self.current_spend_usd / self.monthly_budget_usd) * 100, 1)

    def remaining_budget(self) -> float:
        return max(0.0, self.monthly_budget_usd - self.current_spend_usd)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["percentage_used"] = self.percentage_used()
        d["remaining_budget"] = self.remaining_budget()
        return d


@dataclass
class UserQuota:
    """Per-user daily token and request quota allocations."""

    user_id: str
    daily_token_quota: int = 250000
    current_daily_tokens: int = 0
    daily_request_quota: int = 500
    current_daily_requests: int = 0
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CostAlert:
    """Financial threshold alert notification."""

    id: str
    workspace_id: str
    threshold_pct: float
    message: str
    timestamp: float = field(default_factory=time.time)
    severity: str = "WARNING"  # INFO, WARNING, CRITICAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
