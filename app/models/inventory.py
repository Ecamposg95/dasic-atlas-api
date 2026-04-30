"""Inventario: movimientos de stock auditables."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class MovimientoStock(Base):
    __tablename__ = "movimientos_stock"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)
    cantidad = Column(Integer, nullable=False)
    referencia_tipo = Column(String(20), nullable=True)
    referencia_id = Column(Integer, nullable=True, index=True)
    motivo = Column(Text, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    stock_resultante = Column(Integer, nullable=False)

    producto = relationship("Producto", back_populates="movimientos_stock")
    usuario = relationship("Usuario")
