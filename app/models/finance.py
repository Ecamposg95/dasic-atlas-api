"""
Finance models: TransaccionCliente, TransaccionProveedor.
"""

from sqlalchemy import Column, Date, DateTime, DECIMAL, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base
from app.models.enums import TipoMovimiento, TolerantEnum


class TransaccionCliente(Base):
    __tablename__ = "transacciones_clientes"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    tipo = Column(TolerantEnum(TipoMovimiento))
    monto = Column(DECIMAL(12, 2), nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    descripcion = Column(String(200))
    referencia_id = Column(Integer, nullable=True)
    # CxC formal (FASE 6): vínculo explícito con la venta que origina el cargo.
    # referencia_id se mantiene para compatibilidad con filas legacy.
    orden_venta_id = Column(Integer, ForeignKey("ordenes_venta.id"), nullable=True, index=True)
    fecha_vencimiento = Column(Date, nullable=True)
    # 'pendiente' | 'parcial' | 'pagado' | 'vencido'
    estatus_pago = Column(String(20), nullable=False, default="pendiente", index=True)
    monto_pagado = Column(DECIMAL(12, 2), nullable=False, default=0)

    cliente = relationship("Cliente", back_populates="transacciones")
    orden_venta = relationship("OrdenVenta", foreign_keys=[orden_venta_id])


class TransaccionProveedor(Base):
    __tablename__ = "transacciones_proveedores"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    tipo = Column(TolerantEnum(TipoMovimiento))
    monto = Column(DECIMAL(12, 2), nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    descripcion = Column(String(200))

    proveedor = relationship("Proveedor", back_populates="transacciones")
