"""Catálogos: marcas con abreviatura para SKU interno.

Todas las marcas tienen un prefijo único (abreviatura) que se usa para
generar SKUs internos consecutivos: {ABREV}-{NNNN}. Ej: ABCS-0001,
SIE-0001, etc.

Fuentes de SKU consultadas para `siguiente_sku`:
- Productos cuya columna `sku` empieza con la abreviatura seguida de "-".

Permisos:
- Listar y sugerir SKU: cualquier staff (allow_all_staff).
- Crear/editar marcas: admin o gerente comercial (allow_admin_asistente).
- Eliminar marca: admin/gerente, y solo si no hay productos usándola.
"""

from __future__ import annotations

import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.security import allow_admin_asistente, allow_all_staff


router = APIRouter(prefix="/api/catalogos", tags=["Catálogos"])

_ALPHA_RE = re.compile(r"[^A-Z0-9]")


def normalizar_abreviatura(raw: str) -> str:
    """Mayúsculas, sin espacios ni símbolos. Máximo 20 chars."""
    if not raw:
        raise HTTPException(400, "abreviatura requerida")
    clean = _ALPHA_RE.sub("", raw.upper())[:20]
    if not clean or len(clean) < 2:
        raise HTTPException(400, "abreviatura debe tener al menos 2 caracteres alfanuméricos")
    return clean


def siguiente_sku_para(db: Session, abreviatura: str) -> str:
    """Calcula el siguiente SKU para una abreviatura.

    Escanea productos con SKU `{ABREV}-NNNN`, toma el max(N)+1 y formatea
    con padding a 4 dígitos. Si no hay productos previos, empieza en 0001.

    Esta función NO toma el advisory lock; el lock se toma en el momento
    de crear el producto (en _generate_internal_sku) para que el rango
    desde "sugerir" hasta "crear" no quede protegido (intencional: solo
    es preview).
    """
    pattern = f"{abreviatura}-%"
    rows = (
        db.query(models.Producto.sku)
        .filter(models.Producto.sku.like(pattern))
        .all()
    )
    rx = re.compile(rf"^{re.escape(abreviatura)}-(\d+)$")
    max_n = 0
    for (sku,) in rows:
        if not sku:
            continue
        m = rx.match(sku)
        if m:
            n = int(m.group(1))
            if n > max_n:
                max_n = n
    return f"{abreviatura}-{max_n + 1:04d}"


def _contar_productos_por_marca(db: Session, nombre_marca: str, abreviatura: str) -> int:
    """Cuenta productos asociados a una marca.

    Asocia por DOS criterios (suma sin dobles):
    - producto.marca == nombre_marca (case-insensitive)
    - producto.sku LIKE '{abreviatura}-%'

    Usa SQL DISTINCT para evitar contar dos veces los que cumplen ambos.
    """
    q = (
        db.query(func.count(func.distinct(models.Producto.id)))
        .filter(
            (func.lower(models.Producto.marca) == nombre_marca.lower())
            | (models.Producto.sku.like(f"{abreviatura}-%"))
        )
    )
    return int(q.scalar() or 0)


# --- 1. LISTAR MARCAS ---
@router.get("/marcas", response_model=List[schemas.MarcaResponse], dependencies=[Depends(allow_all_staff)])
def listar_marcas(db: Session = Depends(get_db), q: Optional[str] = None):
    query = db.query(models.Marca)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            (models.Marca.nombre.ilike(like)) | (models.Marca.abreviatura.ilike(like))
        )
    marcas = query.order_by(models.Marca.nombre.asc()).all()

    resultado = []
    for m in marcas:
        n_prod = _contar_productos_por_marca(db, m.nombre, m.abreviatura)
        resultado.append(schemas.MarcaResponse(
            id=m.id,
            abreviatura=m.abreviatura,
            nombre=m.nombre,
            categoria=m.categoria,
            n_productos=n_prod,
            siguiente_sku=siguiente_sku_para(db, m.abreviatura),
        ))
    return resultado


# --- 2. OBTENER UNA MARCA ---
@router.get("/marcas/{abreviatura}", response_model=schemas.MarcaResponse, dependencies=[Depends(allow_all_staff)])
def obtener_marca(abreviatura: str, db: Session = Depends(get_db)):
    abrev = normalizar_abreviatura(abreviatura)
    m = db.query(models.Marca).filter(models.Marca.abreviatura == abrev).first()
    if not m:
        raise HTTPException(404, f"Marca con abreviatura '{abrev}' no encontrada")
    return schemas.MarcaResponse(
        id=m.id,
        abreviatura=m.abreviatura,
        nombre=m.nombre,
        categoria=m.categoria,
        n_productos=_contar_productos_por_marca(db, m.nombre, m.abreviatura),
        siguiente_sku=siguiente_sku_para(db, m.abreviatura),
    )


