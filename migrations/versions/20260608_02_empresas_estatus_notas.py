"""Empresas vista 360: clientes.estatus + tabla notas_empresa

Revision ID: 20260608_02
Revises: 20260608_01

Espejo de las entradas equivalentes en app/db/seeds.py::_BACKFILL_DDL
(Railway NO corre Alembic en deploy; el backfill es el camino real a producción).
"""
from alembic import op
import sqlalchemy as sa

revision = "20260608_02"
down_revision = "20260608_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE IF EXISTS clientes "
        "ADD COLUMN IF NOT EXISTS estatus VARCHAR(12) NOT NULL DEFAULT 'activo'"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notas_empresa (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
            autor_id INTEGER REFERENCES usuarios(id),
            texto TEXT NOT NULL,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_notas_empresa_cliente_id ON notas_empresa(cliente_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notas_empresa")
    op.execute("ALTER TABLE IF EXISTS clientes DROP COLUMN IF EXISTS estatus")
