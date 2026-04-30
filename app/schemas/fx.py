"""Tipo de cambio schemas."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TipoCambioDiaResponse(BaseModel):
    fecha: date
    usd_mxn: Decimal
    fuente: str
    obtenido_en: datetime
    model_config = ConfigDict(from_attributes=True)
