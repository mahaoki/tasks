from __future__ import annotations

from typing import Iterable

import httpx
from fastapi import HTTPException, status

from ..core.settings import settings


class UserServiceClient:
    """Client for interacting with the user service."""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0) -> None:
        self.base_url = base_url or str(settings.user_service_base_url)
        self.timeout = timeout
        self._sector_cache: dict[int, str] = {}
        self._user_cache: set[int] = set()

    async def verify_users(self, user_ids: Iterable[int]) -> None:
        ids = [uid for uid in user_ids if uid not in self._user_cache]
        if not ids:
            return
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            ) as client:
                resp = await client.get(
                    "/users", params={"ids": ",".join(map(str, ids))}
                )
                resp.raise_for_status()
                data = resp.json()
                found = {user["id"] for user in data.get("users", [])}
                self._user_cache.update(found)
                missing = set(ids) - found
                if missing:
                    raise self._validation_error(
                        f"Invalid assignee_ids: {sorted(missing)}"
                    )
        except httpx.TimeoutException as exc:
            raise self._validation_error("User service request timed out") from exc
        except httpx.HTTPError as exc:
            raise self._validation_error("User service request failed") from exc

    async def get_sector_name(self, sector_id: int) -> str:
        if sector_id in self._sector_cache:
            return self._sector_cache[sector_id]

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            ) as client:
                resp = await client.get(f"/sectors/{sector_id}")
                if resp.status_code == 404:
                    raise self._validation_error("Invalid sector_id")
                resp.raise_for_status()
                data = resp.json()
                name = data.get("name")
                if not name:
                    raise self._validation_error("Invalid sector data")

                self._sector_cache[sector_id] = name
                return name
        except httpx.TimeoutException as exc:
            raise self._validation_error("User service request timed out") from exc
        except httpx.HTTPError as exc:
            raise self._validation_error("User service request failed") from exc

    def _validation_error(self, message: str) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message
        )
