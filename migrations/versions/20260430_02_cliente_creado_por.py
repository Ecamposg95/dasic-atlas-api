"""cliente.creado_por_id para owner scoping de VENTAS.

Revision ID: 20260430_02
Revises: 20260430_01
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260430_02"
down_revision = "20260430_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clientes",
        sa.Column("creado_por_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
    )
    op.create_index("ix_clientes_creado_por_id", "clientes", ["creado_por_id"])


def downgrade() -> None:
    op.drop_index("ix_clientes_creado_por_id", table_name="clientes")
    op.drop_column("clientes", "creado_por_id")
