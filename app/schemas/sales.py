"""
Sales schemas: OrdenVenta, DetalleOrden.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import EstatusOrden
from app.schemas.clients import ClienteResponse
from app.schemas.catalog import ProductoInfo


class DetalleOrdenCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)
    descuento: float = 0


class DetalleOrdenResponse(BaseModel):
    producto: ProductoInfo
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    model_config = ConfigDict(from_attributes=True)


class OrdenVentaCreate(BaseModel):
    cliente_id: int
    detalles: List[DetalleOrdenCreate]
    observaciones: Optional[str] = None


class OrdenVentaResponse(BaseModel):
    id: int
    folio: str
    fecha_creacion: datetime
    estatus: EstatusOrden
    total: Decimal
    vendedor_id: int
    cliente: ClienteResponse
    detalles: List[DetalleOrdenResponse]
    model_config = ConfigDict(from_attributes=True)
