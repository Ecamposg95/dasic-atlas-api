"""Router de tipo de cambio."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas
from app.db import get_db
from app.security import allow_all_staff
from app.services.fx_service import get_or_fetch, FXError

router = APIRouter(prefix="/api/fx", tags=["Tipo de cambio"])


@router.get(
    "/usd-mxn",
    response_model=schemas.TipoCambioDiaResponse,
    dependencies=[Depends(allow_all_staff)],
)
def usd_mxn(
    fecha: Optional[date] = Query(None, description="YYYY-MM-DD; default hoy"),
    db: Session = Depends(get_db),
):
    try:
        return get_or_fetch(db, fecha=fecha)
    except FXError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post(
    "/refresh",
    response_model=schemas.TipoCambioDiaResponse,
    dependencies=[Depends(allow_all_staff)],
)
def refresh(db: Session = Depends(get_db)):
    """Refresca TC del día desde la fuente externa. No es destructivo (sólo
    actualiza la cache); cualquier staff puede dispararlo."""
    try:
        return get_or_fetch(db, force=True)
    except FXError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
