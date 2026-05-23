"""Schemas Pydantic para ReporteServicio (documento hijo de OrdenVenta)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ReporteServicioCreate(BaseModel):
    orden_venta_id: int
    tecnico_nombre: Optional[str] = None
    cliente_recibe_nombre: Optional[str] = None
    observaciones: Optional[str] = None


class ReporteServicioResponse(BaseModel):
    id: int
    folio: Optional[str] = None
    orden_venta_id: int
    fecha_reporte: datetime
    tecnico_nombre: Optional[str] = None
    cliente_recibe_nombre: Optional[str] = None
    recibido_at: Optional[datetime] = None
    observaciones: Optional[str] = None
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)
