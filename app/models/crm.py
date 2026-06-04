"""
CRM Kanban models: Pipeline, PipelineStage, Deal.

Multi-tenant: cada tabla lleva organization_id (VARCHAR 36, indexado).
"""

from sqlalchemy import Boolean, Column, DateTime, DECIMAL, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), index=True)
    nombre = Column(String(120), nullable=False)
    es_default = Column(Boolean, default=False, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    stages = relationship(
        "PipelineStage",
        back_populates="pipeline",
        order_by="PipelineStage.orden",
        cascade="all, delete-orphan",
    )


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False, index=True)
    nombre = Column(String(80), nullable=False)
    orden = Column(Integer, default=0, nullable=False)
    color = Column(String(20), nullable=True)
    es_ganado = Column(Boolean, default=False, nullable=False)
    es_perdido = Column(Boolean, default=False, nullable=False)

    pipeline = relationship("Pipeline", back_populates="stages")
    deals = relationship("Deal", back_populates="stage")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("pipeline_stages.id"), nullable=False, index=True)
    titulo = Column(String(200), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    orden_id = Column(Integer, ForeignKey("ordenes_venta.id"), nullable=True)
    monto = Column(DECIMAL(14, 2), nullable=True)
    moneda = Column(String(3), default="MXN", nullable=False)
    owner_user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    orden_en_stage = Column(Integer, default=0, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    cerrado_en = Column(DateTime(timezone=True), nullable=True)

    pipeline = relationship("Pipeline")
    stage = relationship("PipelineStage", back_populates="deals")
    cliente = relationship("Cliente")
    orden = relationship("OrdenVenta")
    owner = relationship("Usuario")
