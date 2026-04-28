"""
Quote events: bitácora unificada de envíos por correo, WhatsApp, IA.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class QuoteEvent(Base):
    __tablename__ = "quote_events"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), nullable=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_venta.id"), nullable=False, index=True)
    canal = Column(String(20), nullable=False)  # EMAIL | WHATSAPP | IA | NOTE
    direccion = Column(String(20), nullable=True)  # OUTBOUND | INBOUND | INTERNAL
    estatus = Column(String(20), nullable=True)  # SENT | FAILED | LOGGED | DRAFT
    asunto = Column(String(255), nullable=True)
    cuerpo = Column(Text, nullable=True)
    destinatario = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=True)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    orden = relationship("OrdenVenta", foreign_keys=[orden_id])
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
