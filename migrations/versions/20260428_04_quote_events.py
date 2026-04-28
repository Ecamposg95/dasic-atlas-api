"""Quote events log (email, whatsapp, IA, notes).

Revision ID: 20260428_04
Revises: 20260428_03
Create Date: 2026-04-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260428_04"
down_revision = "20260428_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quote_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), nullable=True, index=True),
        sa.Column("orden_id", sa.Integer(), sa.ForeignKey("ordenes_venta.id"), nullable=False, index=True),
        sa.Column("canal", sa.String(length=20), nullable=False),
        sa.Column("direccion", sa.String(length=20), nullable=True),
        sa.Column("estatus", sa.String(length=20), nullable=True),
        sa.Column("asunto", sa.String(length=255), nullable=True),
        sa.Column("cuerpo", sa.Text(), nullable=True),
        sa.Column("destinatario", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("creado_por_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("quote_events")
