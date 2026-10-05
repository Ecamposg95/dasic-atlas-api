"""audit_log: bitácora global de mutaciones sensibles (Ola 4 E5).

Revision ID: 20260820_01
Revises: 20260806_01
"""
import sqlalchemy as sa
from alembic import op

revision = "20260820_01"
down_revision = "20260806_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("accion", sa.String(40), nullable=False),
        sa.Column("entidad", sa.String(40), nullable=False),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column("resumen", sa.String(400), nullable=False),
        sa.Column("datos", sa.Text(), nullable=True),
    )
    op.create_index("ix_audit_log_id", "audit_log", ["id"])
    op.create_index("ix_audit_log_fecha", "audit_log", ["fecha"])
    op.create_index("ix_audit_log_usuario_id", "audit_log", ["usuario_id"])
    op.create_index("ix_audit_log_entidad", "audit_log", ["entidad", "entidad_id"])


def downgrade():
    op.drop_table("audit_log")
