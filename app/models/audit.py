"""Bitácora global de mutaciones sensibles (Ola 4 E5).

Sin FK en entidad_id: la entidad auditada puede ya no existir (deletes).
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    accion = Column(String(40), nullable=False)   # eliminar | cambio_precio | cambio_rol | desactivar | crear
    entidad = Column(String(40), nullable=False)  # cliente | contacto | producto | gasto | usuario
    entidad_id = Column(Integer, nullable=True)
    resumen = Column(String(400), nullable=False)
    datos = Column(Text, nullable=True)  # JSON: diff viejo→nuevo o snapshot del borrado

    usuario = relationship("Usuario", foreign_keys=[usuario_id])

    __table_args__ = (Index("ix_audit_log_entidad", "entidad", "entidad_id"),)
