"""Tabla recordatorios — seguimiento de cotizaciones

Revision ID: 20260604_02
Revises: 20260604_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260604_02"
down_revision = "20260604_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recordatorios",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "orden_id",
            sa.Integer(),
            sa.ForeignKey("ordenes_venta.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "fecha_proximo_contacto",
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
        ),
        sa.Column("tipo_accion", sa.String(length=20), nullable=False, server_default=sa.text("'llamada'")),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False, server_default=sa.text("'pendiente'")),
        sa.Column(
            "creado_por_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=True,
        ),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("completado_en", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("recordatorios")
