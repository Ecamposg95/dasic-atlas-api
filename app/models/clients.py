"""
Clients models: Cliente, Proveedor.
"""

from sqlalchemy import Boolean, Column, DECIMAL, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre_empresa = Column(String(150), index=True)
    contacto_nombre = Column(String(100))
    rfc_tax_id = Column(String(50), nullable=True)
    email = Column(String(100))
    telefono = Column(String(20))
    direccion = Column(Text)

    saldo_actual = Column(DECIMAL(12, 2), default=0.00)
    # CRM: crédito y plazo
    limite_credito = Column(DECIMAL(12, 2), nullable=False, default=0)
    dias_credito = Column(Integer, nullable=False, default=0)
    dia_corte = Column(Integer, nullable=True)  # 1-28 si aplica
    moneda_credito = Column(String(3), nullable=False, default="MXN")

    creado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)

    ordenes = relationship("OrdenVenta", back_populates="cliente")
    transacciones = relationship("TransaccionCliente", back_populates="cliente")
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
    contactos = relationship("Contacto", back_populates="cliente", cascade="all, delete-orphan")


class Contacto(Base):
    """Persona de contacto de una empresa (cliente). Varias por empresa."""
    __tablename__ = "contactos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(120), nullable=False)
    cargo = Column(String(80), nullable=True)
    email = Column(String(120), nullable=True)
    telefono = Column(String(40), nullable=True)
    es_principal = Column(Boolean, nullable=False, server_default=text("false"))
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cliente = relationship("Cliente", back_populates="contactos")


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


class ClienteMergeLog(Base):
    """Auditoría de fusiones de empresas (Sub-3). Sin FK a clientes a propósito:
    el loser se borra; este log debe sobrevivir como respaldo recuperable."""
    __tablename__ = "cliente_merge_log"

    id = Column(Integer, primary_key=True, index=True)
    survivor_id = Column(Integer, index=True)
    loser_id = Column(Integer, index=True)
    loser_nombre = Column(String(150))
    loser_rfc = Column(String(50))
    loser_saldo = Column(DECIMAL(12, 2))
    n_ordenes = Column(Integer)
    n_transacciones = Column(Integer)
    n_remisiones = Column(Integer)
    n_contactos = Column(Integer)
    merged_by_id = Column(Integer)
    merged_at = Column(DateTime(timezone=True), server_default=func.now())
