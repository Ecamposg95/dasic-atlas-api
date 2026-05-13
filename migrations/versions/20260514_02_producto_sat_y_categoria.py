"""Producto: campos SAT (CFDI 4.0) + catálogo fabricante + categoría + abreviatura.

Revision ID: 20260514_02
Revises: 20260514_01
Create Date: 2026-05-14

Agregamos los campos fiscales mínimos para preparar CFDI 4.0:
  - clave_prod_serv: c_ClaveProdServ (8 dígitos, ej. 39121500)
  - clave_unidad_sat: c_ClaveUnidad (alfanum, ej. H87, KGM, E48)
  - objeto_imp: c_ObjetoImp (01/02/03/04/05)
  - descripcion_fiscal: opcional, fallback a `nombre` si NULL

Y los campos de clasificación interna pedidos por el usuario:
  - catalogo_fabricante: SKU del fabricante (no es el SKU interno)
  - categoria: agrupación interna (relevadores, contactores, etc.)
  - abreviatura: derivada de marca+categoria, editable

Todos NULL para no romper filas existentes; la UI los muestra con placeholders.
"""

from alembic import op


revision = "20260514_02"
down_revision = "20260514_01"
branch_labels = None
depends_on = None


_COLUMNAS = [
    # SAT (CFDI 4.0)
    ("clave_prod_serv", "VARCHAR(8)"),
    ("clave_unidad_sat", "VARCHAR(10)"),
    ("objeto_imp", "VARCHAR(2)"),
    ("descripcion_fiscal", "TEXT"),
    # Clasificación interna
    ("catalogo_fabricante", "VARCHAR(80)"),
    ("categoria", "VARCHAR(80)"),
    ("abreviatura", "VARCHAR(20)"),
]


def upgrade() -> None:
    for col, tipo in _COLUMNAS:
        op.execute(f"ALTER TABLE productos ADD COLUMN IF NOT EXISTS {col} {tipo}")

    # Índices útiles para filtros UI y búsqueda
    op.execute("CREATE INDEX IF NOT EXISTS ix_productos_categoria ON productos (categoria)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_productos_catalogo_fabricante ON productos (catalogo_fabricante)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_productos_abreviatura ON productos (abreviatura)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_productos_clave_prod_serv ON productos (clave_prod_serv)")


def downgrade() -> None:
    for col, _tipo in reversed(_COLUMNAS):
        op.execute(f"ALTER TABLE productos DROP COLUMN IF EXISTS {col}")
    op.execute("DROP INDEX IF EXISTS ix_productos_categoria")
    op.execute("DROP INDEX IF EXISTS ix_productos_catalogo_fabricante")
    op.execute("DROP INDEX IF EXISTS ix_productos_abreviatura")
    op.execute("DROP INDEX IF EXISTS ix_productos_clave_prod_serv")
