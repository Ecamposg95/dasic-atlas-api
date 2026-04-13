"""
Finance models: TransaccionCliente, TransaccionProveedor.
"""

from sqlalchemy import Column, DateTime, DECIMAL, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base
from app.models.enums import TipoMovimiento


class TransaccionCliente(Base):
    __tablename__ = "transacciones_clientes"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    tipo = Column(Enum(TipoMovimiento))
    monto = Column(DECIMAL(12, 2), nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    descripcion = Column(String(200))
    referencia_id = Column(Integer, nullable=True)

    cliente = relationship("Cliente", back_populates="transacciones")


class TransaccionProveedor(Base):
    __tablename__ = "transacciones_proveedores"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    tipo = Column(Enum(TipoMovimiento))
    monto = Column(DECIMAL(12, 2), nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    descripcion = Column(String(200))

    proveedor = relationship("Proveedor", back_populates="transacciones")
