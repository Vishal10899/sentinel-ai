import hashlib
import secrets
import hmac


PBKDF2_ITERATIONS = 310_000


def hash_password(password: str | bytes) -> tuple[str, str]:
    if isinstance(password, bytes):
        password = password.decode("utf-8", errors="replace")
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()

    return salt, password_hash


def verify_password(
    password: str | bytes,
    salt: str | bytes,
    stored_hash: str | bytes,
) -> bool:
    if isinstance(password, bytes):
        password = password.decode("utf-8", errors="replace")
    if isinstance(salt, bytes):
        salt = salt.decode("utf-8", errors="replace")
    if isinstance(stored_hash, bytes):
        stored_hash = stored_hash.decode("utf-8", errors="replace")

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()

    return hmac.compare_digest(
        password_hash,
        stored_hash,
    )