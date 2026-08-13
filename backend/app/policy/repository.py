"""Policy Repository managing Enterprise Governance Policies and Policy Decision Audit Logs."""

import datetime
from typing import Any
import uuid

from app.policy.models import AIPolicy, BudgetAction, PolicyAuditLogRecord, PolicyDecision


class PolicyRepository:
    """Repository managing Enterprise Governance Policies and Policy Decision Audit Logs."""

    def __init__(self) -> None:
        self._policies: dict[str, AIPolicy] = {}
        self._audit_logs: list[PolicyAuditLogRecord] = []

        # Seed default workspace active policy
        default_policy = AIPolicy(
            id="default-policy-01",
            workspace_id="default",
            name="Default Workspace Policy",
            description="Standard enterprise policy allowing all configured providers and models.",
            allowed_providers=(),
            blocked_providers=(),
            allowed_models=(),
            blocked_models=(),
            max_tokens=4096,
            max_temperature=1.0,
            is_active=True,
        )
        self._policies[default_policy.id] = default_policy

    def list_policies(self, workspace_id: str | None = None) -> list[AIPolicy]:
        """List active policies optionally filtered by workspace_id."""
        policies = list(self._policies.values())
        if workspace_id:
            policies = [p for p in policies if p.workspace_id == workspace_id]
        return policies

    def get_policy(self, policy_id: str) -> AIPolicy | None:
        """Retrieve policy by ID."""
        return self._policies.get(policy_id)

    def create_policy(self, data: dict[str, Any]) -> AIPolicy:
        """Create a new governance policy."""
        policy_id = data.get("id") or str(uuid.uuid4())
        policy = AIPolicy(
            id=policy_id,
            workspace_id=data.get("workspace_id", "default"),
            name=data.get("name", "New Enterprise Policy"),
            description=data.get("description", ""),
            daily_budget_usd=data.get("daily_budget_usd"),
            monthly_budget_limit_usd=data.get("monthly_budget_limit_usd"),
            workspace_budget_usd=data.get("workspace_budget_usd"),
            user_budget_usd=data.get("user_budget_usd"),
            provider_budget_usd=data.get("provider_budget_usd"),
            budget_action=data.get("budget_action", BudgetAction.BLOCK),
            current_spend_usd=data.get("current_spend_usd", 0.0),
            daily_spend_usd=data.get("daily_spend_usd", 0.0),
            allowed_providers=tuple(data.get("allowed_providers", ())),
            blocked_providers=tuple(data.get("blocked_providers", ())),
            allowed_models=tuple(data.get("allowed_models", ())),
            blocked_models=tuple(data.get("blocked_models", ())),
            restricted_regions=tuple(data.get("restricted_regions", ())),
            restricted_capabilities=tuple(data.get("restricted_capabilities", ())),
            restrict_premium_models=data.get("restrict_premium_models", False),
            restrict_external_providers=data.get("restrict_external_providers", False),
            detect_pii=data.get("detect_pii", True),
            detect_secrets=data.get("detect_secrets", True),
            detect_credentials=data.get("detect_credentials", True),
            blocked_keywords=tuple(data.get("blocked_keywords", ())),
            max_prompt_tokens=data.get("max_prompt_tokens", 4000),
            max_tokens=data.get("max_tokens", 4096),
            max_temperature=data.get("max_temperature", 1.0),
            fallback_model=data.get("fallback_model", "gemini-2.0-flash"),
            redirect_provider=data.get("redirect_provider"),
            redirect_model=data.get("redirect_model"),
            is_active=data.get("is_active", True),
        )
        self._policies[policy.id] = policy
        return policy

    def record_log(
        self,
        policy: AIPolicy | None,
        decision: PolicyDecision,
        user_id: str = "default_user",
        workspace_id: str = "default",
        request_id: str = "",
    ) -> PolicyAuditLogRecord:
        """Record policy decision audit log."""
        log_rec = PolicyAuditLogRecord(
            log_id=f"plog-{uuid.uuid4().hex[:12]}",
            policy_id=policy.id if policy else None,
            policy_name=policy.name if policy else "Default Policy",
            decision=decision.action.value,
            reason=decision.reason,
            user_id=user_id,
            workspace_id=workspace_id,
            request_id=request_id or f"req-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
        self._audit_logs.append(log_rec)
        return log_rec

    def list_logs(self, workspace_id: str | None = None, limit: int = 100) -> list[PolicyAuditLogRecord]:
        """Fetch policy execution audit logs."""
        logs = list(reversed(self._audit_logs))
        if workspace_id:
            logs = [l for l in logs if l.workspace_id == workspace_id]
        return logs[:limit]


policy_repository = PolicyRepository()
