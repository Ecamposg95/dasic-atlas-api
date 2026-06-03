from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, model_validator


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
    orden_venta_id: Optional[int] = None
    cliente_id: Optional[int] = None   # modo libre (sin orden)
    moneda: Optional[str] = None       # requerido en modo libre
    transportista: Optional[str] = None
    observaciones: Optional[str] = None
    mostrar_precios: bool = False
    detalles: List[DetalleRemisionInput]

    @model_validator(mode="after")
    def _exactly_one_origin(self):
        if bool(self.orden_venta_id) == bool(self.cliente_id):
            raise ValueError("Manda exactamente uno: orden_venta_id (desde orden) o cliente_id (libre)")
        return self


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
