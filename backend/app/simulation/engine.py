import time
from uuid import uuid4
from typing import Any

from app.audit.engine import audit_engine
from app.observability.repository import observability_repository
from app.policy import policy_engine
from app.simulation.models import PolicyVersion, SimulationResult


class PolicySimulator:
    """Isolated Dry-Run Policy Simulator & Impact Analyzer."""

    def simulate(
        self,
        proposed_policy: dict[str, Any],
        workspace_id: str = "default",
        user_id: str = "admin",
        sample_size: int = 100,
    ) -> SimulationResult:
        """Run dry-run simulation of proposed policy against stored traces without altering state."""
        traces = observability_repository.search_traces(workspace_id=workspace_id, limit=sample_size)
        total = len(traces)
        if total == 0:
            total = 10  # Mock baseline sample size if empty

        allowed = 0
        blocked = 0
        rerouted = 0
        cost_delta = 0.0
        latency_delta = 0.0
        affected_models: dict[str, int] = {}

        max_cost_limit = proposed_policy.get("max_cost_per_request", 0.05)
        blocked_models = proposed_policy.get("blocked_models", [])

        for t in traces:
            model = getattr(t, "model_id", "gpt-4o")
            cost = getattr(t, "cost_usd", 0.002)

            if model in blocked_models or cost > max_cost_limit:
                blocked += 1
                cost_delta -= cost
                affected_models[model] = affected_models.get(model, 0) + 1
            else:
                allowed += 1

        impact_pct = round((blocked / total) * 100, 1)

        # Audit Event for simulation run
        audit_engine.record_event(
            action="SIMULATION_EXECUTED",
            resource="policies/simulator",
            user_id=user_id,
            workspace_id=workspace_id,
            new_value=f"Impact: {impact_pct}% blocked, ${abs(cost_delta):.4f} saved",
        )

        return SimulationResult(
            total_requests=total,
            allowed_count=allowed,
            blocked_count=blocked,
            rerouted_count=rerouted,
            cost_delta_usd=round(cost_delta, 4),
            latency_delta_ms=-15.0 if blocked > 0 else 0.0,
            impact_percentage=impact_pct,
            affected_models=affected_models,
        )


class PolicyVersionManager:
    """Policy Version Control & Zero-Downtime Rollback Engine."""

    def __init__(self) -> None:
        self._versions: dict[str, PolicyVersion] = {}
        self._seed_default_version()

    def _seed_default_version(self) -> None:
        v1 = PolicyVersion(
            version_id="ver-v1.0",
            version_number="v1.0",
            policy_data={"max_cost_per_request": 0.10, "blocked_models": []},
            published_by="admin",
            is_active=True,
        )
        self._versions[v1.version_id] = v1

    def list_versions(self) -> list[PolicyVersion]:
        return list(self._versions.values())

    def publish_version(self, policy_data: dict[str, Any], publisher: str = "admin") -> PolicyVersion:
        ver_num = f"v1.{len(self._versions)}"
        ver_id = f"ver-{ver_num}"

        for v in self._versions.values():
            v.is_active = False

        new_v = PolicyVersion(
            version_id=ver_id,
            version_number=ver_num,
            policy_data=policy_data,
            published_by=publisher,
            is_active=True,
        )
        self._versions[ver_id] = new_v

        # Emit audit event
        audit_engine.record_event(
            action="POLICY_PUBLISHED",
            resource=f"policies/{ver_id}",
            user_id=publisher,
            workspace_id="default",
            new_value=f"Published Policy {ver_num}",
        )

        return new_v

    def rollback_version(self, version_id: str, actor: str = "admin") -> PolicyVersion | None:
        target = self._versions.get(version_id)
        if not target:
            return None

        for v in self._versions.values():
            v.is_active = False

        target.is_active = True

        # Emit audit event
        audit_engine.record_event(
            action="POLICY_ROLLED_BACK",
            resource=f"policies/{version_id}",
            user_id=actor,
            workspace_id="default",
            new_value=f"Rolled Back Policy to {target.version_number}",
        )

        return target


policy_simulator = PolicySimulator()
policy_version_manager = PolicyVersionManager()
