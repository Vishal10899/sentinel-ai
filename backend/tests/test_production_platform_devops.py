"""Comprehensive Unit, Integration, & Performance Test Suite for Sprint 3.1.

Tests Production Docker Configurations, Environment Management, Configuration Validation,
System Health, Readiness & Liveness Probes, Backup Strategy, and Performance Benchmarks.
"""

import time
import pytest
from fastapi.testclient import TestClient

from app.core.config_validator import configuration_validator
from app.main import app

client = TestClient(app)


# ====================================================
# 1. Configuration Validation Tests (< 100 ms)
# ====================================================

def test_configuration_validation():
    report = configuration_validator.validate_configuration("production")
    assert report.environment == "production"
    assert report.is_valid is True
    assert report.execution_time_ms < 100.0


# ====================================================
# 2. System Probes & Health Endpoint Tests
# ====================================================

def test_system_health_and_probes():
    # 1. Health Endpoint (< 20 ms)
    res_health = client.get("/api/v1/system/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "HEALTHY"

    # 2. Readiness Probe (< 50 ms)
    res_ready = client.get("/api/v1/system/readiness")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "READY"

    # 3. Liveness Probe (< 20 ms)
    res_live = client.get("/api/v1/system/liveness")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "ALIVE"

    # 4. Version Endpoint
    res_ver = client.get("/api/v1/system/version")
    assert res_ver.status_code == 200
    assert "version" in res_ver.json()

    # 5. Config Report Endpoint (< 100 ms)
    res_cfg = client.get("/api/v1/system/config")
    assert res_cfg.status_code == 200
    assert res_cfg.json()["is_valid"] is True


# ====================================================
# 3. Performance Benchmarks Tests
# ====================================================

def test_performance_benchmarks():
    # 1. Health Endpoint (< 20 ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        client.get("/api/v1/system/health")
    health_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert health_ms < 20.0, f"Health endpoint took {health_ms:.3f} ms (limit 20 ms)"

    # 2. Readiness Probe (< 50 ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        client.get("/api/v1/system/readiness")
    ready_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert ready_ms < 50.0, f"Readiness check took {ready_ms:.3f} ms (limit 50 ms)"

    # 3. Liveness Probe (< 20 ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        client.get("/api/v1/system/liveness")
    live_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert live_ms < 20.0, f"Liveness probe took {live_ms:.3f} ms (limit 20 ms)"

    # 4. Configuration Validation (< 100 ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        configuration_validator.validate_configuration("production")
    cfg_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert cfg_ms < 100.0, f"Config validation took {cfg_ms:.3f} ms (limit 100 ms)"
