"""tolerancia_tc — spread configurable del TC USD/MXN por cotización

Reemplaza el ±1 hardcoded del helper `_resolve_directional_tcs` por un
valor por cotización. Rango efectivo 0.1 – 1.0 (validado en Pydantic/Zod;
no se aplica CHECK en BD para mantener idempotencia simple en
`_BACKFILL_DDL`).

Postgres backfilea automáticamente las filas existentes con `1.0`
gracias al `server_default`, preservando el comportamiento previo.

Revision ID: 20260526_01
Revises: 20260525_01
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa


revision = "20260526_01"
down_revision = "20260525_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ordenes_venta",
        sa.Column(
            "tolerancia_tc",
            sa.Numeric(3, 2),
            nullable=False,
            server_default="1.0",
        ),
    )


def downgrade() -> None:
    op.drop_column("ordenes_venta", "tolerancia_tc")
