from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.services import UserService


# --- CONFIGURACION (prototype defaults) ---
SECRET_KEY = "ESTA_ES_UNA_CLAVE_SECRETA_SUPER_SEGURA_CAMBIALA"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = UserService.get_user_by_email(db, email=email)
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


allow_admin = RoleChecker([models.RolUsuario.ADMIN])
allow_admin_asistente = RoleChecker([models.RolUsuario.ADMIN, models.RolUsuario.ASISTENTE])
allow_all_staff = RoleChecker(
    [models.RolUsuario.ADMIN, models.RolUsuario.ASISTENTE, models.RolUsuario.VENDEDOR]
)
