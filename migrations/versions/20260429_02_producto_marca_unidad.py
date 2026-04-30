"""Add marca and unidad columns to productos.

Revision ID: 20260429_02
Revises: 20260429_01
Create Date: 2026-04-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_02"
down_revision = "20260429_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("productos", sa.Column("marca", sa.String(length=80), nullable=True))
    op.add_column(
        "productos",
        sa.Column("unidad", sa.String(length=20), nullable=True, server_default="PZA"),
    )
    op.create_index(op.f("ix_productos_marca"), "productos", ["marca"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_productos_marca"), table_name="productos")
    op.drop_column("productos", "unidad")
    op.drop_column("productos", "marca")
