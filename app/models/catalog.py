"""
Catalog models: Producto, Promocion.
"""

from sqlalchemy import Boolean, Column, DateTime, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    sku_comercial = Column(String(80), index=True, nullable=True)
    nombre = Column(String(150), index=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    imagen_url = Column(String(255), nullable=True)

    stock_actual = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=5)

    moneda_compra = Column(String(3), nullable=False, default="MXN")
    costo_compra = Column(DECIMAL(10, 2), default=0.00)
    precio_publico = Column(DECIMAL(10, 2), default=0.00)
    precio_mayorista = Column(DECIMAL(10, 2), default=0.00)
    precio_distribuidor = Column(DECIMAL(10, 2), default=0.00)

    promociones = relationship("Promocion", back_populates="producto")
    detalles_orden = relationship("DetalleOrden", back_populates="producto")
    detalles_compra = relationship("DetalleCompra", back_populates="producto")


class Promocion(Base):
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    nombre_promo = Column(String(100))
    descuento_porcentaje = Column(Integer)
    fecha_inicio = Column(DateTime)
    fecha_fin = Column(DateTime)
    activa = Column(Boolean, default=True)

    producto = relationship("Producto", back_populates="promociones")
