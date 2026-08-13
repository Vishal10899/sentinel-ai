import time
from uuid import uuid4
from typing import Any

from app.finops.models import CostAlert, UserQuota, WorkspaceBudget


class FinOpsRepository:
    """Repository storing workspace budgets, quotas, cost logs, and alerts."""

    def __init__(self) -> None:
        self._budgets: dict[str, WorkspaceBudget] = {}
        self._quotas: dict[str, UserQuota] = {}
        self._spend_records: list[dict[str, Any]] = []
        self._alerts: list[CostAlert] = []

        # Seed default workspace budget
        self.get_or_create_budget("default")

    def get_or_create_budget(self, workspace_id: str, monthly_budget_usd: float = 500.0) -> WorkspaceBudget:
        if workspace_id not in self._budgets:
            self._budgets[workspace_id] = WorkspaceBudget(workspace_id=workspace_id, monthly_budget_usd=monthly_budget_usd)
        return self._budgets[workspace_id]

    def update_budget(
        self,
        workspace_id: str,
        monthly_budget_usd: float | None = None,
        action_on_exceeded: str | None = None,
    ) -> WorkspaceBudget:
        budget = self.get_or_create_budget(workspace_id)
        if monthly_budget_usd is not None:
            budget.monthly_budget_usd = monthly_budget_usd
        if action_on_exceeded is not None:
            budget.action_on_exceeded = action_on_exceeded
        return budget

    def get_user_quota(self, user_id: str) -> UserQuota:
        if user_id not in self._quotas:
            self._quotas[user_id] = UserQuota(user_id=user_id)
        return self._quotas[user_id]

    def record_spend(
        self,
        workspace_id: str,
        user_id: str,
        provider_id: str,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: float,
    ) -> None:
        """Record transaction spend and update current workspace & user metrics."""
        now = time.time()
        record = {
            "id": str(uuid4()),
            "timestamp": now,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "provider_id": provider_id,
            "model_id": model_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": cost_usd,
        }
        self._spend_records.append(record)

        # Update budget spend
        budget = self.get_or_create_budget(workspace_id)
        budget.current_spend_usd = round(budget.current_spend_usd + cost_usd, 6)

        # Update user quota metrics
        quota = self.get_user_quota(user_id)
        quota.current_daily_tokens += (prompt_tokens + completion_tokens)
        quota.current_daily_requests += 1

    def add_alert(self, alert: CostAlert) -> None:
        self._alerts.append(alert)

    def list_alerts(self, workspace_id: str | None = None) -> list[CostAlert]:
        alerts = list(reversed(self._alerts))
        if workspace_id:
            alerts = [a for a in alerts if a.workspace_id == workspace_id]
        return alerts

    def get_spend_records(self, workspace_id: str | None = None) -> list[dict[str, Any]]:
        records = self._spend_records
        if workspace_id:
            records = [r for r in records if r["workspace_id"] == workspace_id]
        return records


finops_repository = FinOpsRepository()
