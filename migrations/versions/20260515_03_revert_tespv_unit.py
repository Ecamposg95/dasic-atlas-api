"""Revertir T.E.S.P.V. como unidad: ahora es sufijo automático del PDF.

Revision ID: 20260515_03
Revises: 20260515_02
Create Date: 2026-05-15

T.E.S.P.V. (Tiempo de Entrega Salvo Previa Venta) NO es una unidad
independiente. Es un sello que aplica SIEMPRE a cualquier tiempo de
entrega capturado (días/semanas) y se imprime en el PDF como sufijo:
"1–4 días T.E.S.P.V." o "2 semanas T.E.S.P.V.".

Esta migración deshace 20260515_02:
- ck_detalle_entrega_unidad_valida vuelve a aceptar solo 'dias'|'semanas'.
- ck_detalle_entrega_consistente vuelve a la regla original (los 3 o
  ninguno, max >= min).
- Cualquier registro con unidad='tespv' se limpia a NULL en los 3
  campos (safety; no debería haber filas todavía).
"""

from alembic import op
from sqlalchemy import text


revision = "20260515_03"
down_revision = "20260515_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Limpiar cualquier fila que haya quedado con entrega_unidad='tespv'
    # antes de re-aplicar el CHECK estricto. En la práctica deberían ser 0.
    conn = op.get_bind()
    result = conn.execute(text(
        "UPDATE detalles_orden "
        "SET entrega_min = NULL, entrega_max = NULL, entrega_unidad = NULL "
        "WHERE entrega_unidad = 'tespv'"
    ))
    if result.rowcount:
        print(f"[20260515_03] Limpiadas {result.rowcount} filas con entrega_unidad='tespv'")

    # Drop + Add ambos CHECK a su forma pre-tespv
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_unidad_valida")
    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_unidad_valida "
        "CHECK (entrega_unidad IS NULL OR entrega_unidad IN ('dias','semanas'))"
    )

    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_consistente")
    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_consistente "
        "CHECK ("
        "  (entrega_min IS NULL AND entrega_max IS NULL AND entrega_unidad IS NULL)"
        "  OR (entrega_min IS NOT NULL AND entrega_max IS NOT NULL AND entrega_unidad IS NOT NULL"
        "      AND entrega_max >= entrega_min)"
        ")"
    )


def downgrade() -> None:
    # Re-aplicar la versión que admitía 'tespv'
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_consistente")
    op.execute("ALTER TABLE detalles_orden DROP CONSTRAINT IF EXISTS ck_detalle_entrega_unidad_valida")
    op.execute(
        "ALTER TABLE detalles_orden ADD CONSTRAINT ck_detalle_entrega_unidad_valida "
        "CHECK (entrega_unidad IS NULL OR entrega_unidad IN ('dias','semanas','tespv'))"
    )
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
