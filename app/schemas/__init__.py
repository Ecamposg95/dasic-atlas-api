from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.models import RolUsuario, EstatusOrden, TipoMovimiento

# NOTA: Hemos cambiado EmailStr por str para evitar el error de documentación en Windows

# --- AUTH & USUARIOS ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    rol: Optional[RolUsuario] = None
    org_id: Optional[str] = None
    branch_id: Optional[str] = None

class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: str # Cambiado de EmailStr a str
    rol: RolUsuario = RolUsuario.VENDEDOR
    activo: bool = True

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, description="Mínimo 6 caracteres")

class UsuarioResponse(UsuarioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    username: str
    password: str

# --- PRODUCTOS ---
class ProductoBase(BaseModel):
    sku: str = Field(..., min_length=2, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=150)
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    stock_minimo: int = Field(5, ge=0)
    precio_publico: Decimal = Field(..., ge=0)
    precio_mayorista: Decimal = Field(..., ge=0)
    precio_distribuidor: Decimal = Field(..., ge=0)

class ProductoCreate(ProductoBase):
    stock_actual: int = Field(0, ge=0)
    costo_compra: Decimal = Field(..., ge=0)

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    precio_publico: Optional[Decimal] = Field(None, ge=0)
    costo_compra: Optional[Decimal] = Field(None, ge=0)
    stock_actual: Optional[int] = Field(None, ge=0)

class ProductoResponseVendedor(ProductoBase):
    id: int
    stock_actual: int
    model_config = ConfigDict(from_attributes=True)

class ProductoResponseAdmin(ProductoBase):
    id: int
    stock_actual: int
    costo_compra: Decimal
    model_config = ConfigDict(from_attributes=True)

# --- SCHEMA MINI PARA DETALLES ---
class ProductoInfo(BaseModel):
    id: int
    sku: str
    nombre: str
    model_config = ConfigDict(from_attributes=True)

# --- PROMOCIONES ---
class PromocionBase(BaseModel):
    nombre_promo: str
    descuento_porcentaje: int = Field(..., gt=0, le=100)
    fecha_inicio: datetime
    fecha_fin: datetime
    activa: bool = True

class PromocionCreate(PromocionBase):
    producto_id: int

class PromocionResponse(PromocionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- TERCEROS ---
class ClienteBase(BaseModel):
    nombre_empresa: str
    contacto_nombre: str
    rfc_tax_id: Optional[str] = None
    email: str # Cambiado de EmailStr a str
    telefono: str
    direccion: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteResponse(ClienteBase):
    id: int
    saldo_actual: Decimal
    model_config = ConfigDict(from_attributes=True)

class ProveedorBase(BaseModel):
    nombre_empresa: str
    contacto_nombre: str
    telefono: str
    email: str # Cambiado de EmailStr a str

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorResponse(ProveedorBase):
    id: int
    saldo_actual: Decimal
    model_config = ConfigDict(from_attributes=True)

# --- TRANSACCIONES ---
class TransaccionCreate(BaseModel):
    entidad_id: int 
    monto: Decimal = Field(..., gt=0)
    tipo: TipoMovimiento
    descripcion: str

class TransaccionResponse(BaseModel):
    id: int
    fecha: datetime
    monto: Decimal
    tipo: TipoMovimiento
    descripcion: str
    referencia_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)

# --- VENTAS Y DETALLES ---
class DetalleOrdenCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)
    descuento: float = 0

class DetalleOrdenResponse(BaseModel):
    producto: ProductoInfo 
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    model_config = ConfigDict(from_attributes=True)

class OrdenVentaCreate(BaseModel):
    cliente_id: int
    detalles: List[DetalleOrdenCreate]
    observaciones: Optional[str] = None

class OrdenVentaResponse(BaseModel):
    id: int
    folio: str
    fecha_creacion: datetime
    estatus: EstatusOrden
    total: Decimal
    vendedor_id: int
    cliente: ClienteResponse 
    detalles: List[DetalleOrdenResponse]
    model_config = ConfigDict(from_attributes=True)
