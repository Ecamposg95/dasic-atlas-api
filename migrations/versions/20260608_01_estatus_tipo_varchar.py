"""Enum nativo (estatusorden / tipomovimiento) → VARCHAR para TolerantEnum

Revision ID: 20260608_01
Revises: 20260604_02

El `Enum` nativo de PG valida el valor en la capa de hidratación de SQLAlchemy
y lanza `LookupError` ante cualquier label legacy (minúsculas / valores viejos),
tirando 500 en TODO endpoint que cargue la fila (ordenes-pendientes-entrega,
ventas/historial, dashboard, reportes…). Convertimos las columnas a VARCHAR para
que el `app.models.enums.TolerantEnum` coaccione en Python sin validación rígida
de la DB, y normalizamos los labels legacy → NOMBRE canónico (UPPER) para que los
filtros SQL por estatus/tipo sigan siendo correctos.

Espejo de las entradas equivalentes en `app/db/seeds.py::_BACKFILL_DDL`
(Railway NO corre Alembic en deploy; el backfill es el camino real a producción).
"""
from alembic import op

revision = "20260608_01"
down_revision = "20260604_02"
branch_labels = None
depends_on = None


# (tabla, columna) con enum nativo a convertir.
_COLS = [
    ("ordenes_venta", "estatus"),
    ("transacciones_clientes", "tipo"),
    ("transacciones_proveedores", "tipo"),
]


def upgrade() -> None:
    for tabla, col in _COLS:
        # DROP DEFAULT defensivo: un default `'x'::estatusorden` impediría el
        # cambio de tipo. El default real es Python-side, así que es seguro.
        op.execute(f"ALTER TABLE {tabla} ALTER COLUMN {col} DROP DEFAULT")
        op.execute(
            f"ALTER TABLE {tabla} ALTER COLUMN {col} TYPE VARCHAR(50) "
            f"USING {col}::text"
        )
        op.execute(
            f"UPDATE {tabla} SET {col} = UPPER({col}) "
            f"WHERE {col} IS NOT NULL AND {col} <> UPPER({col})"
        )


def downgrade() -> None:
    # No-op: revertir a enum nativo reintroduce exactamente el bug de
    # hidratación que esta migración resuelve. Las columnas permanecen VARCHAR.
    pass
