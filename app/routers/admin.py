"""Endpoints administrativos: seed de datos de context/, etc.

Sólo accesibles para roles de admin.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.security import allow_admin

router = APIRouter(prefix="/api/admin", tags=["Administración"])


@router.post("/seed-context", dependencies=[Depends(allow_admin)])
def seed_context(
    dry_run: bool = False,
    db: Session = Depends(get_db),
):
    """Ingiere los datos de `context/` (productos, clientes, proveedores,
    cotizaciones de muestra, OCs de muestra, taxonomía de marcas).

    Idempotente. Útil para inicializar la base de Railway tras un primer deploy.
    """
    try:
        from scripts.import_context_data import run_seed
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo importar el script de seed: {exc}",
        )
    try:
        return run_seed(db, dry_run=dry_run)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Seed falló: {exc}")
