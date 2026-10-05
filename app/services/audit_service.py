"""Registro en la bitácora global de mutaciones (tabla audit_log).

`registrar` NO hace commit: participa en la transacción del caller para que
el evento se persista —o se revierta— atómicamente con la mutación auditada.
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from app import models


def registrar(
    db: Session,
    *,
    usuario: Optional["models.Usuario"],
    accion: str,
    entidad: str,
    entidad_id: Optional[int],
    resumen: str,
    datos: Optional[dict] = None,
) -> "models.AuditLog":
    evento = models.AuditLog(
        usuario_id=usuario.id if usuario is not None else None,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        resumen=resumen[:400],
        datos=json.dumps(datos, ensure_ascii=False, default=str) if datos else None,
    )
    db.add(evento)
    return evento
