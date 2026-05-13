"""DetalleCompra: campos para fantasmas + OCs sin cotización origen.

Revision ID: 20260514_05
Revises: 20260514_04
Create Date: 2026-05-14

Permite OC editables tipo cotizador:
  - DetalleCompra.producto_id NULLABLE (era NOT NULL)
  - DetalleCompra.sku_libre + descripcion_libre (parity con DetalleOrden)
  - DetalleCompra.moneda_origen_linea + costo_base_linea (auditar conversión)

OrdenCompra.cotizacion_id ya es nullable y proveedor_id existente sigue
siendo obligatorio (no se puede generar OC sin proveedor).
"""

from alembic import op


revision = "20260514_05"
down_revision = "20260514_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # producto_id pasa a nullable (DDL idempotente: si ya es nullable, no falla)
    op.execute(
        "ALTER TABLE detalles_compra ALTER COLUMN producto_id DROP NOT NULL"
    )
    op.execute(
        "ALTER TABLE detalles_compra ADD COLUMN IF NOT EXISTS sku_libre VARCHAR(80)"
    )
    op.execute(
        "ALTER TABLE detalles_compra ADD COLUMN IF NOT EXISTS descripcion_libre VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE detalles_compra ADD COLUMN IF NOT EXISTS moneda_origen_linea VARCHAR(3)"
    )
    op.execute(
        "ALTER TABLE detalles_compra ADD COLUMN IF NOT EXISTS costo_base_linea NUMERIC(12,2)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE detalles_compra DROP COLUMN IF EXISTS costo_base_linea")
    op.execute("ALTER TABLE detalles_compra DROP COLUMN IF EXISTS moneda_origen_linea")
    op.execute("ALTER TABLE detalles_compra DROP COLUMN IF EXISTS descripcion_libre")
    op.execute("ALTER TABLE detalles_compra DROP COLUMN IF EXISTS sku_libre")
    # No revertimos NOT NULL para evitar romper filas con producto_id NULL.
