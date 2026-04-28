"""Add quote versioning, ad-hoc line items and purchase order linkage.

Revision ID: 20260428_03
Revises: 20260428_02
Create Date: 2026-04-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260428_03"
down_revision = "20260428_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ordenes_venta: versionado + folio extendido
    op.alter_column(
        "ordenes_venta",
        "folio",
        existing_type=sa.String(length=20),
        type_=sa.String(length=40),
        existing_nullable=True,
    )
    op.add_column(
        "ordenes_venta",
        sa.Column("cotizacion_origen_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "ordenes_venta",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index(
        "ix_ordenes_venta_cotizacion_origen_id",
        "ordenes_venta",
        ["cotizacion_origen_id"],
    )
    op.create_foreign_key(
        "fk_ordenes_venta_origen",
        "ordenes_venta",
        "ordenes_venta",
        ["cotizacion_origen_id"],
        ["id"],
    )

    # detalles_orden: producto opcional + campos ad-hoc
    op.alter_column(
        "detalles_orden",
        "producto_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column("detalles_orden", sa.Column("sku_libre", sa.String(length=80), nullable=True))
    op.add_column("detalles_orden", sa.Column("descripcion_libre", sa.String(length=255), nullable=True))
    op.add_column("detalles_orden", sa.Column("moneda_origen_linea", sa.String(length=3), nullable=True))
    op.add_column(
        "detalles_orden",
        sa.Column("costo_base_linea", sa.DECIMAL(precision=12, scale=2), nullable=True),
    )

    # ordenes_compra: folio + moneda + vínculo a cotización
    op.add_column("ordenes_compra", sa.Column("folio", sa.String(length=40), nullable=True))
    op.create_index("ix_ordenes_compra_folio", "ordenes_compra", ["folio"], unique=True)
    op.add_column(
        "ordenes_compra",
        sa.Column("moneda", sa.String(length=3), nullable=False, server_default="MXN"),
    )
    op.add_column(
        "ordenes_compra",
        sa.Column("tipo_cambio", sa.DECIMAL(precision=12, scale=6), nullable=False, server_default="1.0"),
    )
    op.add_column("ordenes_compra", sa.Column("cotizacion_id", sa.Integer(), nullable=True))
    op.create_index("ix_ordenes_compra_cotizacion_id", "ordenes_compra", ["cotizacion_id"])
    op.create_foreign_key(
        "fk_ordenes_compra_cotizacion",
        "ordenes_compra",
        "ordenes_venta",
        ["cotizacion_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_ordenes_compra_cotizacion", "ordenes_compra", type_="foreignkey")
    op.drop_index("ix_ordenes_compra_cotizacion_id", table_name="ordenes_compra")
    op.drop_column("ordenes_compra", "cotizacion_id")
    op.drop_column("ordenes_compra", "tipo_cambio")
    op.drop_column("ordenes_compra", "moneda")
    op.drop_index("ix_ordenes_compra_folio", table_name="ordenes_compra")
    op.drop_column("ordenes_compra", "folio")

    op.drop_column("detalles_orden", "costo_base_linea")
    op.drop_column("detalles_orden", "moneda_origen_linea")
    op.drop_column("detalles_orden", "descripcion_libre")
    op.drop_column("detalles_orden", "sku_libre")
    op.alter_column(
        "detalles_orden",
        "producto_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_constraint("fk_ordenes_venta_origen", "ordenes_venta", type_="foreignkey")
    op.drop_index("ix_ordenes_venta_cotizacion_origen_id", table_name="ordenes_venta")
    op.drop_column("ordenes_venta", "version")
    op.drop_column("ordenes_venta", "cotizacion_origen_id")
    op.alter_column(
        "ordenes_venta",
        "folio",
        existing_type=sa.String(length=40),
        type_=sa.String(length=20),
        existing_nullable=True,
    )
