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
    # Bloque editable de Condiciones Comerciales del PDF. Una línea = un <li>.
    # NULL → el PDF usa el bloque hardcoded como fallback (compat con
    # cotizaciones legacy creadas antes de esta feature).
    terminos_condiciones = Column(Text, nullable=True)

    # Versionado de cotizaciones
    cotizacion_origen_id = Column(Integer, ForeignKey("ordenes_venta.id"), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)

    # Lifecycle tracking — Fase Cotizador-Edicion (spec 2026-05-19)
    enviada_at = Column(DateTime(timezone=True), nullable=True, index=True)
    pdf_generado_at = Column(DateTime(timezone=True), nullable=True)
    actualizado_en = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

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
    # Vínculo con catálogo de servicios persistibles (Servicio).
    # Cuando es no-null, tipo_linea = 'servicio_catalogo'.
    servicio_id = Column(Integer, ForeignKey("servicios.id"), nullable=True, index=True)

    # Productos fantasma o servicios ad-hoc: si producto_id y servicio_id
    # son ambos NULL, usar estos campos.
    sku_libre = Column(String(80), nullable=True)
    # Text (no length cap): para productos fantasma / servicios ad-hoc el usuario
    # pega descripciones reales del fabricante que rebasan 255 chars con facilidad.
    descripcion_libre = Column(Text, nullable=True)
    moneda_origen_linea = Column(String(3), nullable=True)
    costo_base_linea = Column(DECIMAL(12, 2), nullable=True)

    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    utilidad_aplicada = Column(DECIMAL(10, 2), default=0.00)
    descuento_aplicado = Column(DECIMAL(10, 2), default=0.00)
    subtotal = Column(DECIMAL(12, 2), nullable=False)

    tipo_linea = Column(String(20), nullable=False, default="producto_catalogo")
    proveedor_sugerido_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    fantasma_id = Column(Integer, ForeignKey("productos_fantasma.id"), nullable=True, index=True)

    # Tiempos de entrega por línea (estructurado). Los 3 viajan juntos: o
    # vienen los 3 o ninguno. unidad ∈ {'dias','semanas','tespv'}. min <= max
    # cuando aplica (NULL para tespv). Defaults NULL — los captura el usuario.
    entrega_min = Column(Integer, nullable=True)
    entrega_max = Column(Integer, nullable=True)
    entrega_unidad = Column(String(10), nullable=True)

    # Nota libre por línea: el vendedor captura productos similares o
    # comentarios que se imprimen en el PDF bajo el nombre del producto.
    # Mientras el stock no esté bien definido para sugerir similares
    # automáticamente, esto reemplaza al motor de "productos relacionados".
    observaciones_linea = Column(Text, nullable=True)

    orden = relationship("OrdenVenta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_orden")
    servicio = relationship("Servicio", foreign_keys=[servicio_id])
    proveedor_sugerido = relationship("Proveedor", foreign_keys=[proveedor_sugerido_id])
