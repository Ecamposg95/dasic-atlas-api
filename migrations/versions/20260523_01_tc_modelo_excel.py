"""tc modelo Excel V_03 — tc_mn_a_usd + tc_usd_a_mn en ordenes_venta

Backfill: para filas existentes computa
    tc_mn_a_usd = tipo_cambio - 1
    tc_usd_a_mn = tipo_cambio + 1
(asume que historia operó "como si" hubiera tenido spread default ±1 peso —
decisión consciente del usuario para que totales legacy coincidan al
recalcularse contra el nuevo modelo).

Revision ID: 20260523_01
Revises: 20260520_03
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa


revision = "20260523_01"
down_revision = "20260520_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ordenes_venta",
        sa.Column("tc_mn_a_usd", sa.DECIMAL(12, 6), nullable=True),
    )
    op.add_column(
        "ordenes_venta",
        sa.Column("tc_usd_a_mn", sa.DECIMAL(12, 6), nullable=True),
    )
    # Backfill total: historia se reinterpreta con spread ±1 peso. Idempotente:
    # solo afecta filas con tc_mn_a_usd o tc_usd_a_mn NULL.
    op.execute("""
        UPDATE ordenes_venta
           SET tc_mn_a_usd = COALESCE(tc_mn_a_usd, GREATEST(tipo_cambio - 1, 0.000001)),
               tc_usd_a_mn = COALESCE(tc_usd_a_mn, tipo_cambio + 1)
         WHERE tc_mn_a_usd IS NULL OR tc_usd_a_mn IS NULL
    """)


def downgrade() -> None:
    op.drop_column("ordenes_venta", "tc_usd_a_mn")
    op.drop_column("ordenes_venta", "tc_mn_a_usd")
