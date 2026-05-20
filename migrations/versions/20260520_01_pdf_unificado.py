"""pdf_unificado flag + concepto_unificado en ordenes_venta

Revision ID: 20260520_01
Revises: 20260519_02
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa


revision = "20260520_01"
down_revision = "20260519_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ordenes_venta",
        sa.Column("pdf_unificado", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "ordenes_venta",
        sa.Column("concepto_unificado", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ordenes_venta", "concepto_unificado")
    op.drop_column("ordenes_venta", "pdf_unificado")
