"""oc_recepcion_parcial — snapshot SAT/marca en línea de OC (US-026) +
cantidad_recibida/fecha_recepcion para recepción parcial (US-027).

Aditivo: NULL o server_default → OCs existentes intactas.

Revision ID: 20260601_04
Revises: 20260601_03
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_04"
down_revision = "20260601_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("detalles_compra", sa.Column("marca", sa.String(80), nullable=True))
    op.add_column("detalles_compra", sa.Column("clave_prod_serv", sa.String(8), nullable=True))
    op.add_column("detalles_compra", sa.Column("clave_unidad_sat", sa.String(10), nullable=True))
    op.add_column("detalles_compra", sa.Column("cantidad_recibida", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("detalles_compra", sa.Column("fecha_recepcion", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("detalles_compra", "fecha_recepcion")
    op.drop_column("detalles_compra", "cantidad_recibida")
    op.drop_column("detalles_compra", "clave_unidad_sat")
    op.drop_column("detalles_compra", "clave_prod_serv")
    op.drop_column("detalles_compra", "marca")
