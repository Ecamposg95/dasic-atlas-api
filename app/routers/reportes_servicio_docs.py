"""Endpoints del documento Reporte de Servicio (acta de servicio ejecutado).

⚠ NO confundir con `routers/reportes.py` ni con el dashboard analítico
`/spa/reportes-servicio`. Este router sirve el documento hijo de una
OrdenVenta — análogo a Remision pero para líneas de tipo servicio.
Prefix `/api/reportes-servicio-docs` para evitar colisión semántica.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.security import allow_all_staff, get_current_user

router = APIRouter(
    prefix="/api/reportes-servicio-docs",
    tags=["ReportesServicio (documentos)"],
)


def _generar_folio_rs(db: Session) -> str:
    """Folio RS-YYYYMM-NNNN con NNNN contador del mes."""
    hoy = datetime.utcnow()
    prefijo = f"RS-{hoy.strftime('%Y%m')}-"
    count = (
        db.query(models.ReporteServicio)
        .filter(models.ReporteServicio.folio.like(f"{prefijo}%"))
        .count()
    )
    return f"{prefijo}{count + 1:04d}"


def _serializar(r: models.ReporteServicio) -> dict:
    return {
        "id": r.id,
        "folio": r.folio,
        "orden_venta_id": r.orden_venta_id,
        "orden_venta_folio": r.orden_venta.folio if r.orden_venta else None,
        "cliente_nombre": (
            r.orden_venta.cliente.nombre_empresa
            if r.orden_venta and r.orden_venta.cliente
            else None
        ),
        "fecha_reporte": r.fecha_reporte.isoformat() if r.fecha_reporte else None,
        "tecnico_nombre": r.tecnico_nombre,
        "cliente_recibe_nombre": r.cliente_recibe_nombre,
        "recibido_at": r.recibido_at.isoformat() if r.recibido_at else None,
        "observaciones": r.observaciones,
        "creado_en": r.creado_en.isoformat() if r.creado_en else None,
    }


@router.get("/", dependencies=[Depends(allow_all_staff)])
def listar(
    orden_venta_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
):
    if page < 1 or page_size < 1 or page_size > 500:
        raise HTTPException(400, "page o page_size inválido")
    query = db.query(models.ReporteServicio)
    if orden_venta_id:
        query = query.filter(models.ReporteServicio.orden_venta_id == orden_venta_id)
    rows = (
        query
        .order_by(desc(models.ReporteServicio.creado_en))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "page": page,
        "page_size": page_size,
        "items": [_serializar(r) for r in rows],
    }


@router.post("/", dependencies=[Depends(allow_all_staff)])
def crear(
    payload: schemas.ReporteServicioCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    orden = (
        db.query(models.OrdenVenta)
        .filter(models.OrdenVenta.id == payload.orden_venta_id)
        .first()
    )
    if not orden:
        raise HTTPException(404, "Orden de venta no encontrada")

    tiene_servicios = any(
        (d.tipo_linea == "servicio_catalogo" or d.servicio_id is not None)
        for d in orden.detalles
    )
    if not tiene_servicios:
        raise HTTPException(400, "La cotización no tiene líneas de servicio")

    try:
        nuevo = models.ReporteServicio(
            folio=_generar_folio_rs(db),
            orden_venta_id=orden.id,
            tecnico_nombre=payload.tecnico_nombre,
            cliente_recibe_nombre=payload.cliente_recibe_nombre,
            observaciones=payload.observaciones,
            creado_por_id=current_user.id,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return _serializar(nuevo)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(500, "Error al crear reporte de servicio")


@router.get("/{id}", dependencies=[Depends(allow_all_staff)])
def detalle(id: int, db: Session = Depends(get_db)):
    r = (
        db.query(models.ReporteServicio)
        .filter(models.ReporteServicio.id == id)
        .first()
    )
    if not r:
        raise HTTPException(404, "Reporte no encontrado")
    return _serializar(r)


@router.patch("/{id}/recepcion", dependencies=[Depends(allow_all_staff)])
def registrar_recepcion(
    id: int,
    cliente_recibe_nombre: str,
    db: Session = Depends(get_db),
):
    r = (
        db.query(models.ReporteServicio)
        .filter(models.ReporteServicio.id == id)
        .first()
    )
    if not r:
        raise HTTPException(404, "Reporte no encontrado")
    if r.recibido_at:
        raise HTTPException(409, "El reporte ya tiene recepción registrada")
    r.cliente_recibe_nombre = cliente_recibe_nombre
    r.recibido_at = datetime.utcnow()
    db.commit()
    db.refresh(r)
    return _serializar(r)
