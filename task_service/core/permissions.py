from __future__ import annotations

from typing import Any

import httpx
from fastapi import Depends, HTTPException, status

from .logging import project_id_ctx_var, user_id_ctx_var
from .security import get_current_user
from .settings import settings

# Mapping of actions to roles allowed to perform them
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "create": {"Owner", "Manager", "Contributor"},
    "edit": {"Owner", "Manager", "Contributor"},
    "list": {"Owner", "Manager", "Contributor", "Viewer"},
}


async def _fetch_project_role(
    project_id: int,
    user_id: str,
    base_url: str | None = None,
) -> str | None:
    """Return the role of ``user_id`` in ``project_id``.

    The information is retrieved from the user service.  If the user is not a
    member of the project the service is expected to return a 404 status code.
    """
    base_url = base_url or str(settings.user_service_base_url)
    async with httpx.AsyncClient(base_url=base_url) as client:
        resp = await client.get(f"/projects/{project_id}/members/{user_id}")
        if resp.status_code == status.HTTP_404_NOT_FOUND:
            return None
        resp.raise_for_status()
        data = resp.json()
        return data.get("role")


def require_project_permission(action: str):
    """FastAPI dependency ensuring the current user has the required role.

    Parameters
    ----------
    action:
        The action being performed.  Must be one of ``create``, ``edit`` or
        ``list``.
    """

    allowed_roles = ROLE_PERMISSIONS[action]

    async def dependency(
        project_id: int,
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        role = await _fetch_project_role(project_id, user["user_id"])
        if role is None or role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        # Store identifiers in the logging context for traceability while
        # keeping the log free from sensitive information.
        project_id_ctx_var.set(str(project_id))
        user_id_ctx_var.set(user["user_id"])

        return {"project_id": project_id, "user_id": user["user_id"], "role": role}

    return dependency


__all__ = [
    "ROLE_PERMISSIONS",
    "require_project_permission",
]
