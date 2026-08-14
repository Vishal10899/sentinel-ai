"""Validation script for Sentinel AI system startup and core endpoints.
Used during CI/CD to ensure FastAPI app initializes and endpoints respond as expected.
"""

import sys
import logging
from starlette.testclient import TestClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup_validator")


def validate_system():
    logger.info("Initializing Sentinel AI application...")
    try:
        from app.main import app
        from app.core.settings import settings
        from app.rbac import role_repository, rbac_engine
    except Exception as e:
        logger.error(f"Failed to import app components: {e}")
        sys.exit(1)

    logger.info(f"Loaded application: {settings.project_title} v{settings.project_version}")

    with TestClient(app, raise_server_exceptions=True) as client:
        # 1. Root health check
        res = client.get("/api/v1/health")
        assert res.status_code == 200, f"Health check failed: {res.status_code} {res.text}"
        logger.info("[✓] /api/v1/health responded with 200")

        # 2. System readiness & liveness probes
        res = client.get("/api/v1/system/readiness")
        assert res.status_code == 200, f"Readiness probe failed: {res.status_code} {res.text}"
        logger.info("[✓] /api/v1/system/readiness responded with 200")

        res = client.get("/api/v1/system/liveness")
        assert res.status_code == 200, f"Liveness probe failed: {res.status_code} {res.text}"
        logger.info("[✓] /api/v1/system/liveness responded with 200")

        # 3. Prometheus metrics endpoint
        res = client.get("/metrics")
        assert res.status_code == 200, f"Metrics exposition failed: {res.status_code}"
        logger.info("[✓] /metrics responded with 200")

        # 4. OpenAPI docs schema
        res = client.get("/openapi.json")
        assert res.status_code == 200, f"OpenAPI schema failed: {res.status_code}"
        logger.info("[✓] /openapi.json responded with 200")

        # 5. Verify registered routes coverage
        routes = [route.path for route in app.routes]
        expected_routes = [
            "/api/v1/health",
            "/api/v1/models",
            "/api/v1/providers",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/v1/chat/completions",
            "/metrics",
        ]
        for route in expected_routes:
            assert any(r == route or route in r for r in routes), f"Expected route {route} not found in app routes"
            logger.info(f"[✓] Verified route registered: {route}")

    logger.info("All system startup and endpoint validations passed successfully.")


if __name__ == "__main__":
    validate_system()
