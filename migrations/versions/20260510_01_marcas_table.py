"""Tabla `marcas` para taxonomía de catálogo + SKU interno.

Revision ID: 20260510_01
Revises: 20260430_02
Create Date: 2026-05-10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260510_01"
down_revision = "20260430_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CREATE TABLE IF NOT EXISTS para tolerar bases que ya hayan ejecutado
    # `Base.metadata.create_all()` en lifespan antes del upgrade Alembic.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS marcas (
            id SERIAL PRIMARY KEY,
            abreviatura VARCHAR(20) NOT NULL UNIQUE,
            nombre VARCHAR(150) NOT NULL,
            categoria VARCHAR(150),
            creado_en TIMESTAMPTZ DEFAULT now(),
            actualizado_en TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_marcas_abreviatura ON marcas (abreviatura)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_marcas_abreviatura")
    op.execute("DROP TABLE IF EXISTS marcas")
