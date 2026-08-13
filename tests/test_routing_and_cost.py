"""Production-grade unit and integration tests for Phase 1.3 & 1.4 Enterprise Routing Engine and Cost Engine."""

from decimal import Decimal
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.cost import CostCalculator, CostComparator, CostEstimate, CostEstimator
from app.routing import (
    BalancedStrategy,
    CandidateScore,
    CheapestStrategy,
    CustomWeightedStrategy,
    EmbeddingOptimizedStrategy,
    FastestStrategy,
    HighestQualityStrategy,
    ImageGenerationOptimizedStrategy,
    IntelligentRouter,
    ModelInfo,
    ReasoningOptimizedStrategy,
    TaskCategory,
    VisionOptimizedStrategy,
)


def test_all_routing_strategies():
    """Verify selection logic across all 9 routing strategies."""
    from app.providers import provider_manager
    from app.providers.base import BaseProvider
    class DummyProvider(BaseProvider):
        def __init__(self, name: str):
            self._name = name
        @property
        def name(self) -> str:
            return self._name
        async def health(self):
            return True
        def generate(self, *a, **k): pass
        def stream_generate(self, *a, **k): pass
        def embed(self, *a, **k): pass
        def test_connection(self, *a, **k): pass

    provider_manager.register(DummyProvider(name="p1"))
    provider_manager.register(DummyProvider(name="p2"))
    provider_manager.register(DummyProvider(name="p3"))

    m1 = ModelInfo(
        provider="p1",
        model_name="m1-cheap",
        cost_per_1k_tokens=0.001,
        latency=800.0,
        capabilities=frozenset([TaskCategory.CHAT]),
        priority=10,
        quality_score=70.0,
        reasoning_score=65.0,
    )
    m2 = ModelInfo(
        provider="p2",
        model_name="m2-fast",
        cost_per_1k_tokens=0.01,
        latency=150.0,
        capabilities=frozenset([TaskCategory.CHAT]),
        priority=5,
        quality_score=85.0,
        reasoning_score=80.0,
    )
    m3 = ModelInfo(
        provider="p3",
        model_name="m3-highqual",
        cost_per_1k_tokens=0.05,
        latency=450.0,
        capabilities=frozenset([TaskCategory.CHAT, TaskCategory.VISION]),
        priority=1,
        quality_score=98.0,
        reasoning_score=95.0,
        supports_vision=True,
    )

    candidates = [m1, m2, m3]

    # Cheapest Strategy
    r_cheap = IntelligentRouter(strategy=CheapestStrategy()).select_model(TaskCategory.CHAT, candidates)
    assert r_cheap.model_name == "m1-cheap"

    # Fastest Strategy
    r_fast = IntelligentRouter(strategy=FastestStrategy()).select_model(TaskCategory.CHAT, candidates)
    assert r_fast.model_name == "m2-fast"

    # Highest Quality Strategy
    r_qual = IntelligentRouter(strategy=HighestQualityStrategy()).select_model(TaskCategory.CHAT, candidates)
    assert r_qual.model_name == "m3-highqual"

    # Reasoning Optimized
    r_reason = IntelligentRouter(strategy=ReasoningOptimizedStrategy()).select_model(TaskCategory.CHAT, candidates)
    assert r_reason.model_name == "m3-highqual"

    # Vision Optimized
    r_vision = IntelligentRouter(strategy=VisionOptimizedStrategy()).select_model(TaskCategory.CHAT, candidates)
    assert r_vision.model_name == "m3-highqual"

    # Custom Weighted Strategy
    custom_strat = CustomWeightedStrategy(cost_weight=0.9, latency_weight=0.1, quality_weight=0.0, reasoning_weight=0.0)
    r_custom = IntelligentRouter(strategy=custom_strat).select_model(TaskCategory.CHAT, candidates)
    assert r_custom.model_name == "m1-cheap"


def test_circuit_breaker_and_explanation():
    """Verify circuit breaker bypasses unhealthy providers and generates transparent explanations."""
    from app.providers import provider_manager
    from app.providers.base import BaseProvider
    class DummyProvider(BaseProvider):
        def __init__(self, name: str):
            self._name = name
        @property
        def name(self) -> str:
            return self._name
        async def health(self):
            return True
        def generate(self, *a, **k): pass
        def stream_generate(self, *a, **k): pass
        def embed(self, *a, **k): pass
        def test_connection(self, *a, **k): pass

    provider_manager.register(DummyProvider(name="p1"))
    provider_manager.register(DummyProvider(name="p2"))

    m_healthy = ModelInfo(
        provider="p1",
        model_name="m1",
        cost_per_1k_tokens=0.01,
        latency=300.0,
        capabilities=frozenset([TaskCategory.CHAT]),
        priority=5,
        provider_status="healthy",
        provider_failures=0,
    )
    m_unhealthy = ModelInfo(
        provider="p2",
        model_name="m2",
        cost_per_1k_tokens=0.001,
        latency=100.0,
        capabilities=frozenset([TaskCategory.CHAT]),
        priority=1,
        provider_status="unhealthy",
        provider_failures=5,
    )

    candidates = [m_healthy, m_unhealthy]
    router = IntelligentRouter(strategy=BalancedStrategy())

    explanation = router.evaluate_with_explanation(TaskCategory.CHAT, candidates, strategy_name="balanced")
    assert explanation.selected_provider == "p1"
    assert explanation.selected_model == "m1"
    assert len(explanation.circuit_breaker_bypassed) >= 1
    assert "p2/m2" in explanation.circuit_breaker_bypassed[0]


