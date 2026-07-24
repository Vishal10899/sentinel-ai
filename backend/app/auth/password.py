import hashlib
import secrets
import hmac


PBKDF2_ITERATIONS = 310_000


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        PBKDF2_ITERATIONS,
    ).hex()

    return salt, password_hash


def verify_password(
    password: str,
    salt: str,
    stored_hash: str,
) -> bool:

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        PBKDF2_ITERATIONS,
    ).hex()

    return hmac.compare_digest(
        password_hash,
        stored_hash,
    )