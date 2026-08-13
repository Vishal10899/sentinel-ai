import time
import pytest
from app.cache.semantic import SemanticCache
from app.cache.store import CacheEntry, CacheStore


def test_embedding_retrieval_and_cosine_similarity():
    cache = SemanticCache()

    prompt1 = "Write a Python script to connect to PostgreSQL database"
    prompt2 = "Write Python code to connect PostgreSQL database"
    prompt3 = "Bake a chocolate cake recipe"

    vec1 = cache.generate_embedding(prompt1)
    vec2 = cache.generate_embedding(prompt2)
    vec3 = cache.generate_embedding(prompt3)

    assert len(vec1) == 128
    assert len(vec2) == 128

    sim_high = cache.cosine_similarity(vec1, vec2)
    sim_low = cache.cosine_similarity(vec1, vec3)

    assert sim_high > 0.70
    assert sim_high > sim_low


def test_confidence_scoring():
    store = CacheStore()
    cache = SemanticCache(store=store)

    entry = CacheEntry(
        key="test-key",
        workspace_id="ws-prod",
        prompt="Build a React component for user login",
        normalized_prompt="build a react component for user login",
        response_text="const Login = () => { ... }",
        provider_id="ollama",
        model_id="llama3.2",
        estimated_cost_usd=0.0,
        latency_ms=100.0,
        total_tokens=120,
    )

    conf_same_ws = cache.calculate_confidence(entry, 0.90, workspace_id="ws-prod")
    conf_diff_ws = cache.calculate_confidence(entry, 0.90, workspace_id="ws-other")

    assert conf_same_ws > 0.80
    assert conf_diff_ws == 0.0  # Strict workspace boundary


def test_memory_ranking():
    store = CacheStore()
    cache = SemanticCache(store=store)

    entry_old = CacheEntry(
        key="k1",
        workspace_id="ws-1",
        prompt="Design database schema for e-commerce",
        normalized_prompt="design database schema for ecommerce",
        response_text="Table 1...",
        provider_id="openai",
        model_id="gpt-4o",
        estimated_cost_usd=0.001,
        latency_ms=300.0,
        total_tokens=100,
        use_count=1,
        quality_score=0.85,
    )

    entry_frequent = CacheEntry(
        key="k2",
        workspace_id="ws-1",
        prompt="Design database schema for e-commerce store",
        normalized_prompt="design database schema for ecommerce store",
        response_text="Table Ecommerce...",
        provider_id="openai",
        model_id="gpt-4o",
        estimated_cost_usd=0.001,
        latency_ms=300.0,
        total_tokens=100,
        use_count=15,
        quality_score=0.98,
    )

    candidates = [
        (entry_old, 0.85, 0.82),
        (entry_frequent, 0.85, 0.85),
    ]

    best = cache.rank_memories(candidates)
    assert best is not None
    assert best.key == "k2"  # Frequently used & higher quality memory wins ranking


def test_memory_fingerprinting_and_metadata():
    cache = SemanticCache()
    fp1 = cache.generate_fingerprint("def hello_world(): return 'hi'", workspace_id="ws-dev", intent="CODING")
    fp2 = cache.generate_fingerprint("def hello_world(): return 'hi'", workspace_id="ws-dev", intent="CODING")

    assert fp1["fingerprint_hash"] == fp2["fingerprint_hash"]
    assert fp1["has_code"] is True
    assert fp1["intent"] == "CODING"


def test_memory_lifecycle_states():
    entry = CacheEntry(
        key="l1",
        workspace_id="ws-lc",
        prompt="Test lifecycle",
        normalized_prompt="test lifecycle",
        response_text="Ans",
        provider_id="ollama",
        model_id="llama3.2",
        estimated_cost_usd=0.0,
        latency_ms=50.0,
        total_tokens=10,
        use_count=6,
    )

    state = entry.update_lifecycle_state()
    assert state == "FREQUENTLY_USED"

    store = CacheStore(max_entries=2)
    entry1 = CacheEntry(key="e1", workspace_id="w", prompt="p1", normalized_prompt="p1", response_text="r1", provider_id="o", model_id="m", estimated_cost_usd=0, latency_ms=0, total_tokens=0, use_count=10) # Frequently used
    entry2 = CacheEntry(key="e2", workspace_id="w", prompt="p2", normalized_prompt="p2", response_text="r2", provider_id="o", model_id="m", estimated_cost_usd=0, latency_ms=0, total_tokens=0, use_count=1)
    entry3 = CacheEntry(key="e3", workspace_id="w", prompt="p3", normalized_prompt="p3", response_text="r3", provider_id="o", model_id="m", estimated_cost_usd=0, latency_ms=0, total_tokens=0, use_count=1)

    store.set(entry1)
    store.set(entry2)
    store.set(entry3)  # Eviction triggered

    # entry1 (FREQUENTLY_USED) must be protected from eviction!
    assert store.get("e1") is not None


def test_adaptive_memory_learning():
    store = CacheStore()
    cache = SemanticCache(store=store)

    cache.set("How to calculate Fibonacci in Python", "def fib(n): ...", workspace_id="ws-learn")

    hit = cache.get("How to calculate Fibonacci in Python", workspace_id="ws-learn")
    assert hit is not None

    entry = cache.store.get(hit["entry"]["key"])
    assert entry is not None
    assert entry.use_count == 1
    assert entry.successful_reuses == 1
    assert entry.quality_score >= 0.90


def test_enterprise_safety_constraints():
    store = CacheStore()
    cache = SemanticCache(store=store)

    cache.set(
        "Generate secret API key handling logic",
        "def handle_key(): ...",
        workspace_id="ws-sec",
        system_prompt="System Prompt Version 1",
    )

    # Query with changed system prompt
    hit_changed_sys = cache.get(
        "Generate secret API key handling logic",
        workspace_id="ws-sec",
        system_prompt="System Prompt Version 2 (Strict Policy Updated)",
        confidence_threshold=0.85,
    )

    # System prompt mismatch lowers confidence below threshold -> Safe To Reuse == False
    assert hit_changed_sys is None
    assert cache.metrics.rejected_hits == 1


def test_large_dataset_performance():
    store = CacheStore()
    cache = SemanticCache(store=store)

    # Seed 100 entries
    t0 = time.perf_counter()
    for i in range(100):
        cache.set(
            f"Query prompt number {i} for data processing algorithm",
            f"Result response string number {i}",
            workspace_id="ws-perf",
        )
    t_seed = (time.perf_counter() - t0) * 1000

    # Execute search
    t1 = time.perf_counter()
    hit = cache.get("Query prompt number 50 for data processing algorithm", workspace_id="ws-perf")
    t_search = (time.perf_counter() - t1) * 1000

    assert hit is not None
    assert t_search < 15.0  # Search completes in < 15ms


def test_enterprise_memory_analytics():
    store = CacheStore()
    cache = SemanticCache(store=store)

    cache.set("Top Query 1", "Ans 1", workspace_id="ws-a", total_tokens=200, estimated_cost_usd=0.004)
    cache.get("Top Query 1", workspace_id="ws-a")

    metrics = cache.get_metrics()
    assert "quality_distribution" in metrics
    assert "workspace_statistics" in metrics
    assert "most_valuable_memories" in metrics
    assert metrics["total_memories"] == 1
    assert metrics["hit_rate_pct"] == 100.0
