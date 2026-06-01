from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class DetalleRemisionInput(BaseModel):
    detalle_orden_id: Optional[int] = None
    descripcion: str
    sku: Optional[str] = None
    cantidad: int
    observaciones_linea: Optional[str] = None
    # Solo se usan para líneas fantasma ad-hoc (detalle_orden_id is None).
    # Para líneas de orden, el backend re-lee estos valores de DetalleOrden.
    clave_unidad_sat: Optional[str] = None
    precio_unitario: Optional[Decimal] = None


class RemisionCreate(BaseModel):
    orden_venta_id: int
    transportista: Optional[str] = None
    observaciones: Optional[str] = None
    mostrar_precios: bool = False
    detalles: List[DetalleRemisionInput]


class RemisionResponse(BaseModel):
    id: int
    folio: Optional[str] = None
    orden_venta_id: int
    fecha_remision: datetime
    transportista: Optional[str] = None
    recibido_por: Optional[str] = None
    recibido_at: Optional[datetime] = None
    observaciones: Optional[str] = None
    creado_en: datetime

    class Config:
        from_attributes = True
