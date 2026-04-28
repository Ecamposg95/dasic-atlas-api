"""
Dashboard KPIs — server-side aggregations.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.dependencies import get_current_active_organization
from app.security import allow_all_staff

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/kpis", dependencies=[Depends(allow_all_staff)])
def kpis(
    organization_id: str = Depends(get_current_active_organization),
    db: Session = Depends(get_db),
):
    ahora = datetime.utcnow()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    hace_6_meses = (ahora.replace(day=1) - timedelta(days=180)).replace(day=1)

    # Cotizaciones
    cotizaciones_q = db.query(models.OrdenVenta).filter(
        models.OrdenVenta.organization_id == organization_id,
        models.OrdenVenta.estatus == models.EstatusOrden.COTIZACION,
    )
    cotiz_total = cotizaciones_q.count()
    cotiz_vencidas = cotizaciones_q.filter(
        models.OrdenVenta.fecha_vencimiento.isnot(None),
        models.OrdenVenta.fecha_vencimiento < ahora,
    ).count()
    cotiz_por_vencer = cotizaciones_q.filter(
        models.OrdenVenta.fecha_vencimiento.isnot(None),
        models.OrdenVenta.fecha_vencimiento >= ahora,
        models.OrdenVenta.fecha_vencimiento <= ahora + timedelta(days=3),
    ).count()

    # Ventas mes
    ventas_mes_total = (
        db.query(func.coalesce(func.sum(models.OrdenVenta.total), 0))
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
            models.OrdenVenta.fecha_creacion >= inicio_mes,
        )
        .scalar()
        or Decimal("0")
    )
    ventas_mes_count = (
        db.query(models.OrdenVenta)
        .filter(
            models.OrdenVenta.organization_id == organization_id,
            models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
            models.OrdenVenta.fecha_creacion >= inicio_mes,
        )
        .count()
    )

    # OC (no scoping por organization_id porque OrdenCompra no tiene tenant aún)
    oc_total = db.query(models.OrdenCompra).count()
    oc_borrador = (
        db.query(models.OrdenCompra)
        .filter(models.OrdenCompra.estatus == "borrador")
        .count()
    )
    oc_recibidas = (
        db.query(models.OrdenCompra)
        .filter(models.OrdenCompra.estatus == "recibido")
        .count()
    )

    # Inventario
    productos = db.query(models.Producto).all()
    stock_critico = sum(1 for p in productos if (p.stock_actual or 0) <= (p.stock_minimo or 0))
    sin_stock = sum(1 for p in productos if (p.stock_actual or 0) <= 0)

    # Clientes
    clientes_total = (
        db.query(models.Cliente)
        .filter(models.Cliente.organization_id == organization_id)
        .count()
    )

    # Tendencia ventas últimos 6 meses (por mes)
    tendencia: List[dict] = []
    for i in range(5, -1, -1):
        ref = (ahora.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        siguiente = (ref + timedelta(days=32)).replace(day=1)
        suma = (
            db.query(func.coalesce(func.sum(models.OrdenVenta.total), 0))
            .filter(
                models.OrdenVenta.organization_id == organization_id,
                models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
                models.OrdenVenta.fecha_creacion >= ref,
                models.OrdenVenta.fecha_creacion < siguiente,
            )
            .scalar()
            or 0
        )
        tendencia.append({"mes": ref.strftime("%b"), "total": float(suma)})

    return {
        "cotizaciones": {
            "activas": cotiz_total,
            "vencidas": cotiz_vencidas,
            "por_vencer_3d": cotiz_por_vencer,
        },
        "ventas": {
            "mes_total": float(ventas_mes_total),
            "mes_count": ventas_mes_count,
        },
        "ordenes_compra": {
            "total": oc_total,
            "borrador": oc_borrador,
            "recibidas": oc_recibidas,
        },
        "inventario": {
            "stock_critico": stock_critico,
            "sin_stock": sin_stock,
            "total_skus": len(productos),
        },
        "clientes": {
            "total": clientes_total,
        },
        "tendencia_ventas_6m": tendencia,
    }
