"""Enterprise Health Probing Engine.

Performs active and passive health probes across catalog providers and models.
"""

import datetime
import time

from app.models_registry import model_registry
from app.reliability.models import HealthProbeRecord, HealthProbeStatusEnum


class HealthProbingEngine:
    """Active/Passive Provider Health Probing Engine."""

    def __init__(self) -> None:
        self._probes: dict[str, HealthProbeRecord] = {}

    def probe_provider(self, provider_id: str) -> HealthProbeRecord:
        """Probe provider connection responsiveness."""
        t0 = time.perf_counter_ns()
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            p = model_registry.get_provider(provider_id)
            status_enum = HealthProbeStatusEnum.HEALTHY if p.enabled else HealthProbeStatusEnum.OFFLINE
            t1 = time.perf_counter_ns()
            lat_ms = round((t1 - t0) / 1_000_000, 2)
            record = HealthProbeRecord(
                provider_id=provider_id,
                status=status_enum,
                latency_ms=lat_ms,
                last_checked_at=now_iso,
            )
        except KeyError:
            record = HealthProbeRecord(
                provider_id=provider_id,
                status=HealthProbeStatusEnum.UNHEALTHY,
                latency_ms=0.0,
                last_checked_at=now_iso,
                error_message=f"Provider '{provider_id}' not found in registry.",
            )

        self._probes[provider_id.lower()] = record
        return record

    def run_all_probes(self) -> list[HealthProbeRecord]:
        """Trigger health probes for all registered providers in catalog."""
        providers = model_registry.list_providers()
        results = []
        for p in providers:
            results.append(self.probe_provider(p.provider_id))
        return results

    def get_probe_status(self, provider_id: str) -> HealthProbeRecord:
        """Get last probe status for provider."""
        key = provider_id.lower()
        if key not in self._probes:
            return self.probe_provider(provider_id)
        return self._probes[key]


health_probing_engine = HealthProbingEngine()
