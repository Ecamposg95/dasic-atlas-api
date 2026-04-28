"""
Catalog schemas: Producto, Promocion.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ProductoBase(BaseModel):
    sku: str = Field(..., min_length=2, max_length=50)
    sku_comercial: Optional[str] = Field(None, min_length=2, max_length=80)
    nombre: str = Field(..., min_length=2, max_length=150)
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    stock_minimo: int = Field(5, ge=0)
    moneda_compra: str = Field("MXN", min_length=3, max_length=3)
    precio_publico: Optional[Decimal] = Field(None, ge=0)
    precio_mayorista: Decimal = Field(default=Decimal("0"), ge=0)
    precio_distribuidor: Decimal = Field(default=Decimal("0"), ge=0)


class ProductoCreate(ProductoBase):
    stock_actual: int = Field(0, ge=0)
    costo_compra: Decimal = Field(..., ge=0)


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    sku_comercial: Optional[str] = Field(None, min_length=2, max_length=80)
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    moneda_compra: Optional[str] = Field(None, min_length=3, max_length=3)
    precio_publico: Optional[Decimal] = Field(None, ge=0)
    precio_mayorista: Optional[Decimal] = Field(None, ge=0)
    precio_distribuidor: Optional[Decimal] = Field(None, ge=0)
    costo_compra: Optional[Decimal] = Field(None, ge=0)
    stock_minimo: Optional[int] = Field(None, ge=0)
    stock_actual: Optional[int] = Field(None, ge=0)


class ProductoResponseVendedor(ProductoBase):
    id: int
    stock_actual: int
    model_config = ConfigDict(from_attributes=True)


class ProductoResponseAdmin(ProductoBase):
    id: int
    stock_actual: int
    costo_compra: Decimal
    model_config = ConfigDict(from_attributes=True)


class ProductoInfo(BaseModel):
    """Schema mini para referencias en detalles de orden."""
    id: int
    sku: str
    nombre: str
    model_config = ConfigDict(from_attributes=True)


class PromocionBase(BaseModel):
    nombre_promo: str
    descuento_porcentaje: int = Field(..., gt=0, le=100)
    fecha_inicio: datetime
    fecha_fin: datetime
    activa: bool = True


class PromocionCreate(PromocionBase):
    producto_id: int


class PromocionResponse(PromocionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
