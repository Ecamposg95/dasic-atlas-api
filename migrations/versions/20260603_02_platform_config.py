"""platform_config (config runtime super-admin)

Revision ID: 20260603_02
Revises: 20260603_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260603_02"
down_revision = "20260603_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_config",
        sa.Column("clave", sa.String(length=60), primary_key=True),
        sa.Column("valor", sa.Text()),
        sa.Column("actualizado_por_id", sa.Integer()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("platform_config")
