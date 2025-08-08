from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

import jwt
from jwt.utils import base64url_encode
from passlib.context import CryptContext

from .settings import get_settings

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()
redis_client = redis.from_url(settings.redis_url) if settings.redis_url and redis else None

LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300


def hash_password(password: str) -> str:
    pepper = settings.password_pepper or ""
    return pwd_context.hash(password + pepper)


def verify_password(password: str, hashed: str) -> bool:
    pepper = settings.password_pepper or ""
    return pwd_context.verify(password + pepper, hashed)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expires_minutes)
    )
    to_encode.update({"exp": expire})
    headers = {"kid": settings.jwt_key_id}
    return jwt.encode(to_encode, settings.jwt_private_key, algorithm=settings.jwt_algorithm, headers=headers)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm], options={"verify_aud": False})


def get_jwk() -> dict[str, Any]:
    if settings.jwt_algorithm.startswith("RS"):
        from cryptography.hazmat.primitives import serialization

        public_key = serialization.load_pem_public_key(settings.jwt_public_key.encode())
        numbers = public_key.public_numbers()
        n = base64url_encode(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")).decode()
        e = base64url_encode(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")).decode()
        return {
            "kty": "RSA",
            "use": "sig",
            "kid": settings.jwt_key_id,
            "alg": settings.jwt_algorithm,
            "n": n,
            "e": e,
        }
    else:
        from cryptography.hazmat.primitives import serialization

        public_key = serialization.load_pem_public_key(settings.jwt_public_key.encode())
        raw = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        x = base64url_encode(raw).decode()
        return {
            "kty": "OKP",
            "crv": "Ed25519",
            "use": "sig",
            "kid": settings.jwt_key_id,
            "alg": settings.jwt_algorithm,
            "x": x,
        }


def get_jwks() -> dict[str, Any]:
    return {"keys": [get_jwk()]}


def register_failed_attempt(identifier: str) -> None:
    if redis_client:
        key = f"login:{identifier}"
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, LOGIN_WINDOW_SECONDS)


def clear_failed_attempts(identifier: str) -> None:
    if redis_client:
        redis_client.delete(f"login:{identifier}")


def is_throttled(identifier: str) -> bool:
    if not redis_client:
        return False
    val = redis_client.get(f"login:{identifier}")
    if not val:
        return False
    try:
        return int(val) >= LOGIN_ATTEMPTS
    except (TypeError, ValueError):
        return False
