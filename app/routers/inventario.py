"""Endpoints de inventario: movimientos, ajustes manuales, disponibilidad, liberación."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.models.enums import EstatusOrden, TipoMovimientoStock
from app.security import allow_admin_asistente, allow_all_staff, get_current_user
from app.services.stock_service import (
    aplicar_movimiento,
    disponibilidad,
    liberar_reservas_cotizacion,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inventario", tags=["Inventario"])


@router.get(
    "/movimientos",
    response_model=List[schemas.MovimientoStockResponse],
    dependencies=[Depends(allow_all_staff)],
)
def listar_movimientos(
    producto_id: Optional[int] = None,
    dias: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    desde = datetime.utcnow() - timedelta(days=dias)
    q = db.query(models.MovimientoStock).filter(models.MovimientoStock.creado_en >= desde)
    if producto_id:
        q = q.filter(models.MovimientoStock.producto_id == producto_id)
    return q.order_by(models.MovimientoStock.creado_en.desc()).limit(500).all()


@router.post(
    "/movimientos",
    response_model=schemas.MovimientoStockResponse,
)
def crear_ajuste_manual(
    payload: schemas.AjusteManualIn,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    from app.security.permissions import require
    require(current_user, "ajuste", "stock")  # admin/gerente/operativo OK; ventas 403
    producto = db.get(models.Producto, payload.producto_id)
    if not producto:
        raise HTTPException(404, "Producto no encontrado")
    try:
        mov = aplicar_movimiento(
            db,
            producto=producto,
            tipo=TipoMovimientoStock.AJUSTE.value,
            cantidad=payload.cantidad,
            referencia_tipo="manual",
            motivo=payload.motivo,
            usuario=current_user,
        )
        db.commit()
        db.refresh(mov)
        return mov
    except ValueError as exc:
        db.rollback()
        raise HTTPException(400, str(exc))


@router.get(
    "/disponibilidad/{producto_id}",
    response_model=schemas.DisponibilidadResponse,
    dependencies=[Depends(allow_all_staff)],
)
def disponibilidad_producto(producto_id: int, db: Session = Depends(get_db)):
    producto = db.get(models.Producto, producto_id)
    if not producto:
        raise HTTPException(404, "Producto no encontrado")
    return disponibilidad(db, producto)


@router.post("/liberar-vencidas", dependencies=[Depends(allow_admin_asistente)])
def liberar_vencidas(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Libera reservas de cotizaciones cuya fecha_vencimiento ya pasó. Idempotente."""
    try:
        ahora = datetime.utcnow()
        candidatas = (
            db.query(models.OrdenVenta)
            .filter(
                models.OrdenVenta.estatus == EstatusOrden.COTIZACION,
                models.OrdenVenta.fecha_vencimiento.is_not(None),
                models.OrdenVenta.fecha_vencimiento < ahora,
            )
            .all()
        )
        total_liberadas = 0
        for cot in candidatas:
            total_liberadas += liberar_reservas_cotizacion(
                db,
                cotizacion_id=cot.id,
                motivo="vencimiento automático",
                usuario=current_user,
            )
        db.commit()
        return {
            "cotizaciones_revisadas": len(candidatas),
            "productos_liberados": total_liberadas,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("inventario.liberar_vencidas falló")
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}")
