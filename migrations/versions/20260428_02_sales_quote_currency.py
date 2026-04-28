"""Add quote currency and utility fields to sales tables.

Revision ID: 20260428_02
Revises: 20260428_01
Create Date: 2026-04-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260428_02"
down_revision = "20260428_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ordenes_venta",
        sa.Column("moneda", sa.String(length=3), nullable=False, server_default="MXN"),
    )
    op.add_column(
        "ordenes_venta",
        sa.Column("tipo_cambio", sa.DECIMAL(precision=12, scale=6), nullable=False, server_default="1.0"),
    )
    op.add_column(
        "detalles_orden",
        sa.Column("utilidad_aplicada", sa.DECIMAL(precision=10, scale=2), nullable=False, server_default="0.00"),
    )


def downgrade() -> None:
    op.drop_column("detalles_orden", "utilidad_aplicada")
    op.drop_column("ordenes_venta", "tipo_cambio")
    op.drop_column("ordenes_venta", "moneda")
