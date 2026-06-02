"""contactos — personas por empresa (sub-1 empresas+contactos)

Revision ID: 20260601_05
Revises: 20260601_04
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_05"
down_revision = "20260601_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contactos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("cargo", sa.String(80), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("telefono", sa.String(40), nullable=True),
        sa.Column("es_principal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("contactos")
