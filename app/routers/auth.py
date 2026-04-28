from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core import get_settings
from app.db import get_db
from app import schemas
from app.services import UserService
from app.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])
settings = get_settings()


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = UserService.get_user_by_email(db, form_data.username)
    if not user or not UserService.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrecto",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "rol": user.rol.value,
        },
        expires_delta=access_token_expires,
    )

    response.set_cookie(
        key=settings.token_cookie_name,
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=settings.cookie_secure,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.token_cookie_name)
    return {"ok": True}
