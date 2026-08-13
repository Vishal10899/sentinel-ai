import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

from app.guardrails.detector import JailbreakDetector, PromptInjectionDetector
from app.guardrails.metrics import GuardrailsMetrics
from app.guardrails.pii_secrets import PIIAndSecretScanner, pii_secret_scanner


@dataclass
class GuardrailResult:
    action: str  # ALLOW, BLOCK, SANITIZE, WARN
    sanitized_text: str
    risk_score: float
    matched_rules: list[str]
    pii_redacted: list[str]
    secrets_masked: list[str]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GuardrailsEngine:
    """Unified Enterprise AI Guardrails Engine scanning requests and responses for safety threats and data leaks."""

    def __init__(self) -> None:
        self.injection_detector = PromptInjectionDetector()
        self.jailbreak_detector = JailbreakDetector()
        self.pii_scanner = pii_secret_scanner
        self.metrics = GuardrailsMetrics()

    def normalize_input(self, text: str) -> str:
        """Normalize Unicode, strip control characters, and collapse whitespace."""
        if not text:
            return ""
        norm = unicodedata.normalize("NFKC", text)
        # Strip non-printable control characters (except newlines and tabs)
        clean_chars = [ch for ch in norm if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\r", "\t")]
        return "".join(clean_chars).strip()

    def scan_request(
        self,
        prompt: str,
        block_high_risk: bool = True,
        redact_secrets: bool = True,
        redact_pii: bool = True,
    ) -> GuardrailResult:
        """Scan incoming user prompt for injection attacks, jailbreaks, PII, and API keys."""
        self.metrics.total_scanned += 1
        clean_prompt = self.normalize_input(prompt)

        # 1. Prompt Injection Detection
        inj_res = self.injection_detector.detect(clean_prompt)
        if inj_res.is_detected:
            self.metrics.prompt_injections_detected += 1

        # 2. Jailbreak Detection
        jail_res = self.jailbreak_detector.detect(clean_prompt)
        if jail_res.is_detected:
            self.metrics.jailbreaks_detected += 1

        # 3. PII & Secret Redaction
        scan_res = self.pii_scanner.scan_and_redact(clean_prompt, redact_pii=redact_pii, redact_secrets=redact_secrets)
        if scan_res.pii_found:
            self.metrics.pii_redactions += len(scan_res.pii_found)
        if scan_res.secrets_found:
            self.metrics.secrets_masked += len(scan_res.secrets_found)

        max_risk = max(inj_res.risk_score, jail_res.risk_score)
        all_rules = inj_res.matched_rules + jail_res.matched_rules

        if block_high_risk and max_risk >= 0.8:
            self.metrics.blocked_requests += 1
            return GuardrailResult(
                action="BLOCK",
                sanitized_text=clean_prompt,
                risk_score=max_risk,
                matched_rules=all_rules,
                pii_redacted=scan_res.pii_found,
                secrets_masked=scan_res.secrets_found,
                reason=f"Request blocked due to high adversarial risk score ({max_risk:.2f}). Matched: {', '.join(all_rules)}",
            )

        action = "SANITIZE" if scan_res.is_modified else ("WARN" if max_risk > 0.0 else "ALLOW")
        reason = "Request sanitized to mask sensitive PII/secrets." if scan_res.is_modified else "Request passed guardrail checks."

        return GuardrailResult(
            action=action,
            sanitized_text=scan_res.text,
            risk_score=max_risk,
            matched_rules=all_rules,
            pii_redacted=scan_res.pii_found,
            secrets_masked=scan_res.secrets_found,
            reason=reason,
        )

    def scan_response(self, response_text: str) -> str:
        """Scan outgoing LLM provider output for accidental PII or secret leakage."""
        scan_res = self.pii_scanner.scan_and_redact(response_text, redact_pii=True, redact_secrets=True)
        if scan_res.is_modified:
            self.metrics.responses_redacted += 1
        return scan_res.text

    def get_metrics(self) -> dict[str, Any]:
        """Return Guardrails metrics dictionary."""
        return self.metrics.to_dict()


guardrails_engine = GuardrailsEngine()
