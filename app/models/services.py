"""Catálogo de servicios reutilizables (distintos de productos).

Un servicio (mano de obra, instalación, asesoría, mantto) se puede agregar
a una cotización como línea independiente. Cuando se requieren materiales,
se agregan en líneas adicionales como productos del catálogo.

SAT default 81111500 (servicios profesionales) y unidad E48 (unidad de
servicio); ambos editables por servicio.
"""

import enum

from sqlalchemy import (
    Boolean, Column, DateTime, DECIMAL, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class CategoriaServicio(str, enum.Enum):
    INSTALACION = "instalacion"
    MANTTO = "mantto"
    ASESORIA = "asesoria"
    OTRO = "otro"


class UnidadTiempoServicio(str, enum.Enum):
    HORAS = "horas"
    DIAS = "dias"


SERVICIO_SAT_DEFAULT_PROD_SERV = "81111500"
SERVICIO_SAT_DEFAULT_UNIDAD = "E48"
SERVICIO_SAT_DEFAULT_OBJETO_IMP = "02"


class Servicio(Base):
    __tablename__ = "servicios"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), nullable=True, index=True)
    codigo = Column(String(30), nullable=False)
    nombre = Column(String(150), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    categoria_servicio = Column(String(40), nullable=True, index=True)

    costo = Column(DECIMAL(12, 2), nullable=False, default=0)
    moneda = Column(String(3), nullable=False, default="MXN")
    tiempo_estimado = Column(DECIMAL(8, 2), nullable=True)
    unidad_tiempo = Column(String(10), nullable=True)  # 'horas' | 'dias'

    # SAT (defaults para servicios profesionales)
    clave_prod_serv = Column(String(8), nullable=False, default=SERVICIO_SAT_DEFAULT_PROD_SERV)
    clave_unidad_sat = Column(String(10), nullable=False, default=SERVICIO_SAT_DEFAULT_UNIDAD)
    objeto_imp = Column(String(2), nullable=True, default=SERVICIO_SAT_DEFAULT_OBJETO_IMP)
    descripcion_fiscal = Column(Text, nullable=True)

    activo = Column(Boolean, nullable=False, default=True, index=True)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
