"""Endpoints para precios de proveedor (comparador)."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.security import allow_all_staff, get_current_user
from app.security.jwt import allow_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/precios", tags=["Precios"])


@router.get("/", dependencies=[Depends(allow_all_staff)])
def listar_precios(
    producto_id: Optional[int] = None,
    proveedor_id: Optional[int] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
):
    if page < 1 or page_size < 1 or page_size > 500:
        raise HTTPException(400, "page o page_size inválido")
    query = db.query(models.PrecioProveedor)
    if producto_id:
        query = query.filter(models.PrecioProveedor.producto_id == producto_id)
    if proveedor_id:
        query = query.filter(models.PrecioProveedor.proveedor_id == proveedor_id)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            or_(
                models.PrecioProveedor.descripcion_busqueda.ilike(like),
                models.PrecioProveedor.sku_libre.ilike(like),
            )
        )
    rows = (
        query
        .order_by(desc(models.PrecioProveedor.creado_en))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": p.id,
                "proveedor_id": p.proveedor_id,
                "proveedor_nombre": p.proveedor.nombre_empresa if p.proveedor else None,
                "producto_id": p.producto_id,
                "producto_nombre": p.producto.nombre if p.producto else None,
                "descripcion_busqueda": p.descripcion_busqueda,
                "sku_libre": p.sku_libre,
                "precio": float(p.precio),
                "moneda": p.moneda,
                "fecha_vigencia_desde": p.fecha_vigencia_desde.isoformat() if p.fecha_vigencia_desde else None,
                "fecha_vigencia_hasta": p.fecha_vigencia_hasta.isoformat() if p.fecha_vigencia_hasta else None,
                "notas": p.notas,
                "fuente": p.fuente,
                "creado_en": p.creado_en.isoformat() if p.creado_en else None,
            }
            for p in rows
        ],
    }


@router.post("/", dependencies=[Depends(allow_all_staff)])
def crear_precio(
    payload: schemas.PrecioProveedorCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    proveedor = db.query(models.Proveedor).filter(models.Proveedor.id == payload.proveedor_id).first()
    if not proveedor:
        raise HTTPException(404, "Proveedor no encontrado")
    if payload.producto_id:
        producto = db.query(models.Producto).filter(models.Producto.id == payload.producto_id).first()
        if not producto:
            raise HTTPException(404, "Producto no encontrado")
    if not payload.producto_id and not payload.descripcion_busqueda:
        raise HTTPException(400, "Especifica producto_id o descripcion_busqueda")

    try:
        fila = models.PrecioProveedor(
            proveedor_id=payload.proveedor_id,
            producto_id=payload.producto_id,
            descripcion_busqueda=(payload.descripcion_busqueda or "").strip().lower() or None,
            sku_libre=payload.sku_libre,
            precio=payload.precio,
            moneda=(payload.moneda or "MXN").upper(),
            fecha_vigencia_desde=payload.fecha_vigencia_desde,
            fecha_vigencia_hasta=payload.fecha_vigencia_hasta,
            notas=payload.notas,
            fuente="MANUAL",
            creado_por_id=current_user.id,
        )
        db.add(fila)
        db.commit()
        db.refresh(fila)
        return {"id": fila.id}
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("precios.crear_precio falló")
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")


@router.delete("/{precio_id}", dependencies=[Depends(allow_admin)])
def borrar_precio(precio_id: int, db: Session = Depends(get_db)):
    fila = db.query(models.PrecioProveedor).filter(models.PrecioProveedor.id == precio_id).first()
    if not fila:
        raise HTTPException(404, "Precio no encontrado")
    db.delete(fila)
    db.commit()
    return {"id": precio_id, "deleted": True}


@router.get("/comparar", dependencies=[Depends(allow_all_staff)])
def comparar(
    producto_id: Optional[int] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Comparador: agrupa precios por proveedor para un producto o búsqueda libre."""
    if not producto_id and not q:
        raise HTTPException(400, "Especifica producto_id o q")
    query = db.query(models.PrecioProveedor)
    if producto_id:
        query = query.filter(models.PrecioProveedor.producto_id == producto_id)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            or_(
                models.PrecioProveedor.descripcion_busqueda.ilike(like),
                models.PrecioProveedor.sku_libre.ilike(like),
            )
        )
    rows = query.order_by(models.PrecioProveedor.precio.asc()).all()
    # Agrupar por proveedor: tomar el más reciente de cada uno
    por_proveedor: dict[int, dict] = {}
    for p in rows:
        if p.proveedor_id in por_proveedor:
            continue
        por_proveedor[p.proveedor_id] = {
            "proveedor_id": p.proveedor_id,
            "proveedor_nombre": p.proveedor.nombre_empresa if p.proveedor else None,
            "precio": float(p.precio),
            "moneda": p.moneda,
            "fecha_vigencia_desde": p.fecha_vigencia_desde.isoformat() if p.fecha_vigencia_desde else None,
            "fuente": p.fuente,
            "precio_id": p.id,
        }
    # Ordenar por precio asc
    resultados = sorted(por_proveedor.values(), key=lambda x: x["precio"])
    return {"items": resultados, "total": len(resultados)}
