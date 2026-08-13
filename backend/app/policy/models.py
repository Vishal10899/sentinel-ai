"""Runtime Policy Platform Domain Models."""

from dataclasses import dataclass, field
import datetime
from enum import Enum
from typing import Any
import uuid


class PolicyAction(str, Enum):
    """Actions supported by the Runtime Policy Engine."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    BLOCK = "BLOCK"
    WARN = "WARN"
    REDIRECT = "REDIRECT"
    FALLBACK = "FALLBACK"
    LOG_ONLY = "LOG_ONLY"
    MODIFY = "MODIFY"


class BudgetAction(str, Enum):
    """Actions when budget threshold is exceeded."""

    BLOCK = "BLOCK"
    DOWNGRADE_MODEL = "DOWNGRADE_MODEL"


@dataclass
class AIPolicy:
    """Enterprise AI Governance Policy definition."""

    id: str
    name: str
    workspace_id: str = "default"
    is_active: bool = True
    description: str = ""

    # Budget Enforcement Thresholds
    daily_budget_usd: float | None = None
    monthly_budget_limit_usd: float | None = None
    workspace_budget_usd: float | None = None
    user_budget_usd: float | None = None
    provider_budget_usd: float | None = None
    budget_action: BudgetAction = BudgetAction.BLOCK

    current_spend_usd: float = 0.0
    daily_spend_usd: float = 0.0

    # Provider & Model & Region Restrictions
    allowed_providers: tuple[str, ...] = field(default_factory=tuple)
    blocked_providers: tuple[str, ...] = field(default_factory=tuple)
    allowed_models: tuple[str, ...] = field(default_factory=tuple)
    blocked_models: tuple[str, ...] = field(default_factory=tuple)
    restricted_regions: tuple[str, ...] = field(default_factory=tuple)
    restricted_capabilities: tuple[str, ...] = field(default_factory=tuple)
    restrict_premium_models: bool = False
    restrict_external_providers: bool = False

    # Prompt Security Rules
    detect_pii: bool = True
    detect_secrets: bool = True
    detect_credentials: bool = True
    blocked_keywords: tuple[str, ...] = field(default_factory=tuple)
    max_prompt_tokens: int | None = 4000
    max_tokens: int | None = 4096
    max_temperature: float | None = 1.0

    # Fallback & Redirect Config
    fallback_model: str = "gemini-2.0-flash"
    redirect_provider: str | None = None
    redirect_model: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "workspace_id": self.workspace_id,
            "is_active": self.is_active,
            "description": self.description,
            "daily_budget_usd": self.daily_budget_usd,
            "monthly_budget_limit_usd": self.monthly_budget_limit_usd,
            "workspace_budget_usd": self.workspace_budget_usd,
            "user_budget_usd": self.user_budget_usd,
            "provider_budget_usd": self.provider_budget_usd,
            "budget_action": self.budget_action.value,
            "current_spend_usd": self.current_spend_usd,
            "daily_spend_usd": self.daily_spend_usd,
            "allowed_providers": list(self.allowed_providers),
            "blocked_providers": list(self.blocked_providers),
            "allowed_models": list(self.allowed_models),
            "blocked_models": list(self.blocked_models),
            "restricted_regions": list(self.restricted_regions),
            "restricted_capabilities": list(self.restricted_capabilities),
            "restrict_premium_models": self.restrict_premium_models,
            "restrict_external_providers": self.restrict_external_providers,
            "detect_pii": self.detect_pii,
            "detect_secrets": self.detect_secrets,
            "detect_credentials": self.detect_credentials,
            "blocked_keywords": list(self.blocked_keywords),
            "max_prompt_tokens": self.max_prompt_tokens,
            "max_tokens": self.max_tokens,
            "max_temperature": self.max_temperature,
            "fallback_model": self.fallback_model,
            "redirect_provider": self.redirect_provider,
            "redirect_model": self.redirect_model,
        }


@dataclass
class PolicyDecision:
    """Evaluation output produced by the Policy Engine."""

    action: PolicyAction
    reason: str
    policy_id: str | None = None
    policy_name: str | None = None
    redirect_provider: str | None = None
    redirect_model: str | None = None
    fallback_model: str | None = None
    modified_request: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    evaluation_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "redirect_provider": self.redirect_provider,
            "redirect_model": self.redirect_model,
            "fallback_model": self.fallback_model,
            "modified_request": self.modified_request,
            "warnings": self.warnings,
            "evaluation_time_ms": self.evaluation_time_ms,
        }


@dataclass(frozen=True, slots=True)
class PolicyAuditLogRecord:
    """Policy decision audit log record."""

    log_id: str
    policy_id: str | None
    policy_name: str | None
    decision: str
    reason: str
    user_id: str
    workspace_id: str
    request_id: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "log_id": self.log_id,
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "decision": self.decision,
            "reason": self.reason,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
        }
