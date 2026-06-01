"""ProductoFantasma — pool de productos ad-hoc apilados desde cotizaciones."""

from sqlalchemy import Column, DateTime, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class ProductoFantasma(Base):
    __tablename__ = "productos_fantasma"

    id = Column(Integer, primary_key=True, index=True)
    descripcion_normalizada = Column(String(500), nullable=False, index=True)
    descripcion_original = Column(Text, nullable=False)
    sku_libre = Column(String(80), nullable=True, index=True)
    # Homologación con Producto (US-007/008): marca (texto + FK), claves SAT y notas.
    marca = Column(String(80), nullable=True)
    marca_id = Column(Integer, ForeignKey("marcas.id", ondelete="SET NULL"), nullable=True, index=True)
    clave_prod_serv = Column(String(8), nullable=True)
    clave_unidad_sat = Column(String(10), nullable=True)
    observaciones = Column(Text, nullable=True)
    costo_referencia = Column(DECIMAL(12, 2), nullable=False)
    moneda_referencia = Column(String(3), nullable=False, default="MXN")
    proveedor_sugerido_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    estado = Column(String(20), nullable=False, default="PENDIENTE", index=True)
    promovido_a_producto_id = Column(Integer, ForeignKey("productos.id"), nullable=True)
    veces_solicitado = Column(Integer, nullable=False, default=1)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ultimo_visto_en = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    proveedor_sugerido = relationship("Proveedor", foreign_keys=[proveedor_sugerido_id])
    promovido_a = relationship("Producto", foreign_keys=[promovido_a_producto_id])
    marca_rel = relationship("Marca", foreign_keys=[marca_id])
