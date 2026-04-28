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
    folio = Column(String(40), unique=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_vencimiento = Column(DateTime, nullable=True)

    estatus = Column(Enum(EstatusOrden), default=EstatusOrden.COTIZACION)
    moneda = Column(String(3), nullable=False, default="MXN")
    tipo_cambio = Column(DECIMAL(12, 6), nullable=False, default=1.0)
    total = Column(DECIMAL(12, 2), default=0.00)
    observaciones = Column(Text, nullable=True)

    # Versionado de cotizaciones
    cotizacion_origen_id = Column(Integer, ForeignKey("ordenes_venta.id"), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)

    cliente = relationship("Cliente", back_populates="ordenes")
    vendedor = relationship("Usuario", back_populates="ventas")
    detalles = relationship(
        "DetalleOrden",
        back_populates="orden",
        cascade="all, delete-orphan",
    )
    versiones = relationship(
        "OrdenVenta",
        backref="cotizacion_origen",
        remote_side="OrdenVenta.id",
    )


class DetalleOrden(Base):
    __tablename__ = "detalles_orden"

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_venta.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=True)

    # Productos fantasma: si producto_id es null, usar estos campos
    sku_libre = Column(String(80), nullable=True)
    descripcion_libre = Column(String(255), nullable=True)
    moneda_origen_linea = Column(String(3), nullable=True)
    costo_base_linea = Column(DECIMAL(12, 2), nullable=True)

    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    utilidad_aplicada = Column(DECIMAL(10, 2), default=0.00)
    descuento_aplicado = Column(DECIMAL(10, 2), default=0.00)
    subtotal = Column(DECIMAL(12, 2), nullable=False)

    orden = relationship("OrdenVenta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_orden")
