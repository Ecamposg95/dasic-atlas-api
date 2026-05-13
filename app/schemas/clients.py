"""
Clients & Suppliers schemas: Cliente, Proveedor.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ClienteBase(BaseModel):
    nombre_empresa: str
    contacto_nombre: Optional[str] = None
    rfc_tax_id: Optional[str] = None
    email: Optional[str] = None  # EmailStr omitido para evitar error en Windows
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    # CRM crédito
    limite_credito: Optional[Decimal] = Decimal("0")
    dias_credito: Optional[int] = 0
    dia_corte: Optional[int] = None
    moneda_credito: Optional[str] = "MXN"


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nombre_empresa: Optional[str] = None
    contacto_nombre: Optional[str] = None
    rfc_tax_id: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    limite_credito: Optional[Decimal] = None
    dias_credito: Optional[int] = None
    dia_corte: Optional[int] = None
    moneda_credito: Optional[str] = None


class ClienteResponse(ClienteBase):
    id: int
    saldo_actual: Decimal
    creado_por_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class ProveedorBase(BaseModel):
    nombre_empresa: str
    contacto_nombre: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None  # EmailStr omitido para evitar error en Windows


class ProveedorCreate(ProveedorBase):
    pass


class ProveedorResponse(ProveedorBase):
    id: int
    saldo_actual: Decimal
    model_config = ConfigDict(from_attributes=True)
