"""cotizador robusto + inventario auditable

Revision ID: 20260430_01
Revises: 20260429_02
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260430_01"
down_revision = "20260429_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "productos",
        sa.Column("proveedor_principal_id", sa.Integer(), sa.ForeignKey("proveedores.id"), nullable=True),
    )
    op.add_column(
        "productos",
        sa.Column("proveedor_alterno_id", sa.Integer(), sa.ForeignKey("proveedores.id"), nullable=True),
    )
    op.add_column(
        "productos",
        sa.Column("tiempo_entrega_dias", sa.Integer(), nullable=False, server_default="7"),
    )
    op.add_column(
        "productos",
        sa.Column("es_servicio", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_productos_proveedor_principal_id", "productos", ["proveedor_principal_id"]
    )

    op.add_column(
        "detalles_orden",
        sa.Column(
            "tipo_linea",
            sa.String(length=20),
            nullable=False,
            server_default="producto_catalogo",
        ),
    )
    op.add_column(
        "detalles_orden",
        sa.Column(
            "proveedor_sugerido_id",
            sa.Integer(),
            sa.ForeignKey("proveedores.id"),
            nullable=True,
        ),
    )

    op.create_table(
        "movimientos_stock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("producto_id", sa.Integer(), sa.ForeignKey("productos.id"), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("referencia_tipo", sa.String(length=20), nullable=True),
        sa.Column("referencia_id", sa.Integer(), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("stock_resultante", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_movimientos_stock_producto_creado",
        "movimientos_stock",
        ["producto_id", "creado_en"],
    )
    op.create_index(
        "ix_movimientos_stock_referencia_id",
        "movimientos_stock",
        ["referencia_id"],
    )

    op.create_table(
        "tipos_cambio_dia",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.Date(), nullable=False, unique=True),
        sa.Column("usd_mxn", sa.DECIMAL(precision=12, scale=6), nullable=False),
        sa.Column("fuente", sa.String(length=20), nullable=False),
        sa.Column(
            "obtenido_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_tipos_cambio_dia_fecha", "tipos_cambio_dia", ["fecha"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_tipos_cambio_dia_fecha", table_name="tipos_cambio_dia")
    op.drop_table("tipos_cambio_dia")
    op.drop_index("ix_movimientos_stock_referencia_id", table_name="movimientos_stock")
    op.drop_index("ix_movimientos_stock_producto_creado", table_name="movimientos_stock")
    op.drop_table("movimientos_stock")
    op.drop_column("detalles_orden", "proveedor_sugerido_id")
    op.drop_column("detalles_orden", "tipo_linea")
    op.drop_index("ix_productos_proveedor_principal_id", table_name="productos")
    op.drop_column("productos", "es_servicio")
    op.drop_column("productos", "tiempo_entrega_dias")
    op.drop_column("productos", "proveedor_alterno_id")
    op.drop_column("productos", "proveedor_principal_id")
