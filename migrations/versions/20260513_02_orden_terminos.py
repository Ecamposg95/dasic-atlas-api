"""Bloque editable de Condiciones Comerciales por cotización.

Revision ID: 20260513_02
Revises: 20260513_01
Create Date: 2026-05-13

NULL en cotizaciones legacy → el PDF usa el bloque hardcoded como
fallback. Cotizaciones nuevas reciben los defaults del constante
_DEFAULT_TERMINOS en backend.
"""

from alembic import op


revision = "20260513_02"
down_revision = "20260513_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE ordenes_venta ADD COLUMN IF NOT EXISTS terminos_condiciones TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE ordenes_venta DROP COLUMN IF EXISTS terminos_condiciones")
