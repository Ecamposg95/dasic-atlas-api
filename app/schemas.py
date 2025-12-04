from pydantic import BaseModel
from typing import List, Optional

# --- Modelos para Cotización (Input) ---

class ItemCotizacionInput(BaseModel):
    numero_catalogo: str
    descripcion: str
    costo_proveedor: float
    moneda_compra: str
    nombre_proveedor: str
    tiempo_entrega: str = "1 Día"
    cantidad: int
    margen_ganancia: float
    descuento_cliente: float

class CotizacionCreate(BaseModel):
    cliente_id: Optional[int] = None
    nuevo_cliente_nombre: Optional[str] = None
    moneda_salida: str
    tipo_cambio: float
    items: List[ItemCotizacionInput]

class CotizacionResponse(BaseModel):
    folio: str
    pdf_url: str
    mensaje: str

# --- Modelos para Autenticación (Login) ---

class UserLogin(BaseModel):
    username: str
    password: str

# ¡ESTA ES LA CLASE QUE FALTABA!
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    
    
# En app/schemas.py

class ItemCotizacionInput(BaseModel):
    numero_catalogo: str
    descripcion: str
    costo_proveedor: float
    moneda_compra: str
    nombre_proveedor: str
    tiempo_entrega: str = "1 Día"
    cantidad: int
    margen_ganancia: float
    descuento_cliente: float
    
    # NUEVO CAMPO:
    imagen_url: Optional[str] = None
    
class ClienteCreate(BaseModel):
    nombre: str
    compania: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    rfc: Optional[str] = None
    dias_credito: int = 30

class ClienteResponse(ClienteCreate):
    id: int
    saldo_actual: float = 0.0
    
    class Config:
        from_attributes = True # Para leer desde SQLAlchemy
        
        
# --- app/schemas.py (Agregar al final) ---

class ProductoCreate(BaseModel):
    numero_catalogo: str
    descripcion: str
    marca: Optional[str] = "Generico"
    costo_proveedor: float = 0.0
    moneda_compra: str = "USD"
    tiempo_entrega: Optional[str] = "1 Semana"
    stock_actual: int = 0
    imagen_url: Optional[str] = None