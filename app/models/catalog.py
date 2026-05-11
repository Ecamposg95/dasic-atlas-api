"""
Catalog models: Producto, Promocion, Marca.
"""

from sqlalchemy import Boolean, Column, DateTime, DECIMAL, ForeignKey, Integer, String, Text, false
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Marca(Base):
    """Taxonomía de marcas para SKU interno y agrupación de catálogo.

    La abreviatura se usa como prefijo del SKU interno: {ABREV}-{NNNN}.
    Se seedea inicialmente desde app/data/marca_abreviaturas.json, pero
    la tabla es la fuente de verdad runtime (CRUD vía /api/catalogos).
    """

    __tablename__ = "marcas"

    id = Column(Integer, primary_key=True, index=True)
    abreviatura = Column(String(20), unique=True, index=True, nullable=False)
    nombre = Column(String(150), nullable=False)
    categoria = Column(String(150), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    sku_comercial = Column(String(80), index=True, nullable=True)
    nombre = Column(String(150), index=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    imagen_url = Column(String(255), nullable=True)
    marca = Column(String(80), index=True, nullable=True)
    unidad = Column(String(20), nullable=True, default="PZA")

    proveedor_principal_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True, index=True)
    proveedor_alterno_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    tiempo_entrega_dias = Column(Integer, nullable=False, default=7)
    es_servicio = Column(Boolean, nullable=False, default=False)

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
    proveedor_principal = relationship("Proveedor", foreign_keys=[proveedor_principal_id])
    proveedor_alterno = relationship("Proveedor", foreign_keys=[proveedor_alterno_id])
    # passive_deletes=True: la DB tiene ON DELETE RESTRICT sobre
    # movimientos_stock.producto_id (migración 20260512_02). El ORM no debe
    # cascadear borrados; el kardex es inmutable. Borrar un producto con
    # historial debe fallar en la DB y en el endpoint con 409.
    movimientos_stock = relationship(
        "MovimientoStock", back_populates="producto", passive_deletes=True
    )


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
