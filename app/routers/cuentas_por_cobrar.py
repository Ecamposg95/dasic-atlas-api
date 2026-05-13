"""Dashboard de cuentas por cobrar (CRM Fase 6).

Endpoints:
  GET  /api/cuentas-por-cobrar/vencimientos?dias=7
  POST /api/cuentas-por-cobrar/marcar-vencidos       (admin; job manual)
"""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.security import allow_admin, allow_all_staff
from app.services.cuentas_por_cobrar import (
    listar_vencimientos,
    marcar_vencidos,
)
from app.models.enums import TipoMovimiento


router = APIRouter(prefix="/api/cuentas-por-cobrar", tags=["Cuentas por cobrar"])


@router.get("/resumen", dependencies=[Depends(allow_all_staff)])
def resumen_cxc(db: Session = Depends(get_db)):
    """Métricas globales: total por cobrar, vencido, por vencer (7/30 días)."""
    rows = (
        db.query(models.TransaccionCliente)
        .filter(models.TransaccionCliente.tipo == TipoMovimiento.CARGO)
        .filter(models.TransaccionCliente.estatus_pago != "pagado")
        .all()
    )
    hoy = datetime.utcnow().date()
    total_pendiente = Decimal("0")
    total_vencido = Decimal("0")
    total_7 = Decimal("0")
    total_30 = Decimal("0")
    for r in rows:
        saldo = Decimal(r.monto or 0) - Decimal(r.monto_pagado or 0)
        if saldo <= 0:
            continue
        total_pendiente += saldo
        if r.fecha_vencimiento:
            delta = (r.fecha_vencimiento - hoy).days
            if delta < 0:
                total_vencido += saldo
            elif delta <= 7:
                total_7 += saldo
            elif delta <= 30:
                total_30 += saldo
    return {
        "total_pendiente": float(total_pendiente),
        "total_vencido": float(total_vencido),
        "por_vencer_7d": float(total_7),
        "por_vencer_30d": float(total_30),
        "n_cargos_abiertos": len([r for r in rows if (Decimal(r.monto or 0) - Decimal(r.monto_pagado or 0)) > 0]),
    }


@router.get("/vencimientos", dependencies=[Depends(allow_all_staff)])
def vencimientos(
    dias: int = Query(7, ge=0, le=365),
    db: Session = Depends(get_db),
):
    return {"items": listar_vencimientos(db, dias=dias)}


@router.post("/marcar-vencidos", dependencies=[Depends(allow_admin)])
def marcar_vencidos_endpoint(db: Session = Depends(get_db)):
    """Job manual: marca cargos con fecha_vencimiento < hoy como 'vencido'.
    Idempotente — solo afecta los que no estaban ya pagados/vencidos."""
    n = marcar_vencidos(db)
    return {"ok": True, "actualizados": n}
