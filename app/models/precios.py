"""PrecioProveedor — registro de precios histórico/actual por proveedor."""

from sqlalchemy import Column, Date, DateTime, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class PrecioProveedor(Base):
    __tablename__ = "precios_proveedor"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=False, index=True)
    # Vincular a un producto del catálogo cuando exista. Si es un ítem ad-hoc
    # (fantasma), se usa descripcion_busqueda.
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=True, index=True)
    descripcion_busqueda = Column(String(500), nullable=True, index=True)
    sku_libre = Column(String(80), nullable=True, index=True)
    precio = Column(DECIMAL(12, 2), nullable=False)
    moneda = Column(String(3), nullable=False, default="MXN")
    fecha_vigencia_desde = Column(Date, nullable=False, server_default=func.current_date())
    fecha_vigencia_hasta = Column(Date, nullable=True)
    notas = Column(Text, nullable=True)
    fuente = Column(String(20), nullable=False, default="MANUAL")
    # MANUAL | OC | IMPORT
    referencia_oc_id = Column(Integer, ForeignKey("ordenes_compra.id"), nullable=True)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    proveedor = relationship("Proveedor", foreign_keys=[proveedor_id])
    producto = relationship("Producto", foreign_keys=[producto_id])
