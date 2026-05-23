"""descuento_proveedor en detalles_orden

Separa el descuento al CLIENTE (descuento_aplicado, match Excel N6) del
descuento que el PROVEEDOR le da a Dasic (descuento_proveedor, match Excel
H6). Hoy el SPA usaba `descuento_aplicado` para ambos, distorsionando el
cálculo "Costo OC".

Filas existentes obtienen descuento_proveedor=0 — semánticamente correcto
(antes nadie capturaba descuento de proveedor por línea; el costo OC
reflejaba el costo bruto).

Revision ID: 20260524_01
Revises: 20260523_01
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa


revision = "20260524_01"
down_revision = "20260523_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "detalles_orden",
        sa.Column(
            "descuento_proveedor",
            sa.DECIMAL(5, 2),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("detalles_orden", "descuento_proveedor")
