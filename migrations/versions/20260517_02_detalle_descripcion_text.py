"""Widen detalles_orden.descripcion_libre a TEXT (sin tope de 255 chars).

Revision ID: 20260517_02
Revises: 20260517_01
Create Date: 2026-05-13

`descripcion_libre` se usa para líneas fantasma/servicio donde el vendedor
pega la descripción real del fabricante; 255 chars se queda corto y dispara
422 en POST /api/ventas con "String should have at most 255 characters".
Ya `observaciones_linea` es TEXT por la misma razón.

Idempotente: si la columna ya es TEXT, no-op.
"""

from alembic import op


revision = "20260517_02"
down_revision = "20260517_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE detalles_orden ALTER COLUMN descripcion_libre TYPE TEXT")


def downgrade() -> None:
    # Downgrade trunca a 255 si hay datos largos (Postgres exige USING explícito).
    op.execute(
        "ALTER TABLE detalles_orden ALTER COLUMN descripcion_libre TYPE VARCHAR(255) "
        "USING LEFT(descripcion_libre, 255)"
    )
