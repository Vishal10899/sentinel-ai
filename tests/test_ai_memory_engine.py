import pytest
from app.cache.semantic import SemanticCache
from app.cache.store import CacheStore


def test_exact_match_retrieval():
    store = CacheStore()
    cache = SemanticCache(store=store)

    prompt = "What is the capital of France?"
    response = "The capital of France is Paris."

    cache.set(
        prompt=prompt,
        response_text=response,
        workspace_id="ws-prod-1",
        provider_id="ollama",
        model_id="llama3.2",
        estimated_cost_usd=0.0,
        latency_ms=120.0,
        total_tokens=45,
    )

    hit = cache.get(prompt, workspace_id="ws-prod-1", model_id="llama3.2")
    assert hit is not None
    assert hit["hit"] is True
    assert hit["hit_type"] == "exact"
    assert hit["response_text"] == response
    assert hit["similarity_score"] == 1.0


def test_semantic_similarity_match():
    store = CacheStore()
    cache = SemanticCache(store=store, default_threshold=0.50)

    prompt_orig = "Write a binary search algorithm in Python"
    response = "Here is the binary search function in Python..."

    cache.set(
        prompt=prompt_orig,
        response_text=response,
        workspace_id="ws-prod-1",
        provider_id="ollama",
        model_id="llama3.2",
        estimated_cost_usd=0.002,
        latency_ms=450.0,
        total_tokens=180,
    )

    # Similar query (high token overlap)
    similar_prompt = "Write binary search algorithm in Python"
    hit = cache.get(similar_prompt, workspace_id="ws-prod-1", model_id="llama3.2")

    assert hit is not None
    assert hit["hit"] is True
    assert hit["hit_type"] == "semantic"
    assert hit["response_text"] == response
    assert hit["similarity_score"] >= 0.50


def test_freshness_bypass_keywords():
    store = CacheStore()
    cache = SemanticCache(store=store)

    prompt_cached = "What is the stock price of Apple"
    response = "Apple stock price is $180."

    cache.set(
        prompt=prompt_cached,
        response_text=response,
        workspace_id="ws-finance",
        provider_id="openai",
        model_id="gpt-4o",
    )

    # Query with freshness keyword 'today' or 'latest'
    freshness_query_1 = "What is the stock price of Apple today"
    hit_1 = cache.get(freshness_query_1, workspace_id="ws-finance", model_id="gpt-4o")
    assert hit_1 is None  # Bypassed cache for fresh execution!

    freshness_query_2 = "What is the latest stock price of Apple"
    hit_2 = cache.get(freshness_query_2, workspace_id="ws-finance", model_id="gpt-4o")
    assert hit_2 is None  # Bypassed cache for fresh execution!


def test_workspace_isolation():
    store = CacheStore()
    cache = SemanticCache(store=store)

    prompt = "Explain confidential company Q3 strategy"
    response_ws1 = "Secret strategy for Workspace 1..."

    cache.set(
        prompt=prompt,
        response_text=response_ws1,
        workspace_id="workspace-alpha",
        provider_id="ollama",
        model_id="llama3.2",
    )

    # Query from workspace-beta must NOT return workspace-alpha data!
    hit_ws2 = cache.get(prompt, workspace_id="workspace-beta", model_id="llama3.2")
    assert hit_ws2 is None

    # Query from workspace-alpha returns entry
    hit_ws1 = cache.get(prompt, workspace_id="workspace-alpha", model_id="llama3.2")
    assert hit_ws1 is not None
    assert hit_ws1["response_text"] == response_ws1


def test_cache_analytics_telemetry():
    store = CacheStore()
    cache = SemanticCache(store=store)

    cache.set(
        prompt="Explain quantum computing",
        response_text="Quantum computing uses qubits...",
        workspace_id="ws-1",
        estimated_cost_usd=0.005,
        latency_ms=800.0,
        total_tokens=250,
    )

    # Perform 1 hit and 1 miss
    cache.get("Explain quantum computing", workspace_id="ws-1")
    cache.get("What is deep learning?", workspace_id="ws-1")

    metrics = cache.get_metrics()
    assert metrics["total_requests"] == 2
    assert metrics["exact_hits"] == 1
    assert metrics["misses"] == 1
    assert metrics["hit_rate_pct"] == 50.0
    assert metrics["total_cost_saved_usd"] == 0.005
    assert metrics["total_tokens_saved"] == 250
    assert metrics["avg_latency_saved_ms"] == 800.0


def test_cache_miss():
    store = CacheStore()
    cache = SemanticCache(store=store)

    hit = cache.get("Uncached query for quantum physics", workspace_id="ws-test")
    assert hit is None
    assert cache.metrics.misses == 1


def test_ttl_expiration():
    import time
    store = CacheStore()
    cache = SemanticCache(store=store)

    # Set entry with short 1-second TTL
    cache.set(
        prompt="Ephemeral prompt",
        response_text="Ephemeral answer",
        workspace_id="ws-ttl",
        ttl_seconds=1,
    )

    # Immediate lookup hits
    assert cache.get("Ephemeral prompt", workspace_id="ws-ttl") is not None

    # Wait for TTL expiry
    time.sleep(1.1)

    # Post-TTL lookup misses and evicts expired entry
    assert cache.get("Ephemeral prompt", workspace_id="ws-ttl") is None


def test_routing_engine_non_regression():
    from app.providers import provider_manager, GeminiProvider, OllamaProvider
    from app.orchestration.router import adaptive_router

    provider_manager.register(GeminiProvider(api_key="sk-test-gemini-key", model="gemini-2.0-flash"))
    provider_manager.register(OllamaProvider(base_url="http://localhost:11434", model="llama3.2"))

    # Verify AdaptiveRouter evaluates prompts correctly without cache regression
    res = adaptive_router.route("Write a Python function to sort a list")
    assert res.selected_provider in ["ollama", "gemini", "openai", "anthropic"]
    assert res.intent_detected in ["CODE_GENERATION", "CODING"]
    assert res.explanation_text is not None


def test_manual_cache_invalidation():
    store = CacheStore()
    cache = SemanticCache(store=store)

    cache.set("Prompt A", "Ans A", workspace_id="ws-dev")
    cache.set("Prompt B", "Ans B", workspace_id="ws-dev")
    cache.set("Prompt C", "Ans C", workspace_id="ws-prod")

    invalidated = cache.invalidate(workspace_id="ws-dev")
    assert invalidated == 2

    assert cache.get("Prompt A", workspace_id="ws-dev") is None
    assert cache.get("Prompt C", workspace_id="ws-prod") is not None
