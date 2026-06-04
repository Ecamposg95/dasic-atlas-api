"""CRM Kanban: tablas pipelines, pipeline_stages, deals

Revision ID: 20260604_01
Revises: 20260603_02
"""
from alembic import op
import sqlalchemy as sa

revision = "20260604_01"
down_revision = "20260603_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipelines",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.String(length=36), nullable=True, index=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("es_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "pipeline_stages",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.String(length=36), nullable=True, index=True),
        sa.Column(
            "pipeline_id",
            sa.Integer(),
            sa.ForeignKey("pipelines.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("nombre", sa.String(length=80), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("es_ganado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("es_perdido", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("organization_id", sa.String(length=36), nullable=True, index=True),
        sa.Column(
            "pipeline_id",
            sa.Integer(),
            sa.ForeignKey("pipelines.id"),
            nullable=False,
        ),
        sa.Column(
            "stage_id",
            sa.Integer(),
            sa.ForeignKey("pipeline_stages.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column(
            "cliente_id",
            sa.Integer(),
            sa.ForeignKey("clientes.id"),
            nullable=True,
        ),
        sa.Column(
            "orden_id",
            sa.Integer(),
            sa.ForeignKey("ordenes_venta.id"),
            nullable=True,
        ),
        sa.Column("monto", sa.DECIMAL(precision=14, scale=2), nullable=True),
        sa.Column("moneda", sa.String(length=3), nullable=False, server_default=sa.text("'MXN'")),
        sa.Column(
            "owner_user_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=True,
        ),
        sa.Column("orden_en_stage", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cerrado_en", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("deals")
    op.drop_table("pipeline_stages")
    op.drop_table("pipelines")
