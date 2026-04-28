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
    estatus = Column(String(20), default="borrador")
    folio = Column(String(40), unique=True, nullable=True, index=True)
    moneda = Column(String(3), nullable=False, default="MXN")
    tipo_cambio = Column(DECIMAL(12, 6), nullable=False, default=1.0)
    cotizacion_id = Column(Integer, ForeignKey("ordenes_venta.id"), nullable=True, index=True)

    proveedor = relationship("Proveedor", back_populates="compras")
    detalles = relationship(
        "DetalleCompra",
        back_populates="orden",
        cascade="all, delete-orphan",
    )
    cotizacion = relationship("OrdenVenta", foreign_keys=[cotizacion_id])


class DetalleCompra(Base):
    __tablename__ = "detalles_compra"

    id = Column(Integer, primary_key=True, index=True)
    orden_compra_id = Column(Integer, ForeignKey("ordenes_compra.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))

    cantidad = Column(Integer, nullable=False)
    costo_unitario = Column(DECIMAL(10, 2), nullable=False)

    orden = relationship("OrdenCompra", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_compra")
