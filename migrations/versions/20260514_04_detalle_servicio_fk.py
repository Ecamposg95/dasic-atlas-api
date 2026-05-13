"""DetalleOrden: agregar servicio_id FK a servicios.

Revision ID: 20260514_04
Revises: 20260514_03
Create Date: 2026-05-14

Permite que una línea de cotización referencie a un Servicio del catálogo
nuevo. tipo_linea sigue siendo string-libre; valores aceptados ahora:
  - producto_catalogo (default, existente)
  - producto_fantasma (existente)
  - servicio          (legacy, ad-hoc por línea)
  - servicio_catalogo (NUEVO — viene del catálogo /servicios)

Sin cambios destructivos: servicio_id NULL por default; cotizaciones legacy
no se ven afectadas.
"""

from alembic import op


revision = "20260514_04"
down_revision = "20260514_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE detalles_orden ADD COLUMN IF NOT EXISTS "
        "servicio_id INTEGER REFERENCES servicios(id) ON DELETE SET NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_detalles_orden_servicio_id "
        "ON detalles_orden (servicio_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_detalles_orden_servicio_id")
    op.execute("ALTER TABLE detalles_orden DROP COLUMN IF EXISTS servicio_id")
