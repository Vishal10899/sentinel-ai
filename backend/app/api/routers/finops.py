"""Enterprise Financial Governance & Cost Analytics Router."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import current_user, require_permission
from app.finops.analytics import cost_analytics, cost_forecast, cost_optimizer
from app.finops.repository import finops_repository
from app.models.user import User

router = APIRouter(prefix="/finops", tags=["finops"])


class UpdateBudgetRequest(BaseModel):
    workspace_id: str = "default"
    monthly_budget_usd: float = Field(gt=0)
    action_on_exceeded: str = Field(default="REJECT", pattern="^(REJECT|WARN|DOWNGRADE_MODEL)$")


@router.get("/budgets", summary="Get workspace budgets")
async def get_budgets(workspace_id: str | None = Query(default=None), user: User = Depends(current_user)):
    """Retrieve workspace budget configuration and spend progress."""
    budget = finops_repository.get_or_create_budget(workspace_id or "default")
    return budget.to_dict()


@router.post("/budgets", summary="Create or update workspace budget")
async def update_budget(request: UpdateBudgetRequest, user: User = Depends(require_permission("billing.manage"))):

    """Configure monthly budget limit and enforcement behavior."""
    updated = finops_repository.update_budget(
        workspace_id=request.workspace_id,
        monthly_budget_usd=request.monthly_budget_usd,
        action_on_exceeded=request.action_on_exceeded,
    )
    return updated.to_dict()


@router.get("/quotas", summary="Get user quotas")
async def get_quotas(user: User = Depends(current_user)):
    """Retrieve user daily token and request quota metrics."""
    quota = finops_repository.get_user_quota(user.id)
    return quota.to_dict()


@router.get("/analytics/spend", summary="Get multi-dimensional spend summary")
async def get_spend_summary(workspace_id: str | None = Query(default=None), user: User = Depends(current_user)):
    """Retrieve spend summary aggregated by provider, model, workspace, and user."""
    summary = cost_analytics.get_summary(workspace_id=workspace_id)
    return {
        "total_spend_usd": summary.total_spend_usd,
        "total_tokens": summary.total_tokens,
        "total_requests": summary.total_requests,
        "spend_by_provider": summary.spend_by_provider,
        "spend_by_model": summary.spend_by_model,
        "spend_by_workspace": summary.spend_by_workspace,
        "spend_by_user": summary.spend_by_user,
    }


@router.get("/analytics/forecast", summary="Get end-of-month spend forecast")
async def get_forecast(workspace_id: str = Query(default="default"), user: User = Depends(current_user)):
    """Retrieve end-of-month spend forecast and budget exhaustion projections."""
    return cost_forecast.forecast_spend(workspace_id=workspace_id)


@router.get("/analytics/alerts", summary="Get budget threshold alerts")
async def get_alerts(workspace_id: str | None = Query(default=None), user: User = Depends(current_user)):
    """Retrieve threshold alerts (50%, 75%, 90%, 95%, 100%)."""
    alerts = finops_repository.list_alerts(workspace_id=workspace_id)
    return [a.to_dict() for a in alerts]


@router.get("/analytics/optimization", summary="Get AI cost optimization recommendations")
async def get_optimizations(user: User = Depends(current_user)):
    """Retrieve actionable cost savings recommendations across providers and models."""
    return cost_optimizer.generate_recommendations()
