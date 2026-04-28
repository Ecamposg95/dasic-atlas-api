"""Add commercial SKU and purchase currency to productos.

Revision ID: 20260428_01
Revises:
Create Date: 2026-04-28
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260428_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("productos", sa.Column("sku_comercial", sa.String(length=80), nullable=True))
    op.add_column(
        "productos",
        sa.Column("moneda_compra", sa.String(length=3), nullable=False, server_default="MXN"),
    )
    op.create_index(op.f("ix_productos_sku_comercial"), "productos", ["sku_comercial"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_productos_sku_comercial"), table_name="productos")
    op.drop_column("productos", "moneda_compra")
    op.drop_column("productos", "sku_comercial")
