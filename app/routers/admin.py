"""Endpoints administrativos: seed de datos de context/, etc.

Sólo accesibles para superadmin.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.db import engine, get_db
from app.security.jwt import allow_superadmin

router = APIRouter(prefix="/api/admin", tags=["Administración"])


@router.post("/seed-context", dependencies=[Depends(allow_superadmin)])
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


class _DropConfirm(BaseModel):
    confirm: str


@router.post("/drop-all-tables", dependencies=[Depends(allow_superadmin)])
def drop_all_tables(payload: _DropConfirm):
    """Elimina **todas** las tablas de la base de datos con CASCADE.

    ⚠️  OPERACIÓN DESTRUCTIVA E IRREVERSIBLE. Úsese únicamente para
    reinicializar el esquema en entornos de desarrollo/staging.

    Requiere body: { "confirm": "BORRAR TODO" }
    """
    if payload.confirm != "BORRAR TODO":
        raise HTTPException(
            status_code=400,
            detail='Se requiere confirmación explícita: { "confirm": "BORRAR TODO" }',
        )
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        with engine.begin() as conn:
            # Desactivar restricciones de FK temporalmente para poder
            # eliminar tablas en cualquier orden sin violar integridad.
            conn.execute(text("SET session_replication_role = replica;"))
            for table in table_names:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            conn.execute(text("SET session_replication_role = DEFAULT;"))

        return {
            "status": "ok",
            "warning": "Todas las tablas han sido eliminadas de forma permanente.",
            "dropped_tables": table_names,
            "count": len(table_names),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar tablas: {exc}",
        )
