"""Nota por línea (productos similares manuales) en detalles_orden.

Revision ID: 20260515_01
Revises: 20260513_02
Create Date: 2026-05-15

Texto libre, nullable. Sin CHECK constraints. El vendedor captura una
nota tipo "Ver también modelo XYZ-200 con flujo similar" que se imprime
en el PDF bajo el nombre del producto.
"""

from alembic import op


revision = "20260515_01"
down_revision = "20260513_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE detalles_orden ADD COLUMN IF NOT EXISTS observaciones_linea TEXT"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE detalles_orden DROP COLUMN IF EXISTS observaciones_linea")
