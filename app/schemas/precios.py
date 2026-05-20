from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PrecioProveedorCreate(BaseModel):
    proveedor_id: int
    producto_id: Optional[int] = None
    descripcion_busqueda: Optional[str] = None
    sku_libre: Optional[str] = None
    precio: Decimal
    moneda: str = "MXN"
    fecha_vigencia_desde: Optional[date] = None
    fecha_vigencia_hasta: Optional[date] = None
    notas: Optional[str] = None


class PrecioProveedorResponse(BaseModel):
    id: int
    proveedor_id: int
    proveedor_nombre: Optional[str] = None
    producto_id: Optional[int] = None
    producto_nombre: Optional[str] = None
    descripcion_busqueda: Optional[str] = None
    sku_libre: Optional[str] = None
    precio: Decimal
    moneda: str
    fecha_vigencia_desde: date
    fecha_vigencia_hasta: Optional[date] = None
    notas: Optional[str] = None
    fuente: str
    creado_en: datetime

    class Config:
        from_attributes = True
