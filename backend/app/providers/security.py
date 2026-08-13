"""Security and API key masking utilities for enterprise provider credentials."""

import base64


def mask_api_key(api_key: str | None) -> str | None:
    """Return a masked representation of an API key to avoid exposing secrets over APIs."""
    if not api_key:
        return None
    cleaned = api_key.strip()
    if len(cleaned) <= 8:
        return "****" + cleaned[-2:]
    return f"{cleaned[:6]}****{cleaned[-4:]}"


def encrypt_secret(secret: str | None) -> str | None:
    """Obfuscate/encrypt secret credential string at rest."""
    if not secret:
        return None
    # Lightweight reversible obfuscation suitable for local/standalone DB setups
    # can be swapped for Fernet or KMS in production
    return "enc:" + base64.b64encode(secret.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted: str | None) -> str | None:
    """Decrypt obfuscated credential string for runtime adapter usage."""
    if not encrypted:
        return None
    if encrypted.startswith("enc:"):
        raw = encrypted[4:]
        try:
            return base64.b64decode(raw.encode("utf-8")).decode("utf-8")
        except Exception:
            return encrypted
    return encrypted


def sanitize_base_url(base_url: str | None, default_url: str | None = None) -> str | None:
    """Sanitize base_url parameter: ignore empty/null/placeholder values like https://api.vendor.com and return default_url or None."""
    if not base_url or not isinstance(base_url, str):
        return default_url
    cleaned = base_url.strip()
    if not cleaned:
        return default_url
    cleaned_lower = cleaned.lower()
    placeholders = [
        "api.vendor.com",
        "vendor.com",
        "example.com",
        "placeholder",
        "https://api.vendor.com",
        "http://api.vendor.com",
    ]
    if any(p in cleaned_lower for p in placeholders):
        return default_url
    return cleaned

