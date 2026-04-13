from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.security import get_current_user, get_token_payload


def get_current_active_organization(
    request: Request,
    x_organization_id: str | None = Header(default=None, alias="X-Organization-ID"),
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> str:
    """Resolves active organization from header or token claim.

    MVP transition mode:
    - uses `X-Organization-ID` when provided.
    - falls back to JWT `org_id` claim when header is missing.
    """

    candidate_org_id = x_organization_id or payload.get("org_id")

    if not candidate_org_id:
        raise HTTPException(status_code=400, detail="Falta contexto de organización")

    try:
        org_uuid = str(UUID(str(candidate_org_id)))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Organization ID inválido") from exc

    membership = (
        db.query(models.UserOrganization)
        .filter(
            models.UserOrganization.user_id == current_user.id,
            models.UserOrganization.organization_id == org_uuid,
            models.UserOrganization.is_active.is_(True),
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Sin membresía activa para esta organización")

    request.state.organization_id = org_uuid
    request.state.current_user_id = current_user.id
    request.state.branch_id = membership.branch_id
    return org_uuid
