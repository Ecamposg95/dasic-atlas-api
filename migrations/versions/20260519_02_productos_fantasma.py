"""productos_fantasma table + detalle_orden.fantasma_id

Revision ID: 20260519_02
Revises: 20260519_01
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa


revision = "20260519_02"
down_revision = "20260519_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "productos_fantasma",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("descripcion_normalizada", sa.String(length=500), nullable=False),
        sa.Column("descripcion_original", sa.Text(), nullable=False),
        sa.Column("sku_libre", sa.String(length=80), nullable=True),
        sa.Column("costo_referencia", sa.Numeric(12, 2), nullable=False),
        sa.Column("moneda_referencia", sa.String(length=3), nullable=False, server_default="MXN"),
        sa.Column("proveedor_sugerido_id", sa.Integer(), sa.ForeignKey("proveedores.id"), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default="PENDIENTE"),
        sa.Column("promovido_a_producto_id", sa.Integer(), sa.ForeignKey("productos.id"), nullable=True),
        sa.Column("veces_solicitado", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ultimo_visto_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_productos_fantasma_descripcion", "productos_fantasma", ["descripcion_normalizada"])
    op.create_index("ix_productos_fantasma_estado", "productos_fantasma", ["estado"])
    op.create_index("ix_productos_fantasma_sku", "productos_fantasma", ["sku_libre"])

    op.add_column(
        "detalles_orden",
        sa.Column("fantasma_id", sa.Integer(), sa.ForeignKey("productos_fantasma.id"), nullable=True),
    )
    op.create_index("ix_detalles_orden_fantasma_id", "detalles_orden", ["fantasma_id"])


def downgrade() -> None:
    op.drop_index("ix_detalles_orden_fantasma_id", table_name="detalles_orden")
    op.drop_column("detalles_orden", "fantasma_id")
    op.drop_index("ix_productos_fantasma_sku", table_name="productos_fantasma")
    op.drop_index("ix_productos_fantasma_estado", table_name="productos_fantasma")
    op.drop_index("ix_productos_fantasma_descripcion", table_name="productos_fantasma")
    op.drop_table("productos_fantasma")
