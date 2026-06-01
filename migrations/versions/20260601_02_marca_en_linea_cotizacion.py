"""marca_en_linea_cotizacion — snapshot de marca por línea + flag mostrar_marca
para el PDF de cotización (US-013/014).

Ambas columnas son aditivas: marca NULL y mostrar_marca con server_default
FALSE → filas existentes intactas y PDFs previos sin cambios.

Revision ID: 20260601_02
Revises: 20260601_01
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_02"
down_revision = "20260601_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("detalles_orden", sa.Column("marca", sa.String(80), nullable=True))
    op.add_column(
        "detalles_orden",
        sa.Column("mostrar_marca", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("detalles_orden", "mostrar_marca")
    op.drop_column("detalles_orden", "marca")
