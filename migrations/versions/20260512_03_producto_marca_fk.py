"""Producto.marca_id FK a marcas + backfill.

Revision ID: 20260512_03
Revises: 20260512_02
Create Date: 2026-05-12

La columna `marca` (texto) se mantiene como sombra/legacy y soporte para
imports CSV sin sincronización con la tabla marcas. La nueva `marca_id`
es la fuente canónica una vez la UI la pueble.

Backfill por match case-insensitive nombre→nombre. Productos sin match
quedan con marca_id=NULL y se ven en la UI como "sin marca".
"""

from alembic import op


revision = "20260512_03"
down_revision = "20260512_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotente: tolera bases que ya hayan corrido un create_all parcial.
    op.execute("""
        ALTER TABLE productos
        ADD COLUMN IF NOT EXISTS marca_id INTEGER REFERENCES marcas(id) ON DELETE SET NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_productos_marca_id ON productos(marca_id)")

    # Backfill: match nombre→nombre case-insensitive. Si el texto en productos
    # coincide con el nombre de una marca registrada, asocia. Si no, queda NULL.
    op.execute("""
        UPDATE productos p
        SET marca_id = m.id
        FROM marcas m
        WHERE p.marca_id IS NULL
          AND p.marca IS NOT NULL
          AND lower(trim(m.nombre)) = lower(trim(p.marca))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_productos_marca_id")
    op.execute("ALTER TABLE productos DROP COLUMN IF EXISTS marca_id")
