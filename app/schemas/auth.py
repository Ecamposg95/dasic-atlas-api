"""
Auth & User schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import RolUsuario


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    rol: Optional[RolUsuario] = None
    org_id: Optional[str] = None
    branch_id: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: str  # EmailStr omitido para evitar error en Windows
    rol: RolUsuario = RolUsuario.VENDEDOR
    activo: bool = True


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, description="Mínimo 6 caracteres")


class UsuarioResponse(UsuarioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
