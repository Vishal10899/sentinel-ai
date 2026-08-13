from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class GuardrailsMetrics:
    """Telemetry metrics for AI Guardrails threat detection and secret masking."""

    total_scanned: int = 0
    prompt_injections_detected: int = 0
    jailbreaks_detected: int = 0
    pii_redactions: int = 0
    secrets_masked: int = 0
    blocked_requests: int = 0
    responses_redacted: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
