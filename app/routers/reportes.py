"""
Router de reportes ejecutivos.

Reportes disponibles:
  - GET /api/reportes/ventas-mes?meses=12       → ventas por mes
  - GET /api/reportes/top-productos?dias=90     → productos más vendidos
  - GET /api/reportes/top-clientes?dias=90      → clientes top
  - GET /api/reportes/ranking-vendedores?dias=90 → vendedores
  - GET /api/reportes/ventas-mes/csv             → CSV export
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.security import allow_admin_asistente, allow_all_staff, get_current_user
from app.security.permissions import is_owner_scoped

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


def _scope_ventas(query, user):
    if is_owner_scoped(user, "read", "cotizacion"):
        return query.filter(models.OrdenVenta.vendedor_id == user.id)
    return query


def _to_mxn(monto, moneda, tc):
    if not monto:
        return 0.0
    if (moneda or "MXN") == "USD":
        return float(monto) * float(tc or 1)
    return float(monto)


@router.get("/ventas-mes", dependencies=[Depends(allow_all_staff)])
def ventas_mes(
    meses: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    ahora = datetime.utcnow()
    mes_actual = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    series = []
    meses_es = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
    for i in range(meses - 1, -1, -1):
        ref = mes_actual
        for _ in range(i):
            ref = (ref - timedelta(days=1)).replace(day=1)
        sig = (ref + timedelta(days=32)).replace(day=1)

        ventas_q = _scope_ventas(
            db.query(models.OrdenVenta).filter(
                models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
                models.OrdenVenta.fecha_creacion >= ref,
                models.OrdenVenta.fecha_creacion < sig,
            ),
            current_user,
        )
        ventas = ventas_q.all()
        cot_q = _scope_ventas(
            db.query(models.OrdenVenta).filter(
                models.OrdenVenta.estatus == models.EstatusOrden.COTIZACION,
                models.OrdenVenta.fecha_creacion >= ref,
                models.OrdenVenta.fecha_creacion < sig,
            ),
            current_user,
        )
        cot = cot_q.all()

        ventas_mxn = sum(_to_mxn(o.total, o.moneda, o.tipo_cambio) for o in ventas)
        cot_mxn = sum(_to_mxn(o.total, o.moneda, o.tipo_cambio) for o in cot)

        series.append({
            "mes": ref.strftime("%Y-%m"),
            "label": f"{meses_es[ref.month - 1]} {str(ref.year)[2:]}",
            "ventas_count": len(ventas),
            "ventas_mxn": round(ventas_mxn, 2),
            "cotizaciones_count": len(cot),
            "cotizaciones_mxn": round(cot_mxn, 2),
        })
    return {"series": series, "meses": meses}


@router.get("/top-productos", dependencies=[Depends(allow_all_staff)])
def top_productos(
    dias: int = Query(90, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    desde = datetime.utcnow() - timedelta(days=dias)

    base_q = (
        db.query(
            models.Producto.id,
            models.Producto.sku_comercial,
            models.Producto.sku,
            models.Producto.nombre,
            models.Producto.marca,
            func.coalesce(func.sum(models.DetalleOrden.cantidad), 0).label("qty"),
            func.coalesce(func.sum(models.DetalleOrden.subtotal), 0).label("monto"),
            func.count(models.DetalleOrden.id).label("apariciones"),
        )
        .join(models.DetalleOrden, models.DetalleOrden.producto_id == models.Producto.id)
        .join(models.OrdenVenta, models.DetalleOrden.orden_id == models.OrdenVenta.id)
        .filter(models.OrdenVenta.fecha_creacion >= desde)
    )
    if is_owner_scoped(current_user, "read", "cotizacion"):
        base_q = base_q.filter(models.OrdenVenta.vendedor_id == current_user.id)

    rows = (
        base_q.group_by(models.Producto.id)
        .order_by(desc(func.sum(models.DetalleOrden.cantidad)))
        .limit(limit)
        .all()
    )
    return [
        {
            "producto_id": r.id,
            "sku": r.sku_comercial or r.sku,
            "nombre": r.nombre,
            "marca": r.marca,
            "cantidad_total": int(r.qty or 0),
            "apariciones": int(r.apariciones or 0),
            "monto_mxn": float(r.monto or 0),
        }
        for r in rows
    ]


@router.get("/top-clientes", dependencies=[Depends(allow_all_staff)])
def top_clientes(
    dias: int = Query(90, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    desde = datetime.utcnow() - timedelta(days=dias)

    q = (
        db.query(
            models.Cliente.id,
            models.Cliente.nombre_empresa,
            models.Cliente.saldo_actual,
            func.count(models.OrdenVenta.id).label("orden_count"),
            func.coalesce(func.sum(models.OrdenVenta.total), 0).label("total"),
        )
        .join(models.OrdenVenta, models.OrdenVenta.cliente_id == models.Cliente.id)
        .filter(
            models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
            models.OrdenVenta.fecha_creacion >= desde,
        )
    )
    if is_owner_scoped(current_user, "read", "cotizacion"):
        q = q.filter(models.OrdenVenta.vendedor_id == current_user.id)
    rows = q.group_by(models.Cliente.id).order_by(desc(func.sum(models.OrdenVenta.total))).limit(limit).all()

    return [
        {
            "cliente_id": r.id,
            "empresa": r.nombre_empresa,
            "orden_count": int(r.orden_count or 0),
            "monto_mxn": float(r.total or 0),
            "saldo_actual": float(r.saldo_actual or 0),
        }
        for r in rows
    ]


@router.get("/ranking-vendedores", dependencies=[Depends(allow_admin_asistente)])
def ranking_vendedores(
    dias: int = Query(90, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    desde = datetime.utcnow() - timedelta(days=dias)
    rows = (
        db.query(
            models.Usuario.id,
            models.Usuario.nombre,
            models.Usuario.email,
            func.count(models.OrdenVenta.id).label("orden_count"),
            func.coalesce(func.sum(models.OrdenVenta.total), 0).label("total"),
        )
        .join(models.OrdenVenta, models.OrdenVenta.vendedor_id == models.Usuario.id)
        .filter(
            models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
            models.OrdenVenta.fecha_creacion >= desde,
        )
        .group_by(models.Usuario.id)
        .order_by(desc(func.sum(models.OrdenVenta.total)))
        .limit(limit)
        .all()
    )
    return [
        {
            "usuario_id": r.id,
            "nombre": r.nombre,
            "email": r.email,
            "orden_count": int(r.orden_count or 0),
            "monto_mxn": float(r.total or 0),
        }
        for r in rows
    ]


@router.get("/ventas-mes/csv", dependencies=[Depends(allow_admin_asistente)])
def ventas_mes_csv(
    meses: int = 12,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    data = ventas_mes(meses=meses, db=db, current_user=current_user)
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["mes", "label", "ventas_count", "ventas_mxn", "cotizaciones_count", "cotizaciones_mxn"])
    for s in data["series"]:
        w.writerow([s["mes"], s["label"], s["ventas_count"], s["ventas_mxn"], s["cotizaciones_count"], s["cotizaciones_mxn"]])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ventas_por_mes.csv"},
    )
