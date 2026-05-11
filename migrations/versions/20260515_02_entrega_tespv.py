"""T.E.S.P.V. como tercera opción de tiempo de entrega.

Revision ID: 20260515_02
Revises: 20260515_01
Create Date: 2026-05-15

Amplía:
- ck_detalle_entrega_unidad_valida: acepta 'tespv'
- ck_detalle_entrega_consistente: cuando unidad='tespv', min/max pueden
  ser NULL (no aplica rango — el tiempo depende de confirmación con
  proveedor).

T.E.S.P.V. = "Tiempo de Entrega Salvo Previa Venta".
"""

from alembic import op


revision = "20260515_02"
down_revision = "20260515_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop + Add ck_detalle_entrega_unidad_valida con 'tespv' incluido
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_unidad_valida")
    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_unidad_valida "
        "CHECK (entrega_unidad IS NULL OR entrega_unidad IN ('dias','semanas','tespv'))"
    )

    # Drop + Add ck_detalle_entrega_consistente con la rama TESPV
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_consistente")
    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_consistente "
        "CHECK ("
        "  (entrega_min IS NULL AND entrega_max IS NULL AND entrega_unidad IS NULL)"
        "  OR (entrega_unidad = 'tespv')"
        "  OR (entrega_min IS NOT NULL AND entrega_max IS NOT NULL"
        "      AND entrega_unidad IN ('dias','semanas')"
        "      AND entrega_max >= entrega_min)"
        ")"
    )


def downgrade() -> None:
    # Vuelve a las versiones previas (sin tespv, los 3 obligatorios juntos)
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_consistente")
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_unidad_valida")
    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_unidad_valida "
        "CHECK (entrega_unidad IS NULL OR entrega_unidad IN ('dias','semanas'))"
    )
    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_consistente "
        "CHECK ("
        "  (entrega_min IS NULL AND entrega_max IS NULL AND entrega_unidad IS NULL)"
        "  OR (entrega_min IS NOT NULL AND entrega_max IS NOT NULL AND entrega_unidad IS NOT NULL"
        "      AND entrega_max >= entrega_min)"
        ")"
    )
