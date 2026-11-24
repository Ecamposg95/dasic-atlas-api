"""Interruptor de acceso a la plataforma (suspender / reactivar).

El estado vive en `platform_config`, así que cambia sin redeploy y sin tocar
el esquema. Con la plataforma suspendida solo entra el SUPERADMIN: el resto
recibe 423 en el login y en cualquier endpoint autenticado. Los datos no se
tocan — reactivar deja todo como estaba.

Se lee en cada request autenticada (una consulta por llave primaria) para que
el corte y la reactivación sean inmediatos, también para sesiones ya abiertas.
"""
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models

CLAVE_SUSPENDIDA = "plataforma_suspendida"
CLAVE_MENSAJE = "plataforma_suspension_mensaje"
CLAVES = (CLAVE_SUSPENDIDA, CLAVE_MENSAJE)

MENSAJE_DEFAULT = (
    "El acceso a la plataforma está suspendido temporalmente. "
    "Contacta a tu proveedor para reactivarlo."
)
MENSAJE_MAX = 500

# 423 Locked: distinto de 401 (sin sesión) y 403 (sin permiso) para que el
# frontend muestre la pantalla de suspensión en vez de mandar al login.
STATUS_SUSPENDIDA = 423
HEADER_SUSPENDIDA = "X-Plataforma-Suspendida"


def estado(db: Session) -> dict:
    filas = (
        db.query(models.PlatformConfig)
        .filter(models.PlatformConfig.clave.in_(CLAVES))
        .all()
    )
    valores = {f.clave: f for f in filas}
    fila = valores.get(CLAVE_SUSPENDIDA)
    mensaje_fila = valores.get(CLAVE_MENSAJE)
    mensaje = (mensaje_fila.valor or "").strip() if mensaje_fila else ""
    return {
        "suspendida": bool(fila and fila.valor == "1"),
        "mensaje": mensaje or MENSAJE_DEFAULT,
        "mensaje_personalizado": bool(mensaje),
        "actualizado_en": fila.actualizado_en if fila else None,
        "actualizado_por_id": fila.actualizado_por_id if fila else None,
    }


def es_superadmin(user: "models.Usuario") -> bool:
    try:
        return models.RolUsuario.from_input(user.rol) == models.RolUsuario.SUPERADMIN
    except Exception:
        return False


def verificar_acceso(db: Session, user: "models.Usuario") -> None:
    """Lanza 423 si la plataforma está suspendida y el usuario no es superadmin."""
    if es_superadmin(user):
        return
    actual = estado(db)
    if actual["suspendida"]:
        raise HTTPException(
            status_code=STATUS_SUSPENDIDA,
            detail=actual["mensaje"],
            headers={HEADER_SUSPENDIDA: "1"},
        )


def _guardar(db: Session, clave: str, valor: str | None, usuario_id: int | None) -> None:
    fila = db.query(models.PlatformConfig).filter(models.PlatformConfig.clave == clave).first()
    if valor is None:
        if fila:
            db.delete(fila)
        return
    if fila:
        fila.valor = valor
        fila.actualizado_por_id = usuario_id
        fila.actualizado_en = func.now()
    else:
        db.add(models.PlatformConfig(clave=clave, valor=valor, actualizado_por_id=usuario_id))


def cambiar(
    db: Session,
    *,
    suspendida: bool,
    mensaje: str | None,
    usuario: "models.Usuario",
) -> dict:
    """Suspende o reactiva. NO hace commit: el caller cierra la transacción."""
    _guardar(db, CLAVE_SUSPENDIDA, "1" if suspendida else "0", usuario.id)
    if mensaje is not None:
        limpio = mensaje.strip()[:MENSAJE_MAX]
        _guardar(db, CLAVE_MENSAJE, limpio or None, usuario.id)
    db.flush()
    return estado(db)
