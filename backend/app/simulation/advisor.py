from app.audit.engine import audit_engine
from app.simulation.models import OptimizationRecommendation


class OptimizationAdvisor:
    """AI Optimization Advisor Engine."""

    def __init__(self) -> None:
        self._recommendations: dict[str, OptimizationRecommendation] = {}
        self._seed_recommendations()

    def _seed_recommendations(self) -> None:
        recs = [
            OptimizationRecommendation(
                id="rec-opt-1",
                title="Route Simple Coding Prompts to DeepSeek-Coder",
                category="ROUTING",
                description="Analysis shows 45% of coding prompts are simple utility functions. Routing them to DeepSeek-Coder cuts cost by 65% with zero quality loss.",
                estimated_savings_usd=340.50,
                confidence_score=0.94,
            ),
            OptimizationRecommendation(
                id="rec-opt-2",
                title="Increase Semantic Cache TTL to 24 Hours",
                category="CACHE",
                description="Repeated documentation queries have a 32% hit rate. Extending TTL saves ~120,000 tokens daily.",
                estimated_savings_usd=185.00,
                confidence_score=0.91,
            ),
            OptimizationRecommendation(
                id="rec-opt-3",
                title="Downgrade Non-Production Models to GPT-4o-mini",
                category="COST",
                description="Staging & test workspaces consume $210/mo on GPT-4o. Downgrading to GPT-4o-mini reduces spend by 80%.",
                estimated_savings_usd=168.00,
                confidence_score=0.98,
            ),
        ]
        for r in recs:
            self._recommendations[r.id] = r

    def get_recommendations(self) -> list[OptimizationRecommendation]:
        return list(self._recommendations.values())

    def apply_recommendation(self, rec_id: str, actor_id: str = "admin") -> OptimizationRecommendation | None:
        rec = self._recommendations.get(rec_id)
        if not rec:
            return None

        rec.status = "APPLIED"

        audit_engine.record_event(
            action="OPTIMIZATION_ACCEPTED",
            resource=f"recommendations/{rec_id}",
            user_id=actor_id,
            workspace_id="default",
            new_value=f"Applied Recommendation: {rec.title}",
        )

        return rec


optimization_advisor = OptimizationAdvisor()
