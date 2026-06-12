"""
Schemas Pydantic v2 para Recordatorios de seguimiento.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RecordatorioCreate(BaseModel):
    """Payload del cliente para crear un recordatorio.

    usuario_id NO se acepta en el body: el backend lo deriva de
    orden.vendedor_id (o del usuario autenticado como fallback).

    orden_id es opcional: un recordatorio "libre" no está atado a una orden.
    cliente_id permite apuntar el follow-up a un cliente sin orden.
    """

    orden_id: Optional[int] = None
    cliente_id: Optional[int] = None
    fecha_proximo_contacto: datetime
    tipo_accion: str = "llamada"
    descripcion: Optional[str] = None


class RecordatorioPosponer(BaseModel):
    """Payload para posponer un recordatorio existente."""

    nueva_fecha: datetime


class RecordatorioOut(BaseModel):
    """Schema de salida enriquecido.

    Los endpoints devuelven dicts construidos manualmente para incluir
    campos derivados (folio, cliente, usuario_nombre, dias). Este schema
    documenta la forma esperada para Swagger/OpenAPI.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    orden_id: Optional[int] = None
    cliente_id: Optional[int] = None
    usuario_id: int
    fecha_proximo_contacto: datetime
    tipo_accion: str
    descripcion: Optional[str]
    estado: str
    creado_en: Optional[datetime]
    completado_en: Optional[datetime]

    # Campos enriquecidos (join en el endpoint)
    folio: Optional[str] = None
    cliente: Optional[str] = None
    usuario_nombre: Optional[str] = None
    dias: int = 0  # negativo=vencido, 0=hoy, positivo=futuro
