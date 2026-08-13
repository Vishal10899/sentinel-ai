import time
from uuid import uuid4
from dataclasses import dataclass
from fastapi import HTTPException, status

from app.audit.engine import audit_engine
from app.finops.models import CostAlert, WorkspaceBudget
from app.finops.repository import FinOpsRepository, finops_repository


@dataclass
class BudgetEvaluationResult:
    allowed: bool
    status: str  # OK, WARN, EXCEEDED
    action: str  # ALLOW, REJECT, WARN, DOWNGRADE
    current_spend: float
    monthly_budget: float
    percentage_used: float
    reason: str


class BudgetEngine:
    """High-performance (<1ms) Budget Governance & Quota Enforcement Engine."""

    def __init__(self, repository: FinOpsRepository | None = None) -> None:
        self.repository = repository or finops_repository

    def evaluate_request(
        self,
        workspace_id: str,
        user_id: str = "default_user",
        estimated_cost: float = 0.0,
    ) -> BudgetEvaluationResult:
        """Evaluate pre-request budget and user quota constraints."""
        budget = self.repository.get_or_create_budget(workspace_id)
        if not budget.is_active:
            return BudgetEvaluationResult(
                allowed=True,
                status="OK",
                action="ALLOW",
                current_spend=budget.current_spend_usd,
                monthly_budget=budget.monthly_budget_usd,
                percentage_used=budget.percentage_used(),
                reason="Budget tracking inactive.",
            )

        projected_spend = budget.current_spend_usd + estimated_cost
        projected_pct = projected_spend / budget.monthly_budget_usd if budget.monthly_budget_usd > 0 else 0.0

        # Check threshold alerts (50%, 75%, 90%, 95%, 100%)
        for threshold in budget.alert_thresholds:
            if projected_pct >= threshold and threshold not in budget.triggered_alerts:
                budget.triggered_alerts.append(threshold)
                alert_msg = f"Workspace '{workspace_id}' budget reached {(threshold * 100):.0f}% of ${budget.monthly_budget_usd:.2f} limit."
                severity = "CRITICAL" if threshold >= 0.95 else "WARNING"
                
                alert = CostAlert(
                    id=str(uuid4()),
                    workspace_id=workspace_id,
                    threshold_pct=threshold,
                    message=alert_msg,
                    severity=severity,
                )
                self.repository.add_alert(alert)

                # Emit immutable audit event
                audit_engine.record_event(
                    action="BUDGET_ALERT_TRIGGERED",
                    resource=f"budgets/{workspace_id}",
                    user_id=user_id,
                    workspace_id=workspace_id,
                    new_value=f"Threshold: {(threshold * 100):.0f}%",
                    severity=severity,
                )

        # Enforce budget hard limit if exceeded
        if projected_spend > budget.monthly_budget_usd:
            if budget.action_on_exceeded == "REJECT":
                audit_engine.record_event(
                    action="BUDGET_LIMIT_EXCEEDED",
                    resource=f"budgets/{workspace_id}",
                    user_id=user_id,
                    workspace_id=workspace_id,
                    severity="CRITICAL",
                    status="DENIED",
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Monthly budget limit of ${budget.monthly_budget_usd:.2f} exceeded for workspace '{workspace_id}' (Current spend: ${budget.current_spend_usd:.2f}).",
                )
            elif budget.action_on_exceeded == "DOWNGRADE_MODEL":
                return BudgetEvaluationResult(
                    allowed=True,
                    status="EXCEEDED",
                    action="DOWNGRADE",
                    current_spend=budget.current_spend_usd,
                    monthly_budget=budget.monthly_budget_usd,
                    percentage_used=budget.percentage_used(),
                    reason="Budget exceeded. Request downgraded to low-cost model.",
                )

        return BudgetEvaluationResult(
            allowed=True,
            status="OK" if projected_pct < 0.9 else "WARN",
            action="ALLOW",
            current_spend=budget.current_spend_usd,
            monthly_budget=budget.monthly_budget_usd,
            percentage_used=budget.percentage_used(),
            reason="Budget evaluation approved.",
        )


budget_engine = BudgetEngine()
