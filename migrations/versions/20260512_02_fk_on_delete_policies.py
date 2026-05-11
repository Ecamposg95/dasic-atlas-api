"""Políticas ON DELETE explícitas + índices compuestos para inventario.

Revision ID: 20260512_02
Revises: 20260512_01
Create Date: 2026-05-12

Decisiones (ver mega-plan inventario):
- movimientos_stock.producto_id: RESTRICT — kardex es inmutable.
- detalles_orden.producto_id: SET NULL — preservar histórico de cotización
  (ya hay sku_libre/descripcion_libre como snapshot).
- detalles_compra.producto_id: SET NULL — idem para OCs.
- productos.proveedor_principal_id / proveedor_alterno_id: SET NULL — borrar
  proveedor no debe matar productos.

Índices:
- (producto_id, tipo, creado_en) sobre movimientos_stock: acelera la query
  reservas_activas (filtra por producto+tipo+estatus).
- proveedor_alterno_id sobre productos: ya existe principal; faltaba alterno.
"""

from alembic import op


revision = "20260512_02"
down_revision = "20260512_01"
branch_labels = None
depends_on = None


def _rewrite_fk(table: str, column: str, ref_table: str, ref_column: str,
                old_constraint: str, new_constraint: str, on_delete: str) -> None:
    """Drop + Add con ON DELETE. PG no permite ALTER FK in-place."""
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {old_constraint}")
    op.execute(
        f"ALTER TABLE {table} ADD CONSTRAINT {new_constraint} "
        f"FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column}) "
        f"ON DELETE {on_delete}"
    )


def upgrade() -> None:
    # movimientos_stock.producto_id → RESTRICT
    _rewrite_fk(
        "movimientos_stock", "producto_id", "productos", "id",
        old_constraint="movimientos_stock_producto_id_fkey",
        new_constraint="movimientos_stock_producto_id_fkey",
        on_delete="RESTRICT",
    )

    # detalles_orden.producto_id → SET NULL (ya es nullable)
    _rewrite_fk(
        "detalles_orden", "producto_id", "productos", "id",
        old_constraint="detalles_orden_producto_id_fkey",
        new_constraint="detalles_orden_producto_id_fkey",
        on_delete="SET NULL",
    )

    # detalles_compra.producto_id → SET NULL
    op.execute("ALTER TABLE detalles_compra ALTER COLUMN producto_id DROP NOT NULL")
    _rewrite_fk(
        "detalles_compra", "producto_id", "productos", "id",
        old_constraint="detalles_compra_producto_id_fkey",
        new_constraint="detalles_compra_producto_id_fkey",
        on_delete="SET NULL",
    )

    # productos.proveedor_principal_id / proveedor_alterno_id → SET NULL
    _rewrite_fk(
        "productos", "proveedor_principal_id", "proveedores", "id",
        old_constraint="productos_proveedor_principal_id_fkey",
        new_constraint="productos_proveedor_principal_id_fkey",
        on_delete="SET NULL",
    )
    _rewrite_fk(
        "productos", "proveedor_alterno_id", "proveedores", "id",
        old_constraint="productos_proveedor_alterno_id_fkey",
        new_constraint="productos_proveedor_alterno_id_fkey",
        on_delete="SET NULL",
    )

    # Índices nuevos
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_movimientos_stock_producto_tipo_creado "
        "ON movimientos_stock (producto_id, tipo, creado_en)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_productos_proveedor_alterno_id "
        "ON productos (proveedor_alterno_id)"
    )


def downgrade() -> None:
    # Vuelve a NO ACTION (default PG) recreando las FKs sin ON DELETE.
    op.execute("DROP INDEX IF EXISTS ix_productos_proveedor_alterno_id")
    op.execute("DROP INDEX IF EXISTS ix_movimientos_stock_producto_tipo_creado")

    for table, column, ref_table, ref_column, name in [
        ("productos", "proveedor_alterno_id", "proveedores", "id", "productos_proveedor_alterno_id_fkey"),
        ("productos", "proveedor_principal_id", "proveedores", "id", "productos_proveedor_principal_id_fkey"),
        ("detalles_compra", "producto_id", "productos", "id", "detalles_compra_producto_id_fkey"),
        ("detalles_orden", "producto_id", "productos", "id", "detalles_orden_producto_id_fkey"),
        ("movimientos_stock", "producto_id", "productos", "id", "movimientos_stock_producto_id_fkey"),
    ]:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {name}")
        op.execute(
            f"ALTER TABLE {table} ADD CONSTRAINT {name} "
            f"FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column})"
        )
