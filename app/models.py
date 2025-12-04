from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# --- USUARIOS (Sistema de Login y Permisos) ---
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    rol = Column(String, default="asistente") # 'admin', 'ventas', 'almacen'
    activo = Column(Boolean, default=True)

# --- INVENTARIO (Productos y Proveedores) ---
class Proveedor(Base):
    __tablename__ = "proveedores"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    productos = relationship("Producto", back_populates="proveedor")

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    numero_catalogo = Column(String, unique=True, index=True) # El ID principal de búsqueda
    descripcion = Column(Text)
    marca = Column(String, index=True, nullable=True) # Ej: Balluff, Festo
    
    # Costos y Monedas
    costo_proveedor = Column(Float, default=0.0) # Unit Price Prov
    moneda_compra = Column(String, default="USD") # USD o MXN
    tiempo_entrega = Column(String, nullable=True)
    
    # Inventario y Multimedia
    stock_actual = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=5) 
    ubicacion = Column(String, nullable=True) # Ej: Pasillo 3
    imagen_url = Column(String, nullable=True) # URL de la foto

    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    proveedor = relationship("Proveedor", back_populates="productos")

# --- CRM Y FINANZAS (Clientes y Cuentas por Cobrar) ---
class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    
    # Datos Principales
    compania = Column(String, index=True) # Razón Social / Empresa (¡Campo Agregado!)
    nombre = Column(String, index=True)   # Nombre del Contacto
    rfc = Column(String, nullable=True)
    
    # Contacto
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    direccion = Column(Text, nullable=True)
    
    # Finanzas (Crédito)
    dias_credito = Column(Integer, default=30)
    saldo_actual = Column(Float, default=0.0) # Cuánto deben actualmente
    
    movimientos = relationship("MovimientoCuenta", back_populates="cliente")
    cotizaciones = relationship("Cotizacion", back_populates="cliente")

class MovimientoCuenta(Base):
    """
    Libro Mayor por Cliente:
    Registra cuando se genera una deuda (Nota Remisión) y cuando pagan.
    """
    __tablename__ = "movimientos_cuenta"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    fecha = Column(DateTime, default=datetime.now)
    
    tipo = Column(String) # 'CARGO' (Deuda nueva) o 'ABONO' (Pago recibido)
    monto = Column(Float)
    referencia = Column(String) # Folio Cotización o # Transferencia
    descripcion = Column(String)
    
    cliente = relationship("Cliente", back_populates="movimientos")

# --- VENTAS (Cotizaciones) ---
class Cotizacion(Base):
    __tablename__ = "cotizaciones"
    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String, unique=True, index=True) # Ej: C-2512001
    
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    
    fecha = Column(DateTime, default=datetime.now)
    
    # Configuración Financiera del Documento
    moneda_salida = Column(String) # USD o MXN (Lo que ve el cliente)
    tipo_cambio_usado = Column(Float) # El TC fijado ese día
    total_neto = Column(Float)
    
    # Estados: 'Borrador', 'Finalizada', 'Entregada' (Deuda), 'Pagada', 'Cancelada'
    estado = Column(String, default="Borrador") 

    cliente = relationship("Cliente", back_populates="cotizaciones")
    detalles = relationship("CotizacionDetalle", back_populates="cotizacion")

class CotizacionDetalle(Base):
    __tablename__ = "cotizacion_detalles"
    id = Column(Integer, primary_key=True, index=True)
    cotizacion_id = Column(Integer, ForeignKey("cotizaciones.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=True)
    
    # Snapshot de datos (por si el producto cambia de precio después)
    cantidad = Column(Integer)
    descripcion_historica = Column(String) 
    
    # Cálculos Matemáticos Guardados
    costo_unitario_snapshot = Column(Float) # Costo real en ese momento
    margen_aplicado = Column(Float) # % de ganancia
    descuento_aplicado = Column(Float) # % descuento
    
    precio_venta_final = Column(Float) # Precio unitario final al cliente
    subtotal_linea = Column(Float) # precio * cantidad
    
    cotizacion = relationship("Cotizacion", back_populates="detalles")
    producto = relationship("Producto")