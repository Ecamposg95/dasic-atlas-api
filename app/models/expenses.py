"""Gastos operativos."""

from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String(80), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    monto = Column(DECIMAL(12, 2), nullable=False)
    moneda = Column(String(3), nullable=False, default="MXN")
    fecha = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    usuario = relationship("Usuario")
