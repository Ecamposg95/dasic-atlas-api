"""Service para upsert de productos fantasma desde líneas ad-hoc de cotizaciones."""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app import models


def _normalizar(descripcion: str) -> str:
    return (descripcion or "").strip().lower()


def upsert_from_detalle(
    db: Session,
    *,
    descripcion: str,
    sku_libre: Optional[str],
    costo: Decimal,
    moneda: str,
    proveedor_sugerido_id: Optional[int],
) -> Optional[int]:
    """Crea o actualiza un ProductoFantasma a partir de los datos de una línea
    ad-hoc. Retorna el `id` del fantasma para que el caller lo asigne a
    DetalleOrden.fantasma_id. Si la descripción está vacía o el costo es 0,
    no se hace upsert (retorna None)."""
    desc_norm = _normalizar(descripcion)
    if not desc_norm or not costo or Decimal(costo) <= 0:
        return None

    moneda = (moneda or "MXN").upper()

    existente = (
        db.query(models.ProductoFantasma)
        .filter(
            models.ProductoFantasma.descripcion_normalizada == desc_norm,
            models.ProductoFantasma.moneda_referencia == moneda,
        )
        .first()
    )

    if existente:
        existente.veces_solicitado = (existente.veces_solicitado or 0) + 1
        # Actualizar costo de referencia si es más reciente (siempre)
        existente.costo_referencia = Decimal(costo)
        if sku_libre and not existente.sku_libre:
            existente.sku_libre = sku_libre
        if proveedor_sugerido_id and not existente.proveedor_sugerido_id:
            existente.proveedor_sugerido_id = proveedor_sugerido_id
        db.flush()
        return existente.id

    nuevo = models.ProductoFantasma(
        descripcion_normalizada=desc_norm,
        descripcion_original=descripcion.strip(),
        sku_libre=sku_libre or None,
        costo_referencia=Decimal(costo),
        moneda_referencia=moneda,
        proveedor_sugerido_id=proveedor_sugerido_id,
        estado="PENDIENTE",
        veces_solicitado=1,
    )
    db.add(nuevo)
    db.flush()
    return nuevo.id
