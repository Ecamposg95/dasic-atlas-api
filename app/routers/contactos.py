"""Directorio global de contactos (cross-empresa)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional

from app import models
from app.db import get_db
from app.security import allow_all_staff, get_current_user
from app.security.permissions import is_owner_scoped

router = APIRouter(prefix="/api/contactos", tags=["Contactos"])


@router.get("/", dependencies=[Depends(allow_all_staff)])
def listar_contactos(
    q: Optional[str] = None,
    cliente_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 200,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    if page < 1 or page_size < 1 or page_size > 500:
        raise HTTPException(400, "page o page_size inválido")
    query = (
        db.query(models.Contacto)
        .join(models.Cliente, models.Contacto.cliente_id == models.Cliente.id)
    )
    if is_owner_scoped(current_user, "read", "cliente"):
        query = query.filter(models.Cliente.creado_por_id == current_user.id)
    if cliente_id:
        query = query.filter(models.Contacto.cliente_id == cliente_id)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(
            models.Contacto.nombre.ilike(like),
            models.Contacto.email.ilike(like),
            models.Contacto.cargo.ilike(like),
        ))
    rows = (
        query.order_by(
            models.Cliente.nombre_empresa.asc(),
            models.Contacto.es_principal.desc(),
            models.Contacto.nombre.asc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": c.id,
                "cliente_id": c.cliente_id,
                "empresa_nombre": c.cliente.nombre_empresa if c.cliente else None,
                "nombre": c.nombre,
                "cargo": c.cargo,
                "email": c.email,
                "telefono": c.telefono,
                "es_principal": bool(c.es_principal),
            }
            for c in rows
        ],
    }


@router.get("/{contacto_id}/historial", dependencies=[Depends(allow_all_staff)])
def historial_contacto(contacto_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.OrdenVenta)
        .filter(models.OrdenVenta.contacto_id == contacto_id)
        .order_by(models.OrdenVenta.fecha_creacion.desc())
        .all()
    )
    return [
        {
            "id": o.id,
            "folio": o.folio,
            "fecha": o.fecha_creacion.isoformat() if o.fecha_creacion else None,
            "estatus": str(o.estatus.value if hasattr(o.estatus, "value") else o.estatus),
            "total": float(o.total) if getattr(o, "total", None) is not None else 0.0,
            "moneda": o.moneda,
        }
        for o in rows
    ]
