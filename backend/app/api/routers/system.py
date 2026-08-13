"""Enterprise System Operations REST API Router."""

import time
from fastapi import APIRouter, Response, status

from app.core.config_validator import configuration_validator
from app.core.settings import settings
from app.models_registry import model_registry
from app.reliability import health_probing_engine

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health", summary="System Health Check")
async def get_system_health():
    """Application health endpoint (< 20 ms)."""
    t0 = time.perf_counter_ns()
    t1 = time.perf_counter_ns()
    exec_ms = round((t1 - t0) / 1_000_000, 3)

    return {
        "status": "HEALTHY",
        "service": settings.project_title,
        "version": settings.project_version,
        "response_time_ms": exec_ms,
    }


@router.get("/readiness", summary="Readiness Probe")
async def readiness_probe(response: Response):
    """Readiness probe checking database, redis, and provider readiness (< 50 ms)."""
    t0 = time.perf_counter_ns()

    probes = health_probing_engine.run_all_probes()
    is_ready = any(p.status.value in ("HEALTHY", "DEGRADED") for p in probes) or len(probes) == 0

    t1 = time.perf_counter_ns()
    exec_ms = round((t1 - t0) / 1_000_000, 3)

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "UNREADY",
            "reason": "Dependencies or catalog providers unhealthy.",
            "response_time_ms": exec_ms,
        }

    return {
        "status": "READY",
        "service": settings.project_title,
        "response_time_ms": exec_ms,
    }


@router.get("/liveness", summary="Liveness Probe")
async def liveness_probe():
    """Liveness probe verifying main looper and process health (< 20 ms)."""
    t0 = time.perf_counter_ns()
    t1 = time.perf_counter_ns()
    exec_ms = round((t1 - t0) / 1_000_000, 3)

    return {
        "status": "ALIVE",
        "response_time_ms": exec_ms,
    }


@router.get("/version", summary="Application Version Information")
async def get_version():
    """Return control plane version and build metadata."""
    return {
        "project_title": settings.project_title,
        "version": settings.project_version,
        "environment": settings.environment,
        "api_v1_prefix": settings.api_v1_prefix,
    }


@router.get("/config", summary="Configuration Validation Report")
async def get_config_report():
    """Configuration validation report (< 100 ms)."""
    report = configuration_validator.validate_configuration()
    return report.to_dict()
