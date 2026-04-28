"""
Sales models: OrdenVenta, DetalleOrden.
"""

from sqlalchemy import Column, DateTime, DECIMAL, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base
from app.models.enums import EstatusOrden


class OrdenVenta(Base):
    __tablename__ = "ordenes_venta"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    folio = Column(String(20), unique=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_vencimiento = Column(DateTime, nullable=True)

    estatus = Column(Enum(EstatusOrden), default=EstatusOrden.COTIZACION)
    moneda = Column(String(3), nullable=False, default="MXN")
    tipo_cambio = Column(DECIMAL(12, 6), nullable=False, default=1.0)
    total = Column(DECIMAL(12, 2), default=0.00)
    observaciones = Column(Text, nullable=True)

    cliente = relationship("Cliente", back_populates="ordenes")
    vendedor = relationship("Usuario", back_populates="ventas")
    detalles = relationship(
        "DetalleOrden",
        back_populates="orden",
        cascade="all, delete-orphan",
    )


class DetalleOrden(Base):
    __tablename__ = "detalles_orden"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_venta.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))

    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    utilidad_aplicada = Column(DECIMAL(10, 2), default=0.00)
    descuento_aplicado = Column(DECIMAL(10, 2), default=0.00)
    subtotal = Column(DECIMAL(12, 2), nullable=False)

    orden = relationship("OrdenVenta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_orden")
