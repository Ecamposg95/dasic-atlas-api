"""quote edit timestamps + fx override columns

Revision ID: 20260519_01
Revises: 20260517_02
Create Date: 2026-05-19

"""
from alembic import op
import sqlalchemy as sa


revision = "20260519_01"
down_revision = "20260517_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ordenes_venta",
        sa.Column("enviada_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ordenes_venta",
        sa.Column("pdf_generado_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ordenes_venta",
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_ordenes_venta_enviada_at",
        "ordenes_venta",
        ["enviada_at"],
    )
    op.add_column(
        "tipos_cambio_dia",
        sa.Column("nota", sa.Text(), nullable=True),
    )
    op.add_column(
        "tipos_cambio_dia",
        sa.Column("actualizado_por", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_tipos_cambio_dia_actualizado_por",
        "tipos_cambio_dia",
        "usuarios",
        ["actualizado_por"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_tipos_cambio_dia_actualizado_por",
        "tipos_cambio_dia",
        type_="foreignkey",
    )
    op.drop_column("tipos_cambio_dia", "actualizado_por")
    op.drop_column("tipos_cambio_dia", "nota")
    op.drop_index("ix_ordenes_venta_enviada_at", table_name="ordenes_venta")
    op.drop_column("ordenes_venta", "actualizado_en")
    op.drop_column("ordenes_venta", "pdf_generado_at")
    op.drop_column("ordenes_venta", "enviada_at")
