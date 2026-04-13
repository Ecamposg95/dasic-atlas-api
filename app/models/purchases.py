"""
Purchases models: OrdenCompra, DetalleCompra.
"""

from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class OrdenCompra(Base):
    __tablename__ = "ordenes_compra"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    total = Column(DECIMAL(12, 2))
    estatus = Column(String(20), default="recibido")

    proveedor = relationship("Proveedor", back_populates="compras")
    detalles = relationship(
        "DetalleCompra",
        back_populates="orden",
        cascade="all, delete-orphan",
    )


class DetalleCompra(Base):
    __tablename__ = "detalles_compra"

    id = Column(Integer, primary_key=True, index=True)
    orden_compra_id = Column(Integer, ForeignKey("ordenes_compra.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))

    cantidad = Column(Integer, nullable=False)
    costo_unitario = Column(DECIMAL(10, 2), nullable=False)

    orden = relationship("OrdenCompra", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_compra")
