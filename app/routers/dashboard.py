"""
Dashboard premium DASIC.

Endpoints granulares (cada uno cacheable por separado en el frontend) y
role-aware: vendedor ve solo sus cotizaciones/ventas; admin/gerente ven todo.

Endpoints:
  GET /api/dashboard/hero       — 4 KPIs con delta + sparkline
  GET /api/dashboard/pipeline   — kanban (nueva, seguimiento, por_vencer, vencida, convertida)
  GET /api/dashboard/tendencia  — ventas + cotizaciones por mes (últimos N meses)
  GET /api/dashboard/alertas    — cotizaciones por vencer, stock crítico cotizado, saldos vencidos, OC borrador
  GET /api/dashboard/tops       — top clientes / productos / vendedores
  GET /api/dashboard/heatmap    — densidad de cotizaciones por día (últimos N días)
  GET /api/dashboard/kpis       — legacy (mantengo por compat)
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.security import allow_all_staff, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ---------- helpers ----------

ROLES_FULL_VIS = {
    models.RolUsuario.SUPERADMIN,
    models.RolUsuario.ADMINISTRADOR,
    models.RolUsuario.GERENTE_COMERCIAL,
}


def _can_see_team(user: "models.Usuario") -> bool:
    return user.rol in ROLES_FULL_VIS


def _scope(query, user: "models.Usuario"):
    if not _can_see_team(user):
        query = query.filter(models.OrdenVenta.vendedor_id == user.id)
    return query


def _naive(dt: Optional[datetime]) -> Optional[datetime]:
    """Devuelve dt sin tzinfo (las columnas TIMESTAMP WITH TZ vienen aware
    desde Postgres pero internamente comparamos con datetime.utcnow naive)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _to_mxn(monto: Optional[Decimal], moneda: Optional[str], tc: Optional[Decimal]) -> float:
    if not monto:
        return 0.0
    if (moneda or "MXN") == "USD":
        return float(monto) * float(tc or 1)
    return float(monto)


def _orden_mxn(o: "models.OrdenVenta") -> float:
    return _to_mxn(o.total, o.moneda, o.tipo_cambio)


