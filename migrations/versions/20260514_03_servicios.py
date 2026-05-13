"""Tabla `servicios` — catálogo de servicios reutilizables (con SAT default).

Revision ID: 20260514_03
Revises: 20260514_02
Create Date: 2026-05-14

Servicios persistibles en catálogo, distintos de los "servicios temporales"
que hoy viven como fantasma en DetalleOrden. Cada servicio tiene SAT default
81111500 (servicios profesionales / consultoría) y unidad SAT E48 (unidad de
servicio); ambos editables por servicio.
"""

from alembic import op


revision = "20260514_03"
down_revision = "20260514_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
            id SERIAL PRIMARY KEY,
            organization_id VARCHAR(36),
            codigo VARCHAR(30) NOT NULL,
            nombre VARCHAR(150) NOT NULL,
            descripcion TEXT,
            categoria_servicio VARCHAR(40),
            costo NUMERIC(12,2) NOT NULL DEFAULT 0,
            moneda VARCHAR(3) NOT NULL DEFAULT 'MXN',
            tiempo_estimado NUMERIC(8,2),
            unidad_tiempo VARCHAR(10),
            clave_prod_serv VARCHAR(8) NOT NULL DEFAULT '81111500',
            clave_unidad_sat VARCHAR(10) NOT NULL DEFAULT 'E48',
            objeto_imp VARCHAR(2) DEFAULT '02',
            descripcion_fiscal TEXT,
            activo BOOLEAN NOT NULL DEFAULT true,
            creado_por_id INTEGER REFERENCES usuarios(id),
            creado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    # Unicidad por (org, codigo). Si organization_id es NULL (single-tenant
    # legacy), Postgres permite múltiples NULL; en este repo todo lleva
    # organization_id desde bootstrap, así que la práctica es coherente.
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_servicios_org_codigo
        ON servicios (organization_id, codigo)
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_servicios_activo ON servicios (activo)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_servicios_categoria ON servicios (categoria_servicio)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_servicios_nombre ON servicios (nombre)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_servicios_nombre")
    op.execute("DROP INDEX IF EXISTS ix_servicios_categoria")
    op.execute("DROP INDEX IF EXISTS ix_servicios_activo")
    op.execute("DROP INDEX IF EXISTS ux_servicios_org_codigo")
    op.execute("DROP TABLE IF EXISTS servicios")
