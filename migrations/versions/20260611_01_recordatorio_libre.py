"""Recordatorio libre: orden_id nullable + cliente_id

Revision ID: 20260611_01
Revises: 20260608_02

Permite recordatorios sin orden asociada (follow-up genérico a un cliente).

Espejo de las entradas equivalentes en app/db/seeds.py::_BACKFILL_DDL
(Railway NO corre Alembic en deploy; el backfill es el camino real a producción).
"""
from alembic import op

revision = "20260611_01"
down_revision = "20260608_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE IF EXISTS recordatorios ALTER COLUMN orden_id DROP NOT NULL"
    )
    op.execute(
        "ALTER TABLE IF EXISTS recordatorios "
        "ADD COLUMN IF NOT EXISTS cliente_id INTEGER REFERENCES clientes(id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_recordatorios_cliente_id "
        "ON recordatorios (cliente_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_recordatorios_cliente_id")
    op.execute("ALTER TABLE IF EXISTS recordatorios DROP COLUMN IF EXISTS cliente_id")
    # No re-imponemos NOT NULL en downgrade: filas libres lo violarían.
