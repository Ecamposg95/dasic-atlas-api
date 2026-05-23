"""ReporteServicio — acta de servicio ejecutado.

Documento "hijo" de una OrdenVenta análogo a Remision pero para líneas de
tipo `servicio_catalogo`. Cada cotización convertida a venta puede generar
1+ Reportes de Servicio (uno por intervención del técnico).

NO confundir con `/spa/reportes-servicio` (dashboard analítico). El
documento se sirve bajo el prefix `/api/reportes-servicio-docs` y la feature
SPA vive en `web/src/features/reportes_servicio_docs/`.
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class ReporteServicio(Base):
    __tablename__ = "reportes_servicio"

    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String(40), unique=True, index=True, nullable=True)
    orden_venta_id = Column(Integer, ForeignKey("ordenes_venta.id"), nullable=False, index=True)
    fecha_reporte = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    tecnico_nombre = Column(String(150), nullable=True)
    cliente_recibe_nombre = Column(String(150), nullable=True)
    recibido_at = Column(DateTime(timezone=True), nullable=True)
    observaciones = Column(Text, nullable=True)
    creado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    orden_venta = relationship("OrdenVenta", foreign_keys=[orden_venta_id])
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
