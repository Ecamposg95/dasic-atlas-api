"""orden_contacto — contacto_id en ordenes_venta (sub-2)

Revision ID: 20260601_06
Revises: 20260601_05
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_06"
down_revision = "20260601_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ordenes_venta", sa.Column("contacto_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_ordenes_venta_contacto_id", "ordenes_venta", "contactos",
        ["contacto_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_ordenes_venta_contacto_id", "ordenes_venta", type_="foreignkey")
    op.drop_column("ordenes_venta", "contacto_id")
