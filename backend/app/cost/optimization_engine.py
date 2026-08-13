"""Rule-based Cost Optimization Engine.

Generates actionable optimization recommendations without requiring AI models.
"""

from dataclasses import dataclass, field
from app.models_registry import model_registry


@dataclass(frozen=True, slots=True)
class OptimizationRecommendation:
    """Actionable cost optimization recommendation."""

    rule_id: str
    category: str
    severity: str  # HIGH, MEDIUM, LOW
    title: str
    description: str
    potential_savings_pct: float
    recommended_action: str

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "potential_savings_pct": self.potential_savings_pct,
            "recommended_action": self.recommended_action,
        }


@dataclass(frozen=True, slots=True)
class CostOptimizationReport:
    """Full optimization analysis report."""

    evaluated_prompt_tokens: int
    selected_provider: str
    selected_model: str
    total_recommendations: int
    potential_savings_pct: float
    recommendations: tuple[OptimizationRecommendation, ...]

    def to_dict(self) -> dict:
        return {
            "evaluated_prompt_tokens": self.evaluated_prompt_tokens,
            "selected_provider": self.selected_provider,
            "selected_model": self.selected_model,
            "total_recommendations": self.total_recommendations,
            "potential_savings_pct": self.potential_savings_pct,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


class CostOptimizationEngine:
    """Rule-based AI cost optimization engine."""

    PREMIUM_MODELS = {"gpt-5", "gpt-4o", "claude-sonnet-4", "claude-3-5-sonnet", "o3-mini"}

    def generate_recommendations(
        self,
        prompt: str,
        selected_provider: str,
        selected_model: str,
        prompt_tokens: int,
        conversation_turns: int = 1,
    ) -> CostOptimizationReport:
        """Evaluate request context and generate rule-based cost recommendations."""
        recs: list[OptimizationRecommendation] = []
        max_savings = 0.0

        # Rule 1: Overuse of premium reasoning models on simple prompts
        if selected_model in self.PREMIUM_MODELS and prompt_tokens < 300 and len(prompt) < 1000:
            recs.append(
                OptimizationRecommendation(
                    rule_id="OPT-001",
                    category="MODEL_SELECTION",
                    severity="HIGH",
                    title="Overuse of Premium Model on Short Prompt",
                    description="This workload uses a frontier model for a short prompt. Switching to Gemini 2.0 Flash would reduce cost by ~78%.",
                    potential_savings_pct=78.0,
                    recommended_action="Route short general prompts to Gemini Flash or GPT-4o mini.",
                )
            )
            max_savings = max(max_savings, 78.0)

        # Rule 2: Local Ollama execution availability
        ollama_models = model_registry.list_models(provider="ollama", enabled_only=True)
        if ollama_models and selected_provider != "ollama" and prompt_tokens < 1500:
            recs.append(
                OptimizationRecommendation(
                    rule_id="OPT-002",
                    category="LOCAL_EXECUTION",
                    severity="MEDIUM",
                    title="Local Ollama Model Available",
                    description=f"Local open-source models ({', '.join(m.model_id for m in ollama_models[:2])}) are active. Routing to local execution eliminates 100% of token charges.",
                    potential_savings_pct=100.0,
                    recommended_action="Enable local Ollama fallback for internal development & staging queries.",
                )
            )
            max_savings = max(max_savings, 100.0)

        # Rule 3: Large prompt context threshold
        if prompt_tokens > 4000:
            recs.append(
                OptimizationRecommendation(
                    rule_id="OPT-003",
                    category="PROMPT_COMPRESSION",
                    severity="MEDIUM",
                    title="Large Prompt Context (>4,000 Tokens)",
                    description="Prompt length exceeds recommended size. Applying prompt compression or system prompt truncation saves ~40% token costs.",
                    potential_savings_pct=40.0,
                    recommended_action="Enable automated prompt compression or file chunk filtering.",
                )
            )
            max_savings = max(max_savings, 40.0)

        # Rule 4: Multi-turn conversation caching
        if conversation_turns > 5:
            recs.append(
                OptimizationRecommendation(
                    rule_id="OPT-004",
                    category="CONTEXT_CACHING",
                    severity="LOW",
                    title="Long Conversation History Detected",
                    description="Conversation thread exceeds 5 turns. Utilizing cached context tokens reduces repeated prompt token billing by up to 50%.",
                    potential_savings_pct=50.0,
                    recommended_action="Enable Anthropic / Gemini prompt caching for repeated conversation prefixes.",
                )
            )
            max_savings = max(max_savings, 50.0)

        return CostOptimizationReport(
            evaluated_prompt_tokens=prompt_tokens,
            selected_provider=selected_provider,
            selected_model=selected_model,
            total_recommendations=len(recs),
            potential_savings_pct=max_savings,
            recommendations=tuple(recs),
        )


cost_optimization_engine = CostOptimizationEngine()
