"""cliente_merge_log (auditoría de dedup de empresas)

Revision ID: 20260603_01
Revises: 20260602_05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260603_01"
down_revision = "20260602_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cliente_merge_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("survivor_id", sa.Integer(), index=True),
        sa.Column("loser_id", sa.Integer(), index=True),
        sa.Column("loser_nombre", sa.String(length=150)),
        sa.Column("loser_rfc", sa.String(length=50)),
        sa.Column("loser_saldo", sa.Numeric(12, 2)),
        sa.Column("n_ordenes", sa.Integer()),
        sa.Column("n_transacciones", sa.Integer()),
        sa.Column("n_remisiones", sa.Integer()),
        sa.Column("n_contactos", sa.Integer()),
        sa.Column("merged_by_id", sa.Integer()),
        sa.Column("merged_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("cliente_merge_log")