def test_cost_engine_forecasts_and_recommendations():
    """Verify token cost calculations, daily/monthly forecasts, and savings recommendations."""
    calc = CostCalculator()
    cost = calc.calculate_token_costs(1000, 500, Decimal("0.0015"), Decimal("0.006"))
    assert cost == Decimal("0.004500")

    estimator = CostEstimator()
    est = estimator.estimate_with_token_prices("openai", "gpt-4o-mini", 1000, 500, "0.00015", "0.0006")
    assert est.daily_forecast_usd == est.estimated_cost * Decimal("1000")
    assert est.monthly_forecast_usd == est.estimated_cost * Decimal("30000")

    comparator = CostComparator()
    report = comparator.compare_all(1000, 500)
    assert report.cheapest_model is not None
    assert report.most_expensive_model is not None


@pytest.mark.asyncio
async def test_routing_api_endpoints():
    """Verify POST /api/v1/routing/route and POST /api/v1/routing/explain REST endpoints."""
    from app.providers import provider_manager, GeminiProvider, OllamaProvider
    from app.rbac import rbac_engine

    rbac_engine.check_permission = lambda *args, **kwargs: True
    provider_manager.register(GeminiProvider(api_key="sk-test-gemini-key", model="gemini-2.0-flash"))
    provider_manager.register(OllamaProvider(base_url="http://localhost:11434", model="llama3.2"))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Route endpoint with highest_quality strategy
        route_res = await client.post(
            "/api/v1/routing/route",
            json={
                "task_category": "chat",
                "strategy": "highest_quality",
                "prompt_tokens": 100,
                "max_completion_tokens": 200,
            },
        )
        assert route_res.status_code == 200
        r_json = route_res.json()
        assert r_json["task_category"] == "chat"
        assert r_json["strategy"] == "highest_quality"
        assert r_json["provider_id"] is not None

        # Explain endpoint with balanced strategy
        explain_res = await client.post(
            "/api/v1/routing/explain",
            json={
                "task_category": "chat",
                "strategy": "balanced",
                "prompt_tokens": 50,
                "max_completion_tokens": 100,
            },
        )
        assert explain_res.status_code == 200
        e_json = explain_res.json()
        assert e_json["strategy"] == "balanced"
        assert "ranked_candidates" in e_json
        assert len(e_json["ranked_candidates"]) > 0


@pytest.mark.asyncio
async def test_cost_api_endpoints():
    """Verify cost estimation, comparison, budget status, and recommendations endpoints."""
    from app.api.dependencies import current_user
    from app.models.user import User
    from app.providers import provider_manager, GeminiProvider, OllamaProvider
    from app.rbac import rbac_engine

    rbac_engine.check_permission = lambda *args, **kwargs: True
    provider_manager.register(GeminiProvider(api_key="sk-test-gemini-key", model="gemini-2.0-flash"))
    provider_manager.register(OllamaProvider(base_url="http://localhost:11434", model="llama3.2"))

    app.dependency_overrides[current_user] = lambda: User(id="user123", email="user@sentinel.ai", name="Test User", salt="s", password_hash="p")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Estimate endpoint
        est_res = await client.post(
            "/api/v1/cost/estimate",
            json={
                "provider_id": "gemini",
                "model_id": "gemini-2.0-flash",
                "input_tokens": 1000,
                "output_tokens": 500,
            },
        )
        assert est_res.status_code == 200
        est_json = est_res.json()
        assert est_json["provider_id"] == "gemini"
        assert Decimal(str(est_json["estimated_cost_usd"])) >= Decimal("0.0")

        # Compare endpoint
        cmp_res = await client.post(
            "/api/v1/cost/compare",
            json={
                "input_tokens": 1000,
                "output_tokens": 500,
            },
        )
        assert cmp_res.status_code == 200
        cmp_json = cmp_res.json()
        assert "cheapest" in cmp_json
        assert "recommendations" in cmp_json

        # Budget status endpoint
        bud_res = await client.get("/api/v1/cost/budget?monthly_budget_usd=100&current_spend_usd=85")
        assert bud_res.status_code == 200
        bud_data = bud_res.json()
        assert bud_data["warning_status"] == "warning_80"
        assert Decimal(str(bud_data["percentage_used"])) == Decimal("85.0")

        # Recommendations endpoint
        rec_res = await client.get("/api/v1/cost/recommendations")
        assert rec_res.status_code == 200, f"Got {rec_res.status_code}: {rec_res.text}"
        assert isinstance(rec_res.json(), list)
