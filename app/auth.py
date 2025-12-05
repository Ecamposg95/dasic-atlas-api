from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List

import database
import models
import services

# --- CONFIGURACIÓN ---
SECRET_KEY = "ESTA_ES_UNA_CLAVE_SECRETA_SUPER_SEGURA_CAMBIALA"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 

# Token URL apuntando al endpoint correcto
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = services.UserService.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[models.RolUsuario]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: models.Usuario = Depends(get_current_user)):
        if user.rol not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="No tienes permisos")
        return user

# Instancias de permisos
allow_admin = RoleChecker([models.RolUsuario.ADMIN])
allow_admin_asistente = RoleChecker([models.RolUsuario.ADMIN, models.RolUsuario.ASISTENTE])
allow_all_staff = RoleChecker([models.RolUsuario.ADMIN, models.RolUsuario.ASISTENTE, models.RolUsuario.VENDEDOR])