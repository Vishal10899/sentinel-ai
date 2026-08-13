import time
from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class SimulationRequest:
    """Policy impact simulation request parameters."""

    workspace_id: str = "default"
    proposed_policy: dict[str, Any] = field(default_factory=dict)
    sample_trace_count: int = 100

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SimulationResult:
    """Dry-run policy impact simulation analysis."""

    total_requests: int
    allowed_count: int
    blocked_count: int
    rerouted_count: int
    cost_delta_usd: float
    latency_delta_ms: float
    impact_percentage: float
    affected_models: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyVersion:
    """Versioned Policy Configuration."""

    version_id: str
    version_number: str
    policy_data: dict[str, Any]
    published_by: str
    published_at: float = field(default_factory=time.time)
    is_active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizationRecommendation:
    """AI Optimization Advisor Recommendation."""

    id: str
    title: str
    category: str  # COST, ROUTING, LATENCY, CACHE
    description: str
    estimated_savings_usd: float
    confidence_score: float  # 0.0 to 1.0
    status: str = "PENDING"  # PENDING, APPLIED, DISMISSED
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
