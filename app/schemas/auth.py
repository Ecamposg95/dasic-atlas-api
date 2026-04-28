"""
Auth & User schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_serializer, field_validator

from app.models.enums import RolUsuario


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    rol: Optional[RolUsuario] = None

    @field_validator("rol", mode="before")
    @classmethod
    def normalize_role(cls, value: RolUsuario | str | None) -> RolUsuario | None:
        if value is None:
            return None
        return RolUsuario.from_input(value)


class LoginRequest(BaseModel):
    username: str
    password: str


class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: str  # EmailStr omitido para evitar error en Windows
    rol: RolUsuario = RolUsuario.VENTAS
    activo: bool = True

    @field_validator("rol", mode="before")
    @classmethod
    def normalize_role(cls, value: RolUsuario | str) -> RolUsuario:
        return RolUsuario.from_input(value)

    @field_serializer("rol")
    def serialize_role(self, rol: RolUsuario) -> str:
        return rol.api_value


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6, description="Mínimo 6 caracteres")


class UsuarioResponse(UsuarioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
