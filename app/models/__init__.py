"""ORM models.

Currently kept in a single module for compatibility.
Later we can split by domain (users/catalog/sales/finance/etc).
"""

from sqlalchemy import Boolean, Column, DateTime, DECIMAL, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

import enum

from app.db import Base


# --- ENUMS PARA CONTROL ESTRICTO ---
class RolUsuario(str, enum.Enum):
    ADMIN = "admin"
    ASISTENTE = "asistente"
    VENDEDOR = "vendedor"


class EstatusOrden(str, enum.Enum):
    COTIZACION = "cotizacion"
    PENDIENTE = "pendiente"
    PAGADA = "pagada"
    CANCELADA = "cancelada"


class TipoMovimiento(str, enum.Enum):
    CARGO = "cargo"
    ABONO = "abono"


# --- USUARIOS ---
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    rol = Column(Enum(RolUsuario), default=RolUsuario.VENDEDOR)
    activo = Column(Boolean, default=True)

    ventas = relationship("OrdenVenta", back_populates="vendedor")


# --- PRODUCTOS E INVENTARIO ---
class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    nombre = Column(String(150), index=True, nullable=False)
    descripcion = Column(Text, nullable=True)
    imagen_url = Column(String(255), nullable=True)

    stock_actual = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=5)

    costo_compra = Column(DECIMAL(10, 2), default=0.00)
    precio_publico = Column(DECIMAL(10, 2), default=0.00)
    precio_mayorista = Column(DECIMAL(10, 2), default=0.00)
    precio_distribuidor = Column(DECIMAL(10, 2), default=0.00)

    promociones = relationship("Promocion", back_populates="producto")
    detalles_orden = relationship("DetalleOrden", back_populates="producto")
    detalles_compra = relationship("DetalleCompra", back_populates="producto")


class Promocion(Base):
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"))
    nombre_promo = Column(String(100))
    descuento_porcentaje = Column(Integer)
    fecha_inicio = Column(DateTime)
    fecha_fin = Column(DateTime)
    activa = Column(Boolean, default=True)

    producto = relationship("Producto", back_populates="promociones")


# --- TERCEROS ---
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


# --- FINANZAS ---
class TransaccionCliente(Base):
    __tablename__ = "transacciones_clientes"

    id = Column(Integer, primary_key=True, index=True)
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


# --- VENTAS ---
class OrdenVenta(Base):
    __tablename__ = "ordenes_venta"

    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String(20), unique=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    vendedor_id = Column(Integer, ForeignKey("usuarios.id"))
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_vencimiento = Column(DateTime, nullable=True)

    estatus = Column(Enum(EstatusOrden), default=EstatusOrden.COTIZACION)
    total = Column(DECIMAL(12, 2), default=0.00)
    observaciones = Column(Text, nullable=True)

    cliente = relationship("Cliente", back_populates="ordenes")
    vendedor = relationship("Usuario", back_populates="ventas")
    detalles = relationship(
        "DetalleOrden",
        back_populates="orden",
        cascade="all, delete-orphan",
    )


class DetalleOrden(Base):
    __tablename__ = "detalles_orden"

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_venta.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))

    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    descuento_aplicado = Column(DECIMAL(10, 2), default=0.00)
    subtotal = Column(DECIMAL(12, 2), nullable=False)

    orden = relationship("OrdenVenta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_orden")


# --- COMPRAS ---
class OrdenCompra(Base):
    __tablename__ = "ordenes_compra"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    total = Column(DECIMAL(12, 2))
    estatus = Column(String(20), default="recibido")

    proveedor = relationship("Proveedor", back_populates="compras")
    detalles = relationship(
        "DetalleCompra",
        back_populates="orden",
        cascade="all, delete-orphan",
    )


class DetalleCompra(Base):
    __tablename__ = "detalles_compra"

    id = Column(Integer, primary_key=True, index=True)
    orden_compra_id = Column(Integer, ForeignKey("ordenes_compra.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))

    cantidad = Column(Integer, nullable=False)
    costo_unitario = Column(DECIMAL(10, 2), nullable=False)

    orden = relationship("OrdenCompra", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_compra")
