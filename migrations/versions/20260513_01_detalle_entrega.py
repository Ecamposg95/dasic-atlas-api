"""Tiempos de entrega por línea en detalles_orden.

Revision ID: 20260513_01
Revises: 20260512_03
Create Date: 2026-05-13

3 columnas nuevas + CHECK constraints. Los 3 vienen juntos o ninguno
(garantía semántica de que un rango siempre incluye unidad).
"""

from alembic import op


revision = "20260513_01"
down_revision = "20260512_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE detalles_orden ADD COLUMN IF NOT EXISTS entrega_min INTEGER")
    op.execute("ALTER TABLE detalles_orden ADD COLUMN IF NOT EXISTS entrega_max INTEGER")
    op.execute("ALTER TABLE detalles_orden ADD COLUMN IF NOT EXISTS entrega_unidad VARCHAR(10)")

    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_unidad_valida "
        "CHECK (entrega_unidad IS NULL OR entrega_unidad IN ('dias','semanas'))"
    )
    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_min_ge0 "
        "CHECK (entrega_min IS NULL OR entrega_min >= 0)"
    )
    # Garantiza coherencia del trío: los 3 vienen o ninguno; y min <= max.
    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_consistente "
        "CHECK ("
        "  (entrega_min IS NULL AND entrega_max IS NULL AND entrega_unidad IS NULL)"
        "  OR (entrega_min IS NOT NULL AND entrega_max IS NOT NULL AND entrega_unidad IS NOT NULL"
        "      AND entrega_max >= entrega_min)"
        ")"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_consistente")
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_min_ge0")
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_unidad_valida")
    op.execute("ALTER TABLE detalles_orden DROP COLUMN IF EXISTS entrega_unidad")
    op.execute("ALTER TABLE detalles_orden DROP COLUMN IF EXISTS entrega_max")
    op.execute("ALTER TABLE detalles_orden DROP COLUMN IF EXISTS entrega_min")
