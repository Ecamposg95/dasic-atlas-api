import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core import get_settings
from app.db import get_db
from app import schemas
from app.services import UserService
from app.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user
from app.security.permissions import capabilities_for

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])
settings = get_settings()


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    remember: bool = Form(False),
    db: Session = Depends(get_db),
):
    user = UserService.get_user_by_email(db, form_data.username)
    if not user or not UserService.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrecto",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # "Recordar sesión": cookie persistente de larga duración. Sin él: JWT de
    # 12h y cookie de SESIÓN (sin max_age → el navegador la borra al cerrarse).
    if remember:
        access_token_expires = timedelta(days=settings.remember_session_days)
        cookie_max_age = settings.remember_session_days * 24 * 3600
    else:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        cookie_max_age = None

    access_token = create_access_token(
        data={
            "sub": user.email,
            "rol": user.rol.value,
        },
        expires_delta=access_token_expires,
    )

    cookie_kwargs = dict(
        key=settings.token_cookie_name,
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )
    if cookie_max_age is not None:
        cookie_kwargs["max_age"] = cookie_max_age
    response.set_cookie(**cookie_kwargs)

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    """User logueado + capabilities (consumido por el frontend para esconder UI).

    Si el admin desactiva al usuario (`activo=False`), el token sigue válido
    hasta expirar; este check bloquea el acceso aunque el JWT no haya caducado.
    """
    if not current_user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )
    caps = capabilities_for(current_user)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "nombre": current_user.nombre,
        "activo": current_user.activo,
        **caps,
    }


@router.post("/logout")
def logout(request: Request, response: Response):
    accept = request.headers.get("accept", "")
    wants_html = "text/html" in accept and "application/json" not in accept
    if wants_html:
        redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        redirect.delete_cookie(key=settings.token_cookie_name)
        return redirect
    response.delete_cookie(key=settings.token_cookie_name)
    return {"ok": True}
