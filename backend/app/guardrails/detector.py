import re
from dataclasses import dataclass
from typing import Any


@dataclass
class DetectionResult:
    is_detected: bool
    risk_score: float  # 0.0 to 1.0
    matched_rules: list[str]
    category: str


class PromptInjectionDetector:
    """Detects instruction hijacking, prompt override, and system prompt extraction attacks."""

    INJECTION_PATTERNS = [
        (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", "Prompt Override Attack"),
        (r"disregard\s+(all\s+)?(earlier|previous)\s+directives", "Instruction Hijacking"),
        (r"(reveal|print|show|display|output)\s+(your\s+)?(system\s+prompt|initial\s+instructions)", "System Prompt Leakage"),
        (r"you\s+are\s+now\s+in\s+developer\s+mode", "Developer Mode Override"),
        (r"forget\s+everything\nyou\s+were\s+told", "Context Reset Attack"),
        (r"new\s+system\s+instruction:", "System Instruction Override"),
    ]

    def detect(self, text: str) -> DetectionResult:
        if not text:
            return DetectionResult(is_detected=False, risk_score=0.0, matched_rules=[], category="prompt_injection")

        matched = []
        for pattern, rule_name in self.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matched.append(rule_name)

        is_detected = len(matched) > 0
        risk_score = min(len(matched) * 0.45, 1.0) if is_detected else 0.0

        return DetectionResult(
            is_detected=is_detected,
            risk_score=round(risk_score, 2),
            matched_rules=matched,
            category="prompt_injection",
        )


class JailbreakDetector:
    """Detects adversarial jailbreak techniques, DAN variants, and safety filter bypasses."""

    JAILBREAK_PATTERNS = [
        (r"\bDAN\b|\bDo\s+Anything\s+Now\b", "DAN (Do Anything Now) Jailbreak"),
        (r"jailbroken\s+mode", "Jailbroken Mode Toggle"),
        (r"act\s+as\s+an?\s+(unfiltered|unrestricted|evil|immoral)\s+ai", "Roleplay Safety Bypass"),
        (r"pretend\s+you\s+have\s+no\s+(safety|ethical)\s+(filters|rules|guidelines)", "Filter Bypass Persona"),
        (r"bypass\s+all\s+ethical\s+boundaries", "Ethical Boundary Bypass"),
        (r"hypothetically\s+speaking,\s+how\s+would\s+one\s+(hack|bypass|exploit)", "Hypothetical Exploit Probe"),
    ]

    def detect(self, text: str) -> DetectionResult:
        if not text:
            return DetectionResult(is_detected=False, risk_score=0.0, matched_rules=[], category="jailbreak")

        matched = []
        for pattern, rule_name in self.JAILBREAK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matched.append(rule_name)

        is_detected = len(matched) > 0
        risk_score = min(len(matched) * 0.5, 1.0) if is_detected else 0.0

        return DetectionResult(
            is_detected=is_detected,
            risk_score=round(risk_score, 2),
            matched_rules=matched,
            category="jailbreak",
        )
