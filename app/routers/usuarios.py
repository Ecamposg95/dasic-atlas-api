from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app import models
from app import schemas
from app.db import get_db
from app.models.enums import RolUsuario
from app.security import get_current_user
from app.security.jwt import allow_user_admin
from app.services import UserService

router = APIRouter(prefix="/api/usuarios", tags=["Administración de Usuarios"])


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[str] = None
    rol: Optional[RolUsuario] = None
    activo: Optional[bool] = None

    @field_validator("rol", mode="before")
    @classmethod
    def normalize_role(cls, v):
        if v is None:
            return None
        return RolUsuario.from_input(v)


class PasswordResetIn(BaseModel):
    password: str = Field(..., min_length=6, description="Mínimo 6 caracteres")

# Fase 1 RBAC: mantener gestión de usuarios sólo para el rol admin-equivalente.
@router.get("/", response_model=List[schemas.UsuarioResponse], dependencies=[Depends(allow_user_admin)])
def listar_usuarios(db: Session = Depends(get_db)):
    # Ocultamos al super admin del listado general para evitar accidentes, o lo mostramos
    return db.query(models.Usuario).all()

@router.post("/", response_model=schemas.UsuarioResponse, dependencies=[Depends(allow_user_admin)])
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # Validar correo único
    if UserService.get_user_by_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    return UserService.create_user(db, usuario)

@router.put("/{user_id}", response_model=schemas.UsuarioResponse, dependencies=[Depends(allow_user_admin)])
def actualizar_usuario(
    user_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
):
    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"] and data["email"] != user.email:
        if UserService.get_user_by_email(db, data["email"]):
            raise HTTPException(400, "El correo ya está registrado")
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/password", dependencies=[Depends(allow_user_admin)])
def reset_password(
    user_id: int,
    payload: PasswordResetIn,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    """Reset de contraseña por admin. No requiere la contraseña previa."""
    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    user.password_hash = UserService.get_password_hash(payload.password)
    db.commit()
    return {
        "ok": True,
        "user_id": user.id,
        "email": user.email,
        "actualizado_por": current_user.email,
    }


@router.delete("/{user_id}", dependencies=[Depends(allow_user_admin)])
def eliminar_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
):
    user_to_delete = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user_to_delete.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
        
    db.delete(user_to_delete)
    db.commit()
    return {"mensaje": "Usuario eliminado"}
