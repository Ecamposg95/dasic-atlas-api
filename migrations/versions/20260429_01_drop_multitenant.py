"""drop multi-tenant scaffolding (organization_id + nucleus tables)

Revision ID: 20260429_01
Revises: 20260428_04
Create Date: 2026-04-29
"""
from alembic import op


revision = "20260429_01"
down_revision = "20260428_04"
branch_labels = None
depends_on = None


_TENANT_COLUMNS = [
    ("clientes", "ix_clientes_organization_id"),
    ("transacciones_clientes", "ix_transacciones_clientes_organization_id"),
    ("ordenes_venta", "ix_ordenes_venta_organization_id"),
    ("detalles_orden", "ix_detalles_orden_organization_id"),
    ("quote_events", "ix_quote_events_organization_id"),
]


def upgrade() -> None:
    for table, index_name in _TENANT_COLUMNS:
        op.execute(f"DROP INDEX IF EXISTS {index_name}")
        op.execute(f"ALTER TABLE IF EXISTS {table} DROP COLUMN IF EXISTS organization_id")

    op.execute("DROP TABLE IF EXISTS user_organizations CASCADE")
    op.execute("DROP TABLE IF EXISTS branches CASCADE")
    op.execute("DROP TABLE IF EXISTS organizations CASCADE")


def downgrade() -> None:
    raise NotImplementedError("Downgrade no soportado — restaurar desde backup.")
