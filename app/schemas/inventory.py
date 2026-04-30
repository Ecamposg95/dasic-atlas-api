"""Inventory schemas: movimientos de stock + ajuste manual + disponibilidad."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MovimientoStockResponse(BaseModel):
    id: int
    producto_id: int
    tipo: str
    cantidad: int
    referencia_tipo: Optional[str] = None
    referencia_id: Optional[int] = None
    motivo: Optional[str] = None
    creado_en: datetime
    stock_resultante: int
    model_config = ConfigDict(from_attributes=True)


class AjusteManualIn(BaseModel):
    producto_id: int
    cantidad: int = Field(..., description="Signed: positivo entrada, negativo salida")
    motivo: str = Field(..., min_length=3, max_length=500)


class DisponibilidadResponse(BaseModel):
    producto_id: int
    stock_actual: int
    reservado: int
    disponible: int
    en_oc_pendiente: int
