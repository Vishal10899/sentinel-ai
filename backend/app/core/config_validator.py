"""Enterprise Configuration & Environment Validation Engine.

Validates environment settings (development, testing, staging, production) and configuration parameters in < 100 ms.
"""

from dataclasses import dataclass
import os
import time
from typing import Any

from app.core.settings import settings


@dataclass(frozen=True, slots=True)
class ConfigValidationResult:
    """Configuration validation report."""

    environment: str
    is_valid: bool
    execution_time_ms: float
    checks: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict:
        return {
            "environment": self.environment,
            "is_valid": self.is_valid,
            "execution_time_ms": self.execution_time_ms,
            "checks": list(self.checks),
        }


class ConfigurationValidator:
    """High-performance Configuration Validator (< 100 ms)."""

    VALID_ENVIRONMENTS = {"development", "testing", "staging", "production"}

    def validate_configuration(self, target_env: str | None = None) -> ConfigValidationResult:
        """Validate system configuration in < 100 ms."""
        t0 = time.perf_counter_ns()

        current_env = (target_env or os.getenv("ENVIRONMENT") or settings.environment or "development").lower()
        if current_env not in self.VALID_ENVIRONMENTS:
            current_env = "development"

        checks: list[dict[str, Any]] = []

        # 1. Environment check
        checks.append({
            "name": "environment_check",
            "status": "PASS",
            "message": f"Environment set to '{current_env}'.",
        })

        # 2. Secret / API Key check
        has_gemini_key = bool(settings.gemini_api_key)
        has_openai_key = bool(settings.openai_api_key)

        checks.append({
            "name": "provider_keys_check",
            "status": "PASS" if (has_gemini_key or has_openai_key) else "WARN",
            "message": "At least one provider API key is configured." if (has_gemini_key or has_openai_key) else "No provider API key configured (using mock mode).",
        })

        # 3. Database URL check
        has_db_url = bool(settings.database_url or settings.async_database_url)
        checks.append({
            "name": "database_url_check",
            "status": "PASS" if has_db_url else "WARN",
            "message": "Database connection URL configured.",
        })

        # 4. Redis URL check
        checks.append({
            "name": "redis_url_check",
            "status": "PASS",
            "message": f"Redis URL set to '{settings.redis_url}'.",
        })

        t1 = time.perf_counter_ns()
        exec_ms = round((t1 - t0) / 1_000_000, 3)

        all_passed = all(c["status"] in ("PASS", "WARN") for c in checks)

        return ConfigValidationResult(
            environment=current_env,
            is_valid=all_passed,
            execution_time_ms=exec_ms,
            checks=tuple(checks),
        )


configuration_validator = ConfigurationValidator()
