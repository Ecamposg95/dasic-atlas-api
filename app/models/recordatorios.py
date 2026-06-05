"""
Recordatorios de seguimiento — tareas FUTURAS asociadas a una cotización/orden.

Distinto de QuoteEvent (bitácora histórica): un Recordatorio es algo pendiente
por hacer. Mono-tenant: no lleva organization_id.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Recordatorio(Base):
    __tablename__ = "recordatorios"

    id = Column(Integer, primary_key=True, index=True)

    orden_id = Column(
        Integer,
        ForeignKey("ordenes_venta.id"),
        nullable=False,
        index=True,
    )
    # Responsable / asignado (por default = vendedor de la orden)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )

    fecha_proximo_contacto = Column(DateTime(timezone=True), nullable=False, index=True)

    # llamada | email | whatsapp | visita | otro
    tipo_accion = Column(String(20), nullable=False, default="llamada")

    descripcion = Column(Text, nullable=True)

    # pendiente | completado | pospuesto
    estado = Column(String(20), nullable=False, default="pendiente")

    creado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    completado_en = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    orden = relationship("OrdenVenta", foreign_keys=[orden_id])
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
