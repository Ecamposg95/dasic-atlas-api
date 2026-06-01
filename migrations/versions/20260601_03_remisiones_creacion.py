"""remisiones_creacion — snapshot de precio/unidad SAT en línea de remisión +
moneda y toggle mostrar_precios a nivel remisión (EPIC 06).

Todas las columnas son NULL o tienen server_default → filas existentes intactas.

Revision ID: 20260601_03
Revises: 20260601_02
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_03"
down_revision = "20260601_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("remisiones", sa.Column("moneda", sa.String(3), nullable=True))
    op.add_column(
        "remisiones",
        sa.Column("mostrar_precios", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("detalles_remision", sa.Column("clave_unidad_sat", sa.String(10), nullable=True))
    op.add_column("detalles_remision", sa.Column("precio_unitario", sa.DECIMAL(10, 2), nullable=True))
    op.add_column("detalles_remision", sa.Column("subtotal", sa.DECIMAL(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("detalles_remision", "subtotal")
    op.drop_column("detalles_remision", "precio_unitario")
    op.drop_column("detalles_remision", "clave_unidad_sat")
    op.drop_column("remisiones", "mostrar_precios")
    op.drop_column("remisiones", "moneda")
