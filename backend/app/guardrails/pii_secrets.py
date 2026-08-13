import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ScanResult:
    text: str
    pii_found: list[str]
    secrets_found: list[str]
    is_modified: bool


class PIIAndSecretScanner:
    """Detects and redacts PII and sensitive API keys to prevent data leakage."""

    SECRET_PATTERNS = [
        (r"\bAKIA[0-9A-Z]{16}\b", "[REDACTED_AWS_KEY]", "AWS Access Key ID"),
        (r"sk-[a-zA-Z0-9]{32,64}", "[REDACTED_OPENAI_KEY]", "OpenAI API Key"),
        (r"sk-ant-[a-zA-Z0-9_-]{32,64}", "[REDACTED_ANTHROPIC_KEY]", "Anthropic API Key"),
        (r"AIzaSy[a-zA-Z0-9_-]{33}", "[REDACTED_GEMINI_KEY]", "Google Gemini Key"),
        (r"-----BEGIN (RSA |EC |PGP )?PRIVATE KEY-----[\s\S]*?-----END \1PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]", "RSA/EC Private Key"),
        (r"bearer\s+[a-zA-Z0-9\-_=]+\.[a-zA-Z0-9\-_=]+\.?[a-zA-Z0-9\-_=]*", "[REDACTED_JWT_TOKEN]", "JWT Bearer Token"),
    ]

    PII_PATTERNS = [
        (r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "[REDACTED_EMAIL]", "Email Address"),
        (r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CREDIT_CARD]", "Credit Card Number"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]", "Social Security Number"),
    ]

    def scan_and_redact(self, text: str, redact_pii: bool = True, redact_secrets: bool = True) -> ScanResult:
        if not text:
            return ScanResult(text="", pii_found=[], secrets_found=[], is_modified=False)

        sanitized_text = text
        pii_matches: list[str] = []
        secrets_matches: list[str] = []
        is_modified = False

        if redact_secrets:
            for pattern, replacement, label in self.SECRET_PATTERNS:
                if re.search(pattern, sanitized_text):
                    secrets_matches.append(label)
                    sanitized_text = re.sub(pattern, replacement, sanitized_text)
                    is_modified = True

        if redact_pii:
            for pattern, replacement, label in self.PII_PATTERNS:
                if re.search(pattern, sanitized_text):
                    pii_matches.append(label)
                    sanitized_text = re.sub(pattern, replacement, sanitized_text)
                    is_modified = True

        return ScanResult(
            text=sanitized_text,
            pii_found=pii_matches,
            secrets_found=secrets_matches,
            is_modified=is_modified,
        )


pii_secret_scanner = PIIAndSecretScanner()