# --- 3. CREAR MARCA ---
@router.post("/marcas", response_model=schemas.MarcaResponse, dependencies=[Depends(allow_admin_asistente)])
def crear_marca(payload: schemas.MarcaCreate, db: Session = Depends(get_db)):
    abrev = normalizar_abreviatura(payload.abreviatura)
    nombre = payload.nombre.strip()
    if not nombre:
        raise HTTPException(400, "nombre requerido")

    existente = db.query(models.Marca).filter(models.Marca.abreviatura == abrev).first()
    if existente:
        raise HTTPException(409, f"Abreviatura '{abrev}' ya existe (marca: {existente.nombre})")

    m = models.Marca(
        abreviatura=abrev,
        nombre=nombre,
        categoria=(payload.categoria or "").strip() or None,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return schemas.MarcaResponse(
        id=m.id,
        abreviatura=m.abreviatura,
        nombre=m.nombre,
        categoria=m.categoria,
        n_productos=0,
        siguiente_sku=siguiente_sku_para(db, m.abreviatura),
    )


# --- 4. EDITAR MARCA (no permite cambiar abreviatura) ---
@router.put("/marcas/{abreviatura}", response_model=schemas.MarcaResponse, dependencies=[Depends(allow_admin_asistente)])
def editar_marca(
    abreviatura: str,
    payload: schemas.MarcaUpdate,
    db: Session = Depends(get_db),
):
    abrev = normalizar_abreviatura(abreviatura)
    m = db.query(models.Marca).filter(models.Marca.abreviatura == abrev).first()
    if not m:
        raise HTTPException(404, f"Marca '{abrev}' no encontrada")

    if payload.nombre is not None:
        new_nombre = payload.nombre.strip()
        if not new_nombre:
            raise HTTPException(400, "nombre no puede quedar vacío")
        m.nombre = new_nombre
    if payload.categoria is not None:
        m.categoria = payload.categoria.strip() or None

    db.commit()
    db.refresh(m)
    return schemas.MarcaResponse(
        id=m.id,
        abreviatura=m.abreviatura,
        nombre=m.nombre,
        categoria=m.categoria,
        n_productos=_contar_productos_por_marca(db, m.nombre, m.abreviatura),
        siguiente_sku=siguiente_sku_para(db, m.abreviatura),
    )


# --- 5. ELIMINAR MARCA (bloquea si hay productos) ---
@router.delete("/marcas/{abreviatura}", dependencies=[Depends(allow_admin_asistente)])
def eliminar_marca(abreviatura: str, db: Session = Depends(get_db)):
    abrev = normalizar_abreviatura(abreviatura)
    m = db.query(models.Marca).filter(models.Marca.abreviatura == abrev).first()
    if not m:
        raise HTTPException(404, f"Marca '{abrev}' no encontrada")

    n_prod = _contar_productos_por_marca(db, m.nombre, m.abreviatura)
    if n_prod > 0:
        raise HTTPException(
            409,
            f"No se puede eliminar: hay {n_prod} producto(s) usando esta marca. "
            "Reasigna o elimina los productos primero.",
        )

    db.delete(m)
    db.commit()
    return {"mensaje": f"Marca '{abrev}' eliminada"}


# --- 6. SUGERIR SIGUIENTE SKU (preview, sin reservar) ---
@router.get("/marcas/{abreviatura}/sugerir-sku", dependencies=[Depends(allow_all_staff)])
def sugerir_sku(abreviatura: str, db: Session = Depends(get_db)):
    abrev = normalizar_abreviatura(abreviatura)
    if not db.query(models.Marca).filter(models.Marca.abreviatura == abrev).first():
        raise HTTPException(404, f"Marca '{abrev}' no encontrada")
    return {
        "abreviatura": abrev,
        "siguiente_sku": siguiente_sku_para(db, abrev),
        "nota": "Preview sin reservar — el SKU se asigna al crear el producto",
    }


# --- 7. RESUMEN / STATS PARA DASHBOARD DEL MÓDULO ---
@router.get("/resumen", dependencies=[Depends(allow_all_staff)])
def resumen_catalogo(db: Session = Depends(get_db)):
    total_marcas = db.query(func.count(models.Marca.id)).scalar() or 0
    total_productos = db.query(func.count(models.Producto.id)).scalar() or 0
    productos_con_marca = (
        db.query(func.count(models.Producto.id))
        .filter(models.Producto.marca.is_not(None))
        .filter(models.Producto.marca != "")
        .scalar() or 0
    )
    return {
        "total_marcas": total_marcas,
        "total_productos": total_productos,
        "productos_con_marca": productos_con_marca,
        "productos_sin_marca": total_productos - productos_con_marca,
    }
