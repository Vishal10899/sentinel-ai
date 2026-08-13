"""Comprehensive Unit, Integration, & Performance Test Suite for Sprint 2.9.

Tests Circuit Breaker State Transitions, Bulkhead Isolation, Advanced Retry Jitter,
Adaptive Timeouts, Idempotency Replay, Rate Limiter Token Buckets, Health Probes,
Connection Pooling, Performance Benchmarks, and System Integrity.
"""

import time
import pytest

from app.reliability import (
    CircuitState,
    adaptive_timeout_engine,
    advanced_retry_engine,
    bulkhead_engine,
    circuit_breaker_engine,
    connection_pool_engine,
    health_probing_engine,
    idempotency_engine,
    rate_limiter_engine,
)


# ====================================================
# 1. Circuit Breaker Engine Tests (< 0.1ms)
# ====================================================

def test_circuit_breaker_transitions_and_reset():
    p_id = "test-provider-cb"

    # Initial state CLOSED
    state = circuit_breaker_engine.check_state(p_id)
    assert state == CircuitState.CLOSED

    # Record 3 failures -> Should trip to OPEN
    circuit_breaker_engine.record_failure(p_id)
    circuit_breaker_engine.record_failure(p_id)
    state_tripped = circuit_breaker_engine.record_failure(p_id)
    assert state_tripped == CircuitState.OPEN
    assert circuit_breaker_engine.check_state(p_id) == CircuitState.OPEN

    # Reset circuit manually -> Should be CLOSED
    reset_rec = circuit_breaker_engine.reset_circuit(p_id)
    assert reset_rec.state == CircuitState.CLOSED
    assert circuit_breaker_engine.check_state(p_id) == CircuitState.CLOSED


# ====================================================
# 2. Bulkhead Isolation & Queue Tests
# ====================================================

def test_bulkhead_isolation():
    p_id = "test-bulkhead-provider"

    # Acquire worker slot
    acquired, msg = bulkhead_engine.acquire(p_id)
    assert acquired is True
    status = bulkhead_engine.get_status(p_id)
    assert status.active_workers == 1

    # Release worker slot
    bulkhead_engine.release(p_id)
    status_after = bulkhead_engine.get_status(p_id)
    assert status_after.completed_requests == 1


# ====================================================
# 3. Idempotency Key & Replay Tests
# ====================================================

def test_idempotency_key_replay():
    k = "idem-key-12345"

    # Initial lookup -> None
    rec_none = idempotency_engine.get_record(k)
    assert rec_none is None

    # Save record
    saved = idempotency_engine.save_record(k, {"result": "success", "data": 42})
    assert saved.key == k

    # Second lookup -> Should hit cached response
    rec_hit = idempotency_engine.get_record(k)
    assert rec_hit is not None
    assert rec_hit.response_payload["data"] == 42


# ====================================================
# 4. Rate Limiter Token Bucket Tests
# ====================================================

def test_rate_limiter_token_bucket():
    res = rate_limiter_engine.evaluate("ws-1", "user-1", "gemini")
    assert res.allowed is True
    assert res.remaining >= 0


# ====================================================
# 5. Advanced Retry Engine Tests (< 0.2ms)
# ====================================================

def test_advanced_retry_decision():
    # Transient 429 error -> Retry
    decision_429 = advanced_retry_engine.evaluate_retry(attempt=0, status_code=429)
    assert decision_429.should_retry is True
    assert decision_429.wait_seconds > 0.0

    # Non-transient 401 Auth error -> Immediate Failover
    decision_401 = advanced_retry_engine.evaluate_retry(attempt=0, status_code=401)
    assert decision_401.should_retry is False
    assert decision_401.is_transient is False

    # Max retries exhausted
    decision_exhausted = advanced_retry_engine.evaluate_retry(attempt=2, status_code=500, max_retries=2)
    assert decision_exhausted.should_retry is False


# ====================================================
# 6. Adaptive Timeout Engine Tests (< 0.2ms)
# ====================================================

def test_adaptive_timeout_calculation():
    # Reasoning task -> higher timeout
    res_reasoning = adaptive_timeout_engine.calculate_timeout("gemini", "gemini-2.0-flash", task_category="reasoning")
    assert res_reasoning.hard_timeout_seconds >= 45.0

    # Chat task -> standard timeout
    res_chat = adaptive_timeout_engine.calculate_timeout("gemini", "gemini-2.0-flash", task_category="chat")
    assert res_chat.hard_timeout_seconds <= 20.0


# ====================================================
# 7. Health Probes & Connection Pool Tests
# ====================================================

def test_health_prober_and_connection_pool():
    # Health Probes
    probes = health_probing_engine.run_all_probes()
    assert len(probes) >= 4

    # Connection Lookup (< 0.1ms)
    adapter = connection_pool_engine.get_connection("gemini")
    assert adapter is not None


# ====================================================
# 8. Performance Benchmarks Tests
# ====================================================

def test_performance_benchmarks():
    # 1. Circuit Breaker Check (< 0.1ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        circuit_breaker_engine.check_state("gemini")
    cb_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert cb_ms < 0.1, f"Circuit breaker check took {cb_ms:.3f} ms (limit 0.1 ms)"

    # 2. Retry Decision (< 0.2ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        advanced_retry_engine.evaluate_retry(attempt=0, status_code=429)
    retry_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert retry_ms < 0.2, f"Retry decision took {retry_ms:.3f} ms (limit 0.2 ms)"

    # 3. Timeout Decision (< 0.2ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        adaptive_timeout_engine.calculate_timeout("gemini", "gemini-2.0-flash", "coding")
    timeout_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert timeout_ms < 0.2, f"Timeout decision took {timeout_ms:.3f} ms (limit 0.2 ms)"

    # 4. Connection Lookup (< 0.1ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        connection_pool_engine.get_connection("gemini")
    conn_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert conn_ms < 0.1, f"Connection lookup took {conn_ms:.3f} ms (limit 0.1 ms)"
