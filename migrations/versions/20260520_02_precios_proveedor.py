"""precios_proveedor table

Revision ID: 20260520_02
Revises: 20260520_01
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa


revision = "20260520_02"
down_revision = "20260520_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "precios_proveedor",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proveedor_id", sa.Integer(), sa.ForeignKey("proveedores.id"), nullable=False),
        sa.Column("producto_id", sa.Integer(), sa.ForeignKey("productos.id"), nullable=True),
        sa.Column("descripcion_busqueda", sa.String(500), nullable=True),
        sa.Column("sku_libre", sa.String(80), nullable=True),
        sa.Column("precio", sa.Numeric(12, 2), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False, server_default="MXN"),
        sa.Column("fecha_vigencia_desde", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("fecha_vigencia_hasta", sa.Date(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("fuente", sa.String(20), nullable=False, server_default="MANUAL"),
        sa.Column("referencia_oc_id", sa.Integer(), sa.ForeignKey("ordenes_compra.id"), nullable=True),
        sa.Column("creado_por_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_precios_proveedor_proveedor_id", "precios_proveedor", ["proveedor_id"])
    op.create_index("ix_precios_proveedor_producto_id", "precios_proveedor", ["producto_id"])
    op.create_index("ix_precios_proveedor_descripcion", "precios_proveedor", ["descripcion_busqueda"])
    op.create_index("ix_precios_proveedor_sku", "precios_proveedor", ["sku_libre"])


def downgrade() -> None:
    op.drop_index("ix_precios_proveedor_sku", table_name="precios_proveedor")
    op.drop_index("ix_precios_proveedor_descripcion", table_name="precios_proveedor")
    op.drop_index("ix_precios_proveedor_producto_id", table_name="precios_proveedor")
    op.drop_index("ix_precios_proveedor_proveedor_id", table_name="precios_proveedor")
    op.drop_table("precios_proveedor")
