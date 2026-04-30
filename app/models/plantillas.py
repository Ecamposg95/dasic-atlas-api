"""Plantillas / kits reutilizables para el cotizador."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class PlantillaCotizacion(Base):
    """Combinación de líneas frecuente que un usuario puede recargar.

    `lineas` es JSON serializado en TEXT (postgres acepta cualquier string;
    no usamos JSONB para no requerir migración compleja). Cada línea tiene
    el mismo shape que DetalleOrdenCreate (producto_id, cantidad, utilidad,
    moneda_origen, sku_libre, descripcion_libre, costo_unitario, tipo_linea,
    proveedor_sugerido_id).
    """
    __tablename__ = "plantillas_cotizacion"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(Text, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    lineas = Column(Text, nullable=False, default="[]")  # JSON string
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuario")
