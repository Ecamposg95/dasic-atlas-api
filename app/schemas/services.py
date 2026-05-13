"""Schemas Pydantic para el módulo Servicios."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServicioBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=30)
    nombre: str = Field(..., min_length=2, max_length=150)
    descripcion: Optional[str] = None
    categoria_servicio: Optional[str] = Field(None, max_length=40)
    costo: Decimal = Field(default=Decimal("0"), ge=0)
    moneda: str = Field("MXN", min_length=3, max_length=3)
    tiempo_estimado: Optional[Decimal] = Field(None, ge=0)
    unidad_tiempo: Optional[str] = Field(None, max_length=10)
    # SAT defaults se aplican en el modelo si vienen vacíos.
    clave_prod_serv: Optional[str] = Field(None, max_length=8)
    clave_unidad_sat: Optional[str] = Field(None, max_length=10)
    objeto_imp: Optional[str] = Field(None, max_length=2)
    descripcion_fiscal: Optional[str] = None
    activo: bool = True


class ServicioCreate(ServicioBase):
    pass


class ServicioUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=2, max_length=30)
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    descripcion: Optional[str] = None
    categoria_servicio: Optional[str] = Field(None, max_length=40)
    costo: Optional[Decimal] = Field(None, ge=0)
    moneda: Optional[str] = Field(None, min_length=3, max_length=3)
    tiempo_estimado: Optional[Decimal] = Field(None, ge=0)
    unidad_tiempo: Optional[str] = Field(None, max_length=10)
    clave_prod_serv: Optional[str] = Field(None, max_length=8)
    clave_unidad_sat: Optional[str] = Field(None, max_length=10)
    objeto_imp: Optional[str] = Field(None, max_length=2)
    descripcion_fiscal: Optional[str] = None
    activo: Optional[bool] = None


class ServicioResponse(ServicioBase):
    id: int
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
