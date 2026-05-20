"""Remision y DetalleRemision — comprobantes de entrega física."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Remision(Base):
    __tablename__ = "remisiones"

    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String(40), unique=True, index=True)
    orden_venta_id = Column(Integer, ForeignKey("ordenes_venta.id"), nullable=False, index=True)
    fecha_remision = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    transportista = Column(String(150), nullable=True)
    recibido_por = Column(String(150), nullable=True)
    recibido_at = Column(DateTime(timezone=True), nullable=True)
    observaciones = Column(Text, nullable=True)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    orden_venta = relationship("OrdenVenta", foreign_keys=[orden_venta_id])
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
    detalles = relationship("DetalleRemision", back_populates="remision", cascade="all, delete-orphan")


class DetalleRemision(Base):
    __tablename__ = "detalles_remision"

    id = Column(Integer, primary_key=True, index=True)
    remision_id = Column(Integer, ForeignKey("remisiones.id"), nullable=False, index=True)
    detalle_orden_id = Column(Integer, ForeignKey("detalles_orden.id"), nullable=True)
    descripcion = Column(Text, nullable=False)
    sku = Column(String(80), nullable=True)
    cantidad = Column(Integer, nullable=False)
    observaciones_linea = Column(Text, nullable=True)

    remision = relationship("Remision", back_populates="detalles")
