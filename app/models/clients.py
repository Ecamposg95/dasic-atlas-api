"""
Clients models: Cliente, Proveedor.
"""

from sqlalchemy import Column, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    nombre_empresa = Column(String(150), index=True)
    contacto_nombre = Column(String(100))
    rfc_tax_id = Column(String(50), nullable=True)
    email = Column(String(100))
    telefono = Column(String(20))
    direccion = Column(Text)

    saldo_actual = Column(DECIMAL(12, 2), default=0.00)

    ordenes = relationship("OrdenVenta", back_populates="cliente")
    transacciones = relationship("TransaccionCliente", back_populates="cliente")


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre_empresa = Column(String(150), index=True)
    contacto_nombre = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(100))

    saldo_actual = Column(DECIMAL(12, 2), default=0.00)

    compras = relationship("OrdenCompra", back_populates="proveedor")
    transacciones = relationship("TransaccionProveedor", back_populates="proveedor")
