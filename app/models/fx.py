"""Tipos de cambio cacheados por día."""

from sqlalchemy import Column, Date, DateTime, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.db import Base


class TipoCambioDia(Base):
    __tablename__ = "tipos_cambio_dia"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, unique=True, index=True)
    usd_mxn = Column(DECIMAL(12, 6), nullable=False)
    fuente = Column(String(20), nullable=False)
    obtenido_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    nota = Column(Text, nullable=True)
    actualizado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
