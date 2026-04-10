from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request

from app import models
from app.security import get_current_user


def get_current_active_organization(
    request: Request,
    x_organization_id: str | None = Header(default=None, alias="X-Organization-ID"),
    current_user: models.Usuario = Depends(get_current_user),
) -> str:
    """Resolves active organization context from header.

    Current stage: validates format and stores context in request.state.
    Full membership enforcement will be added when user-org mapping is introduced.
    """

    if not x_organization_id:
        raise HTTPException(status_code=400, detail="Falta header X-Organization-ID")

    try:
        org_uuid = str(UUID(x_organization_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="X-Organization-ID inválido") from exc

    request.state.organization_id = org_uuid
    request.state.current_user_id = current_user.id
    return org_uuid
