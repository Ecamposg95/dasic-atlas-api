"""remision libre: cliente_id + orden_venta_id nullable

Revision ID: 20260602_05
Revises: 20260601_06
"""
from alembic import op
import sqlalchemy as sa

revision = "20260602_05"
down_revision = "20260601_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("remisiones", "orden_venta_id", nullable=True)
    op.add_column("remisiones", sa.Column("cliente_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_remisiones_cliente", "remisiones", "clientes", ["cliente_id"], ["id"])
    op.create_index("ix_remisiones_cliente_id", "remisiones", ["cliente_id"])


def downgrade() -> None:
    op.drop_index("ix_remisiones_cliente_id", "remisiones")
    op.drop_constraint("fk_remisiones_cliente", "remisiones", type_="foreignkey")
    op.drop_column("remisiones", "cliente_id")
    op.alter_column("remisiones", "orden_venta_id", nullable=False)
