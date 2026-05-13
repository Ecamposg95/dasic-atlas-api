"""Eliminar columnas redundantes en productos: abreviatura, catalogo_fabricante.

Revision ID: 20260517_01
Revises: 20260514_06
Create Date: 2026-05-17

Las columnas `productos.abreviatura` y `productos.catalogo_fabricante`
introducidas en `20260514_02_producto_sat_y_categoria.py` resultaron
duplicar la semántica de campos ya existentes:

  - `sku`            ya es el "SKU interno" (prefijo de marca + consecutivo,
                     ej. ABCS-0001). Esto es la "abreviatura".
  - `sku_comercial`  ya es el catálogo del fabricante (ej. LC1D09BL).

Mantener cuatro campos confunde la UI y duplica fuentes de verdad.
Esta migración los elimina + sus índices. La info útil que pudiera
haberse capturado en `abreviatura` se preserva en `sku` (igual auto-gen).
Si algún producto tiene `catalogo_fabricante` pero no `sku_comercial`,
el upgrade lo copia antes de drop.
"""

from alembic import op


revision = "20260517_01"
down_revision = "20260514_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill defensivo: si catalogo_fabricante tiene valor y sku_comercial
    # está vacío, copiamos antes de drop para no perder datos del usuario.
    op.execute("""
        UPDATE productos
           SET sku_comercial = catalogo_fabricante
         WHERE catalogo_fabricante IS NOT NULL
           AND catalogo_fabricante <> ''
           AND (sku_comercial IS NULL OR sku_comercial = '')
    """)

    # Drop índices primero (algunos los crea 20260514_02, otros no existieron)
    op.execute("DROP INDEX IF EXISTS ix_productos_abreviatura")
    op.execute("DROP INDEX IF EXISTS ix_productos_catalogo_fabricante")

    # Drop columnas
    op.execute("ALTER TABLE productos DROP COLUMN IF EXISTS abreviatura")
    op.execute("ALTER TABLE productos DROP COLUMN IF EXISTS catalogo_fabricante")


def downgrade() -> None:
    # Re-creación sin restauración de datos — eran columnas opcionales.
    op.execute("ALTER TABLE productos ADD COLUMN IF NOT EXISTS abreviatura VARCHAR(20)")
    op.execute("ALTER TABLE productos ADD COLUMN IF NOT EXISTS catalogo_fabricante VARCHAR(80)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_productos_abreviatura ON productos (abreviatura)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_productos_catalogo_fabricante ON productos (catalogo_fabricante)")
