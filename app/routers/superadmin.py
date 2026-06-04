"""Consola super-admin: configuración en runtime."""
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import models
from app.db import get_db
from app.security import get_current_user
from app.security.jwt import allow_superadmin
from app.core.runtime_config import EDITABLE_KEYS, effective_summary

router = APIRouter(prefix="/api/superadmin", tags=["Super-Admin"])


class ConfigSet(BaseModel):
    clave: str
    valor: str | None  # null = borra el override (vuelve al default)


def _validar(clave: str, valor: str | None) -> None:
    if clave not in EDITABLE_KEYS:
        raise HTTPException(400, f"Clave no editable: {clave}")
    if valor is None:
        return
    if clave == "iva_rate":
        try:
            v = Decimal(str(valor))
        except (InvalidOperation, ValueError):
            raise HTTPException(400, "iva_rate debe ser número (ej. 0.16)")
        if v < 0 or v > 1:
            raise HTTPException(400, "iva_rate debe estar entre 0 y 1")
    elif clave == "quote_validity_days":
        try:
            n = int(valor)
        except (ValueError, TypeError):
            raise HTTPException(400, "quote_validity_days debe ser entero")
        if n < 1:
            raise HTTPException(400, "quote_validity_days debe ser ≥ 1")


@router.get("/config", dependencies=[Depends(allow_superadmin)])
def get_config(db: Session = Depends(get_db)):
    return {"items": effective_summary(db)}


@router.put("/config", dependencies=[Depends(allow_superadmin)])
def set_config(
    payload: ConfigSet,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    _validar(payload.clave, payload.valor)
    row = db.query(models.PlatformConfig).filter(models.PlatformConfig.clave == payload.clave).first()
    if payload.valor is None:
        if row:
            db.delete(row)
    else:
        if row:
            row.valor = payload.valor
            row.actualizado_por_id = current_user.id
        else:
            db.add(models.PlatformConfig(clave=payload.clave, valor=payload.valor, actualizado_por_id=current_user.id))
    db.commit()
    return {"items": effective_summary(db)}
