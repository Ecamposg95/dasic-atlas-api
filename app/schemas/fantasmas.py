from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ProductoFantasmaBase(BaseModel):
    descripcion_original: str
    sku_libre: Optional[str] = None
    costo_referencia: Decimal
    moneda_referencia: str = "MXN"
    proveedor_sugerido_id: Optional[int] = None


class ProductoFantasmaResponse(ProductoFantasmaBase):
    id: int
    descripcion_normalizada: str
    estado: str
    promovido_a_producto_id: Optional[int] = None
    veces_solicitado: int
    creado_en: datetime
    ultimo_visto_en: datetime

    class Config:
        from_attributes = True


class ProductoFantasmaUpdate(BaseModel):
    descripcion_original: Optional[str] = None
    sku_libre: Optional[str] = None
    costo_referencia: Optional[Decimal] = None
    moneda_referencia: Optional[str] = None
    proveedor_sugerido_id: Optional[int] = None
