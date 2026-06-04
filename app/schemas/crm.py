"""Schemas Pydantic para el módulo CRM Kanban."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PipelineOut(BaseModel):
    id: int
    organization_id: Optional[str] = None
    nombre: str
    es_default: bool
    creado_en: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class StageOut(BaseModel):
    id: int
    organization_id: Optional[str] = None
    pipeline_id: int
    nombre: str
    orden: int
    color: Optional[str] = None
    es_ganado: bool
    es_perdido: bool
    model_config = ConfigDict(from_attributes=True)


class DealOut(BaseModel):
    id: int
    organization_id: Optional[str] = None
    pipeline_id: int
    stage_id: int
    titulo: str
    cliente_id: Optional[int] = None
    orden_id: Optional[int] = None
    monto: Optional[Decimal] = None
    moneda: str
    owner_user_id: Optional[int] = None
    orden_en_stage: int
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    cerrado_en: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class DealCreate(BaseModel):
    pipeline_id: int
    titulo: str
    stage_id: Optional[int] = None
    cliente_id: Optional[int] = None
    orden_id: Optional[int] = None
    monto: Optional[Decimal] = None
    moneda: str = "MXN"
    owner_user_id: Optional[int] = None


class DealUpdate(BaseModel):
    titulo: Optional[str] = None
    stage_id: Optional[int] = None
    cliente_id: Optional[int] = None
    orden_id: Optional[int] = None
    monto: Optional[Decimal] = None
    moneda: Optional[str] = None
    owner_user_id: Optional[int] = None
    orden_en_stage: Optional[int] = None


class DealMove(BaseModel):
    stage_id: int
    orden_en_stage: Optional[int] = None
