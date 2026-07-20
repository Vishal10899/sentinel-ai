"""Small dependency-free JWT and user service for the API layer."""

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.settings import settings


def _encode(value: dict[str, object]) -> str:
    return base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=").decode()


def _decode(value: str) -> dict[str, object]:
    return json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))


def _hash(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000).hex()
    return salt, digest


@dataclass(slots=True)
class User:
    user_id: str
    name: str
    email: str
    salt: str
    password_hash: str

    def public(self) -> dict[str, str]:
        return {"user_id": self.user_id, "name": self.name, "email": self.email}


class AuthService:
    """Issue signed access/refresh tokens and retain users for the running service."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._refresh_tokens: set[str] = set()

    def register(self, name: str, email: str, password: str) -> User:
        email = email.strip().lower()
        if email in self._users:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this email")
        salt, password_hash = _hash(password)
        user = User(secrets.token_urlsafe(12), name.strip(), email, salt, password_hash)
        self._users[email] = user
        return user

    def login(self, email: str, password: str) -> User:
        user = self._users.get(email.strip().lower())
        if user is None or not hmac.compare_digest(_hash(password, user.salt)[1], user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
        return user

    def _token(self, user: User, token_type: str, lifetime: timedelta) -> str:
        now = datetime.now(timezone.timezone.utc)
        header = _encode({"alg": "HS256", "typ": "JWT"})
        payload = _encode({"sub": user.user_id, "email": user.email, "type": token_type, "iat": int(now.timestamp()), "exp": int((now + lifetime).timestamp())})
        signature = hmac.new(settings.jwt_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        return f"{header}.{payload}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"

    def token_pair(self, user: User) -> dict[str, object]:
        access = self._token(user, "access", timedelta(minutes=settings.jwt_access_token_minutes))
        refresh = self._token(user, "refresh", timedelta(days=settings.jwt_refresh_token_days))
        self._refresh_tokens.add(refresh)
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer", "user": user.public()}

    def user_from_token(self, token: str, expected_type: str = "access") -> User:
        try:
            header, payload, signature = token.split(".")
            expected = hmac.new(settings.jwt_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
            if not hmac.compare_digest(expected, base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))): raise ValueError
            claims = _decode(payload)
            if claims["type"] != expected_type or int(claims["exp"]) < int(datetime.now(timezone.timezone.utc).timestamp()): raise ValueError
            user = self._users.get(str(claims["email"]))
            if user is None or user.user_id != claims["sub"]: raise ValueError
            return user
        except (ValueError, KeyError, json.JSONDecodeError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from None

    def refresh(self, token: str) -> dict[str, object]:
        if token not in self._refresh_tokens: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")
        self._refresh_tokens.discard(token)
        return self.token_pair(self.user_from_token(token, "refresh"))

    def logout(self, token: str) -> None: self._refresh_tokens.discard(token)


auth_service = AuthService()
