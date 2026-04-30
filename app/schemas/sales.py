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
    producto_id: Optional[int] = None
    cantidad: int = Field(..., gt=0)
    utilidad: Decimal = Field(default=Decimal("0"), ge=0, lt=100)
    descuento: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    moneda_origen: Optional[str] = Field(default=None, min_length=3, max_length=3)
    # Productos fantasma / servicios
    sku_libre: Optional[str] = Field(default=None, max_length=80)
    descripcion_libre: Optional[str] = Field(default=None, max_length=255)
    costo_unitario: Optional[Decimal] = Field(default=None, ge=0)
    # Tipo de línea: producto_catalogo / producto_fantasma / servicio
    tipo_linea: Optional[str] = Field(default="producto_catalogo", max_length=20)
    proveedor_sugerido_id: Optional[int] = None


class DetalleOrdenResponse(BaseModel):
    producto: Optional[ProductoInfo] = None
    sku_libre: Optional[str] = None
    descripcion_libre: Optional[str] = None
    moneda_origen_linea: Optional[str] = None
    costo_base_linea: Optional[Decimal] = None
    cantidad: int
    precio_unitario: Decimal
    utilidad_aplicada: Decimal
    descuento_aplicado: Decimal
    subtotal: Decimal
    tipo_linea: Optional[str] = "producto_catalogo"
    proveedor_sugerido_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class OrdenVentaCreate(BaseModel):
    cliente_id: int
    detalles: List[DetalleOrdenCreate]
    observaciones: Optional[str] = None
    moneda: str = Field(default="MXN", min_length=3, max_length=3)
    tipo_cambio: Optional[Decimal] = Field(default=None, gt=0)


class OrdenVentaResponse(BaseModel):
    id: int
    folio: str
    fecha_creacion: datetime
    fecha_vencimiento: Optional[datetime] = None
    estatus: EstatusOrden
    moneda: str
    tipo_cambio: Decimal
    total: Decimal
    vendedor_id: int
    cliente: ClienteResponse
    detalles: List[DetalleOrdenResponse]
    version: int = 1
    cotizacion_origen_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
