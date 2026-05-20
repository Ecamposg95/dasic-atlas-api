from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DetalleRemisionInput(BaseModel):
    detalle_orden_id: Optional[int] = None
    descripcion: str
    sku: Optional[str] = None
    cantidad: int
    observaciones_linea: Optional[str] = None


class RemisionCreate(BaseModel):
    orden_venta_id: int
    transportista: Optional[str] = None
    observaciones: Optional[str] = None
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