def _date_range(window: str) -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    if window == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif window == "7d":
        start = now - timedelta(days=7)
    elif window == "30d":
        start = now - timedelta(days=30)
    elif window == "qtd":
        q_start_month = ((now.month - 1) // 3) * 3 + 1
        start = now.replace(month=q_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif window == "ytd":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  # mtd default
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, now


def _serialize_orden_breve(o: "models.OrdenVenta") -> dict:
    fc = _naive(o.fecha_creacion)
    return {
        "id": o.id,
        "folio": o.folio,
        "cliente": o.cliente.nombre_empresa if o.cliente else "",
        "contacto": o.cliente.contacto_nombre if o.cliente else None,
        "monto_mxn": round(_orden_mxn(o), 2),
        "moneda": o.moneda,
        "vendedor": o.vendedor.nombre if o.vendedor else None,
        "fecha": fc.isoformat() if fc else None,
    }


# ---------- 1. HERO ----------

@router.get("/hero", dependencies=[Depends(allow_all_staff)])
def hero(
    window: str = Query("mtd"),
    db: Session = Depends(get_db),
    current_user: "models.Usuario" = Depends(get_current_user),
):
    now = datetime.utcnow()
    start, end = _date_range(window)
    duracion = (end - start) or timedelta(days=1)
    start_prev = start - duracion
    end_prev = start

    def _ventas_q(_start, _end):
        return _scope(
            db.query(models.OrdenVenta).filter(
                models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
                models.OrdenVenta.fecha_creacion >= _start,
                models.OrdenVenta.fecha_creacion < _end,
            ),
            current_user,
        )

    ventas_now = _ventas_q(start, end).all()
    ventas_prev = _ventas_q(start_prev, end_prev).all()

    monto_now = sum(_orden_mxn(o) for o in ventas_now)
    monto_prev = sum(_orden_mxn(o) for o in ventas_prev)
    delta_pct = (
        round((monto_now - monto_prev) / monto_prev * 100, 1)
        if monto_prev > 0
        else None
    )

    sparkline_30d = []
    for i in range(29, -1, -1):
        d = (now - timedelta(days=i)).date()
        d0 = datetime.combine(d, datetime.min.time())
        d1 = d0 + timedelta(days=1)
        total = sum(_orden_mxn(o) for o in _ventas_q(d0, d1).all())
        sparkline_30d.append({"d": d.isoformat(), "v": round(total, 2)})

    pipeline = _scope(
        db.query(models.OrdenVenta).filter(
            models.OrdenVenta.estatus == models.EstatusOrden.COTIZACION,
        ),
        current_user,
    ).all()
    pipeline_monto = sum(_orden_mxn(o) for o in pipeline)
    pipeline_count = len(pipeline)
    pipeline_avg = (pipeline_monto / pipeline_count) if pipeline_count else 0

    cot_30d = _scope(
        db.query(models.OrdenVenta).filter(
            models.OrdenVenta.fecha_creacion >= now - timedelta(days=30),
        ),
        current_user,
    ).all()
    total_30d = len(cot_30d)
    venta_count = sum(
        1 for o in cot_30d if o.estatus != models.EstatusOrden.COTIZACION
    )
    conversion_pct = (venta_count / total_30d * 100) if total_30d else 0

    conv_spark = []
    for i in range(3, -1, -1):
        wk0 = now - timedelta(days=(i + 1) * 7)
        wk1 = now - timedelta(days=i * 7)
        wk = _scope(
            db.query(models.OrdenVenta).filter(
                models.OrdenVenta.fecha_creacion >= wk0,
                models.OrdenVenta.fecha_creacion < wk1,
            ),
            current_user,
        ).all()
        ventas_wk = sum(1 for o in wk if o.estatus != models.EstatusOrden.COTIZACION)
        conv_spark.append(
            round(ventas_wk / len(wk) * 100, 1) if wk else 0
        )

    detalles_q = (
        db.query(models.DetalleOrden)
        .join(models.OrdenVenta, models.DetalleOrden.orden_id == models.OrdenVenta.id)
        .filter(
            models.OrdenVenta.fecha_creacion >= start,
            models.OrdenVenta.fecha_creacion < end,
        )
    )
    if not _can_see_team(current_user):
        detalles_q = detalles_q.filter(models.OrdenVenta.vendedor_id == current_user.id)
    detalles = detalles_q.all()
    suma_subt = sum(float(d.subtotal or 0) for d in detalles)
    margen_pct = (
        sum(float(d.utilidad_aplicada or 0) * float(d.subtotal or 0) for d in detalles)
        / suma_subt
        if suma_subt > 0
        else 0
    )

    return {
        "window": window,
        "ventas": {
            "monto_mxn": round(monto_now, 2),
            "count": len(ventas_now),
            "delta_pct": delta_pct,
            "sparkline_30d": sparkline_30d,
        },
        "pipeline": {
            "monto_mxn": round(pipeline_monto, 2),
            "count": pipeline_count,
            "ticket_promedio_mxn": round(pipeline_avg, 2),
        },
        "conversion": {
            "tasa_pct": round(conversion_pct, 1),
            "target_pct": 50.0,
            "sparkline_4w": conv_spark,
        },
        "margen": {
            "pct": round(margen_pct, 1),
            "muestra_lineas": len(detalles),
        },
    }


# ---------- 2. PIPELINE ----------

@router.get("/pipeline", dependencies=[Depends(allow_all_staff)])
def pipeline(
    db: Session = Depends(get_db),
    current_user: "models.Usuario" = Depends(get_current_user),
):
    now = datetime.utcnow()

    abiertas = _scope(
        db.query(models.OrdenVenta).filter(
            models.OrdenVenta.estatus == models.EstatusOrden.COTIZACION,
        ),
        current_user,
    ).all()

    convertidas = _scope(
        db.query(models.OrdenVenta).filter(
            models.OrdenVenta.estatus.in_(
                [models.EstatusOrden.PENDIENTE, models.EstatusOrden.PAGADA]
            ),
            models.OrdenVenta.fecha_creacion >= now - timedelta(days=30),
        ),
        current_user,
    ).all()

    columnas = {k: [] for k in ("nueva", "seguimiento", "por_vencer", "vencida", "convertida")}

    for o in abiertas:
        fc = _naive(o.fecha_creacion)
        fv = _naive(o.fecha_vencimiento)
        edad = (now - fc).days if fc else 0
        dias_rest = (fv - now).days if fv else None
        item = _serialize_orden_breve(o)
        item["edad_dias"] = edad
        item["dias_restantes"] = dias_rest

        if dias_rest is not None and dias_rest < 0:
            columnas["vencida"].append(item)
        elif dias_rest is not None and dias_rest <= 3:
            columnas["por_vencer"].append(item)
        elif edad < 1:
            columnas["nueva"].append(item)
        else:
            columnas["seguimiento"].append(item)

    for o in convertidas:
        item = _serialize_orden_breve(o)
        item["estatus"] = (
            o.estatus.value if hasattr(o.estatus, "value") else str(o.estatus)
        )
        columnas["convertida"].append(item)

    out = {}
    for key, items in columnas.items():
        items.sort(key=lambda x: x.get("monto_mxn", 0), reverse=True)
        out[key] = {
            "items": items[:25],
            "count": len(items),
            "monto_total_mxn": round(sum(x.get("monto_mxn", 0) for x in items), 2),
        }
    return out


# ---------- 3. TENDENCIA ----------

@router.get("/tendencia", dependencies=[Depends(allow_all_staff)])
def tendencia(
    meses: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db),
    current_user: "models.Usuario" = Depends(get_current_user),
):
    now = datetime.utcnow()
    mes_actual = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    series: List[dict] = []
    for i in range(meses - 1, -1, -1):
        ref = mes_actual
        for _ in range(i):
            ref = (ref - timedelta(days=1)).replace(day=1)
        siguiente = (ref + timedelta(days=32)).replace(day=1)

        ventas = _scope(
            db.query(models.OrdenVenta).filter(
                models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
                models.OrdenVenta.fecha_creacion >= ref,
                models.OrdenVenta.fecha_creacion < siguiente,
            ),
            current_user,
        ).all()

        cotizaciones = _scope(
            db.query(models.OrdenVenta).filter(
                models.OrdenVenta.estatus == models.EstatusOrden.COTIZACION,
                models.OrdenVenta.fecha_creacion >= ref,
                models.OrdenVenta.fecha_creacion < siguiente,
            ),
            current_user,
        ).all()

        meses_es_short = [
            "ene", "feb", "mar", "abr", "may", "jun",
            "jul", "ago", "sep", "oct", "nov", "dic",
        ]
        label = f"{meses_es_short[ref.month - 1]} {str(ref.year)[2:]}"
        series.append({
            "mes": ref.strftime("%Y-%m"),
            "label": label,
            "ventas_mxn": round(sum(_orden_mxn(o) for o in ventas), 2),
            "ventas_count": len(ventas),
            "cotizaciones_mxn": round(sum(_orden_mxn(o) for o in cotizaciones), 2),
            "cotizaciones_count": len(cotizaciones),
        })
    return {"series": series, "meses": meses}


# ---------- 4. ALERTAS ----------

@router.get("/alertas", dependencies=[Depends(allow_all_staff)])
def alertas(
    db: Session = Depends(get_db),
    current_user: "models.Usuario" = Depends(get_current_user),
):
    now = datetime.utcnow()

    por_vencer = _scope(
        db.query(models.OrdenVenta).filter(
            models.OrdenVenta.estatus == models.EstatusOrden.COTIZACION,
            models.OrdenVenta.fecha_vencimiento.is_not(None),
            models.OrdenVenta.fecha_vencimiento >= now,
            models.OrdenVenta.fecha_vencimiento <= now + timedelta(days=3),
        ),
        current_user,
    ).order_by(models.OrdenVenta.fecha_vencimiento.asc()).limit(15).all()

    por_vencer_items = []
    for o in por_vencer:
        item = _serialize_orden_breve(o)
        fv = _naive(o.fecha_vencimiento)
        item["dias_restantes"] = (fv - now).days if fv else None
        por_vencer_items.append(item)

    productos_criticos = (
        db.query(models.Producto)
        .filter(models.Producto.stock_actual <= models.Producto.stock_minimo)
        .all()
    )
    critico_ids = [p.id for p in productos_criticos]
    stock_critico_cotizado: list[dict] = []
    if critico_ids:
        rows = (
            db.query(
                models.Producto.id,
                models.Producto.sku_comercial,
                models.Producto.sku,
                models.Producto.nombre,
                models.Producto.marca,
                models.Producto.stock_actual,
                models.Producto.stock_minimo,
                func.count(models.DetalleOrden.id).label("cotizaciones"),
                func.coalesce(func.sum(models.DetalleOrden.cantidad), 0).label("cantidad_cotizada"),
            )
            .join(
                models.DetalleOrden,
                models.DetalleOrden.producto_id == models.Producto.id,
            )
            .join(
                models.OrdenVenta,
                models.DetalleOrden.orden_id == models.OrdenVenta.id,
            )
            .filter(
                models.Producto.id.in_(critico_ids),
                models.OrdenVenta.estatus == models.EstatusOrden.COTIZACION,
            )
            .group_by(models.Producto.id)
            .order_by(func.count(models.DetalleOrden.id).desc())
            .limit(10)
            .all()
        )
        for r in rows:
            stock_critico_cotizado.append({
                "producto_id": r.id,
                "sku": r.sku_comercial or r.sku,
                "nombre": r.nombre,
                "marca": r.marca,
                "stock_actual": r.stock_actual,
                "stock_minimo": r.stock_minimo,
                "cotizaciones_activas": r.cotizaciones,
                "cantidad_cotizada": int(r.cantidad_cotizada),
            })

    saldos_vencidos: list[dict] = []
    clientes_con_saldo = (
        db.query(models.Cliente)
        .filter(models.Cliente.saldo_actual > 0)
        .all()
    )
    for c in clientes_con_saldo:
        ultimo_abono = (
            db.query(models.TransaccionCliente)
            .filter(
                models.TransaccionCliente.cliente_id == c.id,
                models.TransaccionCliente.tipo == models.TipoMovimiento.ABONO,
            )
            .order_by(models.TransaccionCliente.fecha.desc())
            .first()
        )
        ultima_fecha = _naive(ultimo_abono.fecha) if ultimo_abono else None
        if ultima_fecha:
            dias = (now - ultima_fecha).days
        else:
            dias = 999
        if dias > 60:
            saldos_vencidos.append({
                "id": c.id,
                "empresa": c.nombre_empresa,
                "contacto": c.contacto_nombre,
                "saldo": float(c.saldo_actual),
                "dias_sin_pago": dias,
            })
    saldos_vencidos.sort(key=lambda x: x["saldo"], reverse=True)

    oc_borrador = (
        db.query(models.OrdenCompra)
        .filter(models.OrdenCompra.estatus == "borrador")
        .order_by(models.OrdenCompra.fecha.desc())
        .limit(10)
        .all()
    )
    oc_items = []
    for oc in oc_borrador:
        oc_items.append({
            "id": oc.id,
            "folio": oc.folio,
            "proveedor": oc.proveedor.nombre_empresa if oc.proveedor else None,
            "total": float(oc.total or 0),
            "moneda": oc.moneda,
            "fecha": oc.fecha.isoformat() if oc.fecha else None,
        })

    return {
        "por_vencer_3d": por_vencer_items,
        "stock_critico_cotizado": stock_critico_cotizado,
        "saldos_vencidos": saldos_vencidos[:10],
        "oc_borrador": oc_items,
    }


# ---------- 5. TOPS ----------

@router.get("/tops", dependencies=[Depends(allow_all_staff)])
def tops(
    db: Session = Depends(get_db),
    current_user: "models.Usuario" = Depends(get_current_user),
):
    now = datetime.utcnow()
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Top clientes del mes (ventas cerradas)
    clientes_q = (
        db.query(
            models.Cliente.id,
            models.Cliente.nombre_empresa,
            models.Cliente.saldo_actual,
            func.count(models.OrdenVenta.id).label("orden_count"),
            func.sum(models.OrdenVenta.total).label("total"),
            models.OrdenVenta.moneda,
        )
        .join(models.OrdenVenta, models.OrdenVenta.cliente_id == models.Cliente.id)
        .filter(
            models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
            models.OrdenVenta.fecha_creacion >= inicio_mes,
        )
    )
    if not _can_see_team(current_user):
        clientes_q = clientes_q.filter(models.OrdenVenta.vendedor_id == current_user.id)
    clientes_rows = clientes_q.group_by(
        models.Cliente.id, models.OrdenVenta.moneda
    ).all()

    cli_dict: dict[int, dict] = {}
    for r in clientes_rows:
        bucket = cli_dict.setdefault(r.id, {
            "id": r.id,
            "empresa": r.nombre_empresa,
            "saldo": float(r.saldo_actual or 0),
            "orden_count": 0,
            "monto_mxn": 0.0,
        })
        bucket["orden_count"] += int(r.orden_count or 0)
        bucket["monto_mxn"] += _to_mxn(r.total, r.moneda, Decimal("1"))  # tc=1 simplificación
    top_clientes = sorted(cli_dict.values(), key=lambda x: x["monto_mxn"], reverse=True)[:5]

    # Top productos cotizados (últimos 30 días)
    prod_rows = (
        db.query(
            models.Producto.id,
            models.Producto.sku_comercial,
            models.Producto.sku,
            models.Producto.nombre,
            models.Producto.marca,
            models.Producto.stock_actual,
            models.Producto.stock_minimo,
            func.sum(models.DetalleOrden.cantidad).label("qty"),
            func.count(models.DetalleOrden.id).label("apariciones"),
        )
        .join(models.DetalleOrden, models.DetalleOrden.producto_id == models.Producto.id)
        .join(models.OrdenVenta, models.DetalleOrden.orden_id == models.OrdenVenta.id)
        .filter(models.OrdenVenta.fecha_creacion >= now - timedelta(days=30))
        .group_by(models.Producto.id)
        .order_by(func.sum(models.DetalleOrden.cantidad).desc())
        .limit(5)
        .all()
    )
    top_productos = [
        {
            "id": r.id,
            "sku": r.sku_comercial or r.sku,
            "nombre": r.nombre,
            "marca": r.marca,
            "cantidad_total": int(r.qty or 0),
            "apariciones": int(r.apariciones or 0),
            "stock_actual": r.stock_actual,
            "stock_minimo": r.stock_minimo,
            "stock_riesgo": (r.stock_actual or 0) <= (r.stock_minimo or 0),
        }
        for r in prod_rows
    ]

    # Top vendedores (sólo full-vis)
    top_vendedores = []
    if _can_see_team(current_user):
        vrows = (
            db.query(
                models.Usuario.id,
                models.Usuario.nombre,
                func.count(models.OrdenVenta.id).label("orden_count"),
                func.sum(models.OrdenVenta.total).label("total"),
                models.OrdenVenta.moneda,
            )
            .join(models.OrdenVenta, models.OrdenVenta.vendedor_id == models.Usuario.id)
            .filter(
                models.OrdenVenta.estatus != models.EstatusOrden.COTIZACION,
                models.OrdenVenta.fecha_creacion >= inicio_mes,
            )
            .group_by(models.Usuario.id, models.OrdenVenta.moneda)
            .all()
        )
        ven_dict: dict[int, dict] = {}
        for r in vrows:
            bucket = ven_dict.setdefault(r.id, {
                "id": r.id,
                "nombre": r.nombre,
                "orden_count": 0,
                "monto_mxn": 0.0,
            })
            bucket["orden_count"] += int(r.orden_count or 0)
            bucket["monto_mxn"] += _to_mxn(r.total, r.moneda, Decimal("1"))
        top_vendedores = sorted(ven_dict.values(), key=lambda x: x["monto_mxn"], reverse=True)[:5]

    return {
        "clientes": top_clientes,
        "productos": top_productos,
        "vendedores": top_vendedores,
        "ve_equipo": _can_see_team(current_user),
    }


# ---------- 6. HEATMAP ----------

@router.get("/heatmap", dependencies=[Depends(allow_all_staff)])
def heatmap(
    dias: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: "models.Usuario" = Depends(get_current_user),
):
    now = datetime.utcnow()
    start = (now - timedelta(days=dias - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    rows = _scope(
        db.query(models.OrdenVenta.fecha_creacion).filter(
            models.OrdenVenta.fecha_creacion >= start,
        ),
        current_user,
    ).all()

    counts: dict[str, int] = defaultdict(int)
    for (f,) in rows:
        if f is None:
            continue
        counts[f.date().isoformat()] += 1

    series = []
    for i in range(dias):
        d = (start + timedelta(days=i)).date().isoformat()
        series.append({"d": d, "v": counts.get(d, 0)})

    return {
        "days": series,
        "max": max((s["v"] for s in series), default=0),
        "total": sum(s["v"] for s in series),
    }


# ---------- LEGACY ----------

@router.get("/kpis", dependencies=[Depends(allow_all_staff)])
def kpis(
    db: Session = Depends(get_db),
    current_user: "models.Usuario" = Depends(get_current_user),
):
    """Endpoint legacy. Devuelve un superset compacto que el dashboard
    viejo aún consume mientras se migra al hero/pipeline/tendencia."""
    h = hero(window="mtd", db=db, current_user=current_user)
    p = pipeline(db=db, current_user=current_user)
    t = tendencia(meses=6, db=db, current_user=current_user)
    a = alertas(db=db, current_user=current_user)

    productos = db.query(models.Producto).all()
    return {
        "cotizaciones": {
            "activas": h["pipeline"]["count"],
            "vencidas": p["vencida"]["count"],
            "por_vencer_3d": p["por_vencer"]["count"],
        },
        "ventas": {
            "mes_total": h["ventas"]["monto_mxn"],
            "mes_count": h["ventas"]["count"],
        },
        "ordenes_compra": {
            "total": db.query(models.OrdenCompra).count(),
            "borrador": len(a["oc_borrador"]),
            "recibidas": db.query(models.OrdenCompra)
                .filter(models.OrdenCompra.estatus == "recibido")
                .count(),
        },
        "inventario": {
            "stock_critico": sum(
                1 for p in productos if (p.stock_actual or 0) <= (p.stock_minimo or 0)
            ),
            "sin_stock": sum(1 for p in productos if (p.stock_actual or 0) <= 0),
            "total_skus": len(productos),
        },
        "clientes": {"total": db.query(models.Cliente).count()},
        "tendencia_ventas_6m": [
            {"mes": s["label"], "total": s["ventas_mxn"]} for s in t["series"]
        ],
    }
