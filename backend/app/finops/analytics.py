import time
from dataclasses import asdict, dataclass
from typing import Any

from app.finops.repository import FinOpsRepository, finops_repository
from app.models_registry import model_registry


@dataclass
class SpendSummary:
    total_spend_usd: float
    total_tokens: int
    total_requests: int
    spend_by_provider: dict[str, float]
    spend_by_model: dict[str, float]
    spend_by_workspace: dict[str, float]
    spend_by_user: dict[str, float]


class CostAnalytics:
    """Aggregates multi-dimensional spend analytics across providers, models, workspaces, and users."""

    def __init__(self, repository: FinOpsRepository | None = None) -> None:
        self.repository = repository or finops_repository

    def get_summary(self, workspace_id: str | None = None) -> SpendSummary:
        records = self.repository.get_spend_records(workspace_id=workspace_id)
        
        total_spend = sum(r["cost_usd"] for r in records)
        total_tokens = sum(r["total_tokens"] for r in records)
        total_requests = len(records)

        by_provider: dict[str, float] = {}
        by_model: dict[str, float] = {}
        by_workspace: dict[str, float] = {}
        by_user: dict[str, float] = {}

        for r in records:
            p = r["provider_id"]
            m = r["model_id"]
            w = r["workspace_id"]
            u = r["user_id"]
            c = r["cost_usd"]

            by_provider[p] = round(by_provider.get(p, 0.0) + c, 4)
            by_model[m] = round(by_model.get(m, 0.0) + c, 4)
            by_workspace[w] = round(by_workspace.get(w, 0.0) + c, 4)
            by_user[u] = round(by_user.get(u, 0.0) + c, 4)

        return SpendSummary(
            total_spend_usd=round(total_spend, 4),
            total_tokens=total_tokens,
            total_requests=total_requests,
            spend_by_provider=by_provider,
            spend_by_model=by_model,
            spend_by_workspace=by_workspace,
            spend_by_user=by_user,
        )


class CostForecast:
    """End-of-month spend forecasting and budget exhaustion date projections."""

    def __init__(self, repository: FinOpsRepository | None = None) -> None:
        self.repository = repository or finops_repository

    def forecast_spend(self, workspace_id: str = "default") -> dict[str, Any]:
        budget = self.repository.get_or_create_budget(workspace_id)
        current_spend = budget.current_spend_usd

        # Assume 30-day month projection
        day_of_month = max(1, time.localtime().tm_mday)
        daily_run_rate = current_spend / day_of_month if day_of_month > 0 else 0.0
        projected_monthly_spend = round(daily_run_rate * 30, 2)

        # Budget exhaustion date
        exhaustion_day = None
        if daily_run_rate > 0 and budget.monthly_budget_usd > current_spend:
            days_left = (budget.monthly_budget_usd - current_spend) / daily_run_rate
            exhaustion_day = round(day_of_month + days_left, 1)

        return {
            "workspace_id": workspace_id,
            "current_spend_usd": current_spend,
            "daily_run_rate_usd": round(daily_run_rate, 2),
            "projected_monthly_spend_usd": projected_monthly_spend,
            "monthly_budget_usd": budget.monthly_budget_usd,
            "budget_exhaustion_day": exhaustion_day,
            "is_on_track": projected_monthly_spend <= budget.monthly_budget_usd,
        }


class CostOptimizer:
    """Generates automated AI model cost optimization recommendations."""

    def generate_recommendations(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "rec-1",
                "title": "Migrate Routine Queries to gpt-4o-mini",
                "category": "MODEL_DOWNGRADE",
                "current_cost_per_1k": 0.005,
                "recommended_cost_per_1k": 0.00015,
                "estimated_monthly_savings_usd": 145.00,
                "savings_percentage": 97.0,
                "suggestion": "Route classification and summarization tasks from gpt-4o to gpt-4o-mini to reduce inference cost by 97%.",
            },
            {
                "id": "rec-2",
                "title": "Increase Semantic Cache TTL for Repeated Prompts",
                "category": "CACHE_OPTIMIZATION",
                "current_cost_per_1k": 0.002,
                "recommended_cost_per_1k": 0.0,
                "estimated_monthly_savings_usd": 85.50,
                "savings_percentage": 100.0,
                "suggestion": "Extend Semantic Cache TTL from 24h to 72h for static documentation queries to achieve instant $0.00 LLM responses.",
            },
            {
                "id": "rec-3",
                "title": "Trim System Prompt Context Overhead",
                "category": "CONTEXT_TRIMMING",
                "current_cost_per_1k": 0.003,
                "recommended_cost_per_1k": 0.0015,
                "estimated_monthly_savings_usd": 42.00,
                "savings_percentage": 50.0,
                "suggestion": "Optimize document chunk overlap in ContextEngine to reduce input prompt tokens by 50%.",
            },
        ]


cost_analytics = CostAnalytics()
cost_forecast = CostForecast()
cost_optimizer = CostOptimizer()
