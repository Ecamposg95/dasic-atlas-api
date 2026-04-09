from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models
from app import schemas
from app.db import get_db
from app.security import allow_admin, get_current_user
from app.services import UserService

router = APIRouter(prefix="/api/usuarios", tags=["Administración de Usuarios"])

# Solo el ADMIN puede ver y crear usuarios
@router.get("/", response_model=List[schemas.UsuarioResponse], dependencies=[Depends(allow_admin)])
def listar_usuarios(db: Session = Depends(get_db)):
    # Ocultamos al super admin del listado general para evitar accidentes, o lo mostramos
    return db.query(models.Usuario).all()

@router.post("/", response_model=schemas.UsuarioResponse, dependencies=[Depends(allow_admin)])
def crear_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # Validar correo único
    if UserService.get_user_by_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    return UserService.create_user(db, usuario)

@router.delete("/{user_id}", dependencies=[Depends(allow_admin)])
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
