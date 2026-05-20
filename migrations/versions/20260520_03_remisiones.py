"""remisiones + detalles_remision

Revision ID: 20260520_03
Revises: 20260520_02
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa


revision = "20260520_03"
down_revision = "20260520_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "remisiones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("folio", sa.String(40), nullable=True),
        sa.Column("orden_venta_id", sa.Integer(), sa.ForeignKey("ordenes_venta.id"), nullable=False),
        sa.Column("fecha_remision", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("transportista", sa.String(150), nullable=True),
        sa.Column("recibido_por", sa.String(150), nullable=True),
        sa.Column("recibido_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("creado_por_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("folio"),
    )
    op.create_index("ix_remisiones_orden_venta_id", "remisiones", ["orden_venta_id"])
    op.create_index("ix_remisiones_folio", "remisiones", ["folio"], unique=True)

    op.create_table(
        "detalles_remision",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("remision_id", sa.Integer(), sa.ForeignKey("remisiones.id"), nullable=False),
        sa.Column("detalle_orden_id", sa.Integer(), sa.ForeignKey("detalles_orden.id"), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("sku", sa.String(80), nullable=True),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("observaciones_linea", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_detalles_remision_remision_id", "detalles_remision", ["remision_id"])


def downgrade() -> None:
    op.drop_index("ix_detalles_remision_remision_id", table_name="detalles_remision")
    op.drop_table("detalles_remision")
    op.drop_index("ix_remisiones_folio", table_name="remisiones")
    op.drop_index("ix_remisiones_orden_venta_id", table_name="remisiones")
    op.drop_table("remisiones")
