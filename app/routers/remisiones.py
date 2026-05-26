"""Endpoints de remisiones."""

import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.security import allow_all_staff, get_current_user

router = APIRouter(prefix="/api/remisiones", tags=["Remisiones"])


def _generar_folio_remision(db: Session) -> str:
    """Folio R-YYMM<NNNN> con consecutivo global por mes.

    Mismo patrón validado en `ventas.py::_generar_folio`: advisory lock
    transaccional + MAX(folio) + regex para extraer el consecutivo (tolera
    gaps por borrados y sufijos versionados).
    """
    hoy = datetime.utcnow()
    yymm = hoy.strftime("%y%m")
    prefijo = "R"

    # Advisory lock transaccional: serializa el cómputo entre llamadas concurrentes.
    lock_key = f"folio:{prefijo}:{yymm}"
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:k))"), {"k": lock_key})

    patron = f"{prefijo}-{yymm}%"
    ultimo = (
        db.query(func.max(models.Remision.folio))
        .filter(models.Remision.folio.like(patron))
        .scalar()
    )
    consecutivo = 1
    if ultimo:
        m = re.match(rf"{re.escape(prefijo)}-{re.escape(yymm)}(\d+)", ultimo)
        if m:
            consecutivo = int(m.group(1)) + 1
    return f"{prefijo}-{yymm}{consecutivo:04d}"


@router.get("/", dependencies=[Depends(allow_all_staff)])
def listar_remisiones(
    orden_venta_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
):
    if page < 1 or page_size < 1 or page_size > 500:
        raise HTTPException(400, "page o page_size inválido")
    query = db.query(models.Remision)
    if orden_venta_id:
        query = query.filter(models.Remision.orden_venta_id == orden_venta_id)
    rows = (
        query
        .order_by(desc(models.Remision.fecha_remision))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": r.id,
                "folio": r.folio,
                "orden_venta_id": r.orden_venta_id,
                "orden_folio": r.orden_venta.folio if r.orden_venta else None,
                "cliente_nombre": (r.orden_venta.cliente.nombre_empresa if r.orden_venta and r.orden_venta.cliente else None),
                "fecha_remision": r.fecha_remision.isoformat() if r.fecha_remision else None,
                "transportista": r.transportista,
                "recibido_por": r.recibido_por,
                "recibido_at": r.recibido_at.isoformat() if r.recibido_at else None,
                "lineas_count": len(r.detalles),
            }
            for r in rows
        ],
    }


@router.post("/", dependencies=[Depends(allow_all_staff)])
def crear_remision(
    payload: schemas.RemisionCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    orden = db.query(models.OrdenVenta).filter(models.OrdenVenta.id == payload.orden_venta_id).first()
    if not orden:
        raise HTTPException(404, "Orden de venta no encontrada")
    if orden.estatus == models.EstatusOrden.COTIZACION:
        raise HTTPException(400, "La orden todavía es cotización — convierte a venta antes de remisionar")
    if not payload.detalles:
        raise HTTPException(400, "Debe incluir al menos una línea")

    folio = _generar_folio_remision(db)
    try:
        rem = models.Remision(
            folio=folio,
            orden_venta_id=orden.id,
            transportista=payload.transportista,
            observaciones=payload.observaciones,
            creado_por_id=current_user.id,
        )
        db.add(rem)
        db.flush()
        for d in payload.detalles:
            db.add(models.DetalleRemision(
                remision_id=rem.id,
                detalle_orden_id=d.detalle_orden_id,
                descripcion=d.descripcion,
                sku=d.sku,
                cantidad=d.cantidad,
                observaciones_linea=d.observaciones_linea,
            ))
        db.commit()
        db.refresh(rem)
        return {"id": rem.id, "folio": rem.folio}
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(500, "Error al crear remisión")


@router.get("/{id}", dependencies=[Depends(allow_all_staff)])
def detalle_remision(id: int, db: Session = Depends(get_db)):
    rem = db.query(models.Remision).filter(models.Remision.id == id).first()
    if not rem:
        raise HTTPException(404, "Remisión no encontrada")
    return {
        "id": rem.id,
        "folio": rem.folio,
        "orden_venta_id": rem.orden_venta_id,
        "orden_folio": rem.orden_venta.folio if rem.orden_venta else None,
        "cliente_nombre": (rem.orden_venta.cliente.nombre_empresa if rem.orden_venta and rem.orden_venta.cliente else None),
        "fecha_remision": rem.fecha_remision.isoformat() if rem.fecha_remision else None,
        "transportista": rem.transportista,
        "recibido_por": rem.recibido_por,
        "recibido_at": rem.recibido_at.isoformat() if rem.recibido_at else None,
        "observaciones": rem.observaciones,
        "detalles": [
            {
                "id": d.id,
                "descripcion": d.descripcion,
                "sku": d.sku,
                "cantidad": d.cantidad,
                "observaciones_linea": d.observaciones_linea,
            }
            for d in rem.detalles
        ],
    }


@router.patch("/{id}/recepcion", dependencies=[Depends(allow_all_staff)])
def registrar_recepcion(
    id: int,
    recibido_por: str,
    db: Session = Depends(get_db),
):
    rem = db.query(models.Remision).filter(models.Remision.id == id).first()
    if not rem:
        raise HTTPException(404, "Remisión no encontrada")
    if rem.recibido_at:
        raise HTTPException(409, "Remisión ya tiene recepción registrada")
    rem.recibido_por = recibido_por
    rem.recibido_at = datetime.utcnow()
    db.commit()
    return {"id": rem.id, "recibido_at": rem.recibido_at.isoformat(), "recibido_por": rem.recibido_por}
