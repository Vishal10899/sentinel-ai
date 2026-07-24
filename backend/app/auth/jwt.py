import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.settings import settings


def _encode(data: dict) -> str:
    return (
        base64.urlsafe_b64encode(
            json.dumps(
                data,
                separators=(",", ":"),
            ).encode()
        )
        .rstrip(b"=")
        .decode()
    )


def _decode(data: str) -> dict:
    return json.loads(
        base64.urlsafe_b64decode(
            data + "=" * (-len(data) % 4)
        )
    )


class JWTService:

    @staticmethod
    def create_token(
        *,
        user_id: str,
        email: str,
        token_type: str,
        expires: timedelta,
    ) -> str:

        now = datetime.now(timezone.utc)

        header = _encode(
            {
                "alg": "HS256",
                "typ": "JWT",
            }
        )

        payload = _encode(
            {
                "sub": user_id,
                "email": email,
                "type": token_type,
                "iat": int(now.timestamp()),
                "exp": int(
                    (now + expires).timestamp()
                ),
            }
        )

        signature = hmac.new(
            settings.jwt_secret.encode(),
            f"{header}.{payload}".encode(),
            hashlib.sha256,
        ).digest()

        signature = (
            base64.urlsafe_b64encode(signature)
            .rstrip(b"=")
            .decode()
        )

        return f"{header}.{payload}.{signature}"

    @staticmethod
    def verify(
        token: str,
        expected_type: str,
    ) -> dict:

        try:

            header, payload, signature = token.split(".")

            expected_signature = hmac.new(
                settings.jwt_secret.encode(),
                f"{header}.{payload}".encode(),
                hashlib.sha256,
            ).digest()

            if not hmac.compare_digest(
                expected_signature,
                base64.urlsafe_b64decode(
                    signature + "=" * (-len(signature) % 4)
                ),
            ):
                raise ValueError()

            claims = _decode(payload)

            if claims["type"] != expected_type:
                raise ValueError()

            if int(claims["exp"]) < int(
                datetime.now(timezone.utc).timestamp()
            ):
                raise ValueError()

            return claims

        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )