from __future__ import annotations

from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .settings import get_settings

settings = get_settings()

security_scheme = HTTPBearer(auto_error=False)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as exc:  # pragma: no cover - invalid tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    return payload


def get_current_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return decode_token(credentials.credentials)


def require_roles(
    required: list[str], allowed_to_assign: list[str] | None = None
) -> Callable[[dict], dict]:
    def dependency(payload: dict = Depends(get_current_payload)) -> dict:
        roles = payload.get("roles", [])
        if not any(role in roles for role in required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        if allowed_to_assign is not None:
            payload["_allowed_to_assign"] = allowed_to_assign
        return payload

    return dependency


def enforce_allowed_roles(payload: dict, target_roles: list[str]) -> None:
    allowed = payload.get("_allowed_to_assign")
    if allowed is None or "admin" in payload.get("roles", []):
        return
    if not all(role in allowed for role in target_roles or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign requested roles",
        )
