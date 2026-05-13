"""Dashboard de cuentas por cobrar (CRM Fase 6).

Endpoints:
  GET  /api/cuentas-por-cobrar/vencimientos?dias=7
  POST /api/cuentas-por-cobrar/marcar-vencidos       (admin; job manual)
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
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
    """Métricas globales: total por cobrar, vencido, por vencer (7/30 días).

    Calcula los 4 buckets con un único `SELECT … SUM(CASE …)` en lugar de
    cargar todas las transacciones en memoria. Mantiene la misma semántica
    de buckets que la versión Python (delta<0 vencido, 0≤delta≤7 por vencer
    7d, 8≤delta≤30 por vencer 30d).
    """
    hoy = datetime.utcnow().date()
    saldo_expr = models.TransaccionCliente.monto - func.coalesce(
        models.TransaccionCliente.monto_pagado, 0
    )
    venc = models.TransaccionCliente.fecha_vencimiento

    row = (
        db.query(
            func.coalesce(func.sum(saldo_expr), 0).label("total_pendiente"),
            func.coalesce(
                func.sum(case((venc < hoy, saldo_expr), else_=0)), 0
            ).label("total_vencido"),
            func.coalesce(
                func.sum(case((venc.between(hoy, hoy + timedelta(days=7)), saldo_expr), else_=0)),
                0,
            ).label("total_7"),
            func.coalesce(
                func.sum(
                    case(
                        (venc.between(hoy + timedelta(days=8), hoy + timedelta(days=30)), saldo_expr),
                        else_=0,
                    )
                ),
                0,
            ).label("total_30"),
            func.count().label("n_cargos_abiertos"),
        )
        .filter(models.TransaccionCliente.tipo == TipoMovimiento.CARGO)
        .filter(models.TransaccionCliente.estatus_pago != "pagado")
        .filter(saldo_expr > 0)
        .one()
    )

    return {
        "total_pendiente": float(row.total_pendiente or 0),
        "total_vencido": float(row.total_vencido or 0),
        "por_vencer_7d": float(row.total_7 or 0),
        "por_vencer_30d": float(row.total_30 or 0),
        "n_cargos_abiertos": int(row.n_cargos_abiertos or 0),
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
