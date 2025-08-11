from __future__ import annotations

import time
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .settings import settings

JWKS_CACHE_TTL_SECONDS = 600
_jwks_cache: dict[str, tuple[dict[str, Any], float]] = {}

bearer_scheme = HTTPBearer(auto_error=False)


async def _get_jwk(kid: str) -> dict[str, Any]:
    cached = _jwks_cache.get(kid)
    now = time.time()
    if cached and cached[1] > now:
        return cached[0]

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(str(settings.auth_jwks_url))
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not fetch JWKS",
            ) from exc
    jwks = resp.json()
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            _jwks_cache[kid] = (jwk, now + JWKS_CACHE_TTL_SECONDS)
            return jwk
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    )


async def validate_token(token: str) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    kid = header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header"
        )
    jwk = await _get_jwk(kid)
    try:
        key = jwt.PyJWK.from_dict(jwk).key
        payload = jwt.decode(
            token, key, algorithms=[jwk["alg"]], options={"verify_aud": False}
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    payload = await validate_token(credentials.credentials)
    user_id = payload.get("sub")
    sector_id = payload.get("sector_id")
    if user_id is None or sector_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims"
        )
    return {"user_id": user_id, "sector_id": sector_id, "claims": payload}


__all__ = ["validate_token", "get_current_user"]
