"""
Finance schemas: TransaccionCliente, TransaccionProveedor.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import TipoMovimiento


class TransaccionCreate(BaseModel):
    entidad_id: int
    monto: Decimal = Field(..., gt=0)
    tipo: TipoMovimiento
    descripcion: str


class TransaccionResponse(BaseModel):
    id: int
    fecha: datetime
    monto: Decimal
    tipo: TipoMovimiento
    descripcion: str
    referencia_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
