"""10 tablas de catálogos SAT chicos (CFDI 4.0).

Revision ID: 20260514_01
Revises: 20260515_03
Create Date: 2026-05-14

Tablas pequeñas (≤ 200 entries) que se siembran desde Python al arranque.
Los catálogos masivos (sat_clave_prodserv, sat_clave_unidad) viven en una
migración aparte (Fase C) por usar pg_trgm.
"""

from alembic import op


revision = "20260514_01"
down_revision = "20260515_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_forma_pago (
            codigo VARCHAR(3) PRIMARY KEY,
            descripcion TEXT NOT NULL,
            activo BOOLEAN NOT NULL DEFAULT true,
            vigencia_desde DATE,
            vigencia_hasta DATE,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_forma_pago_activo ON sat_forma_pago(activo)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_metodo_pago (
            codigo VARCHAR(3) PRIMARY KEY,
            descripcion TEXT NOT NULL,
            activo BOOLEAN NOT NULL DEFAULT true,
            vigencia_desde DATE,
            vigencia_hasta DATE,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_metodo_pago_activo ON sat_metodo_pago(activo)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_uso_cfdi (
            codigo VARCHAR(5) PRIMARY KEY,
            descripcion TEXT NOT NULL,
            activo BOOLEAN NOT NULL DEFAULT true,
            vigencia_desde DATE,
            vigencia_hasta DATE,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_uso_cfdi_activo ON sat_uso_cfdi(activo)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_regimen_fiscal (
            codigo VARCHAR(3) PRIMARY KEY,
            descripcion TEXT NOT NULL,
            aplica_persona_fisica BOOLEAN NOT NULL DEFAULT false,
            aplica_persona_moral BOOLEAN NOT NULL DEFAULT false,
            activo BOOLEAN NOT NULL DEFAULT true,
            vigencia_desde DATE,
            vigencia_hasta DATE,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_regimen_fiscal_activo ON sat_regimen_fiscal(activo)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_objeto_imp (
            codigo VARCHAR(2) PRIMARY KEY,
            descripcion TEXT NOT NULL,
            activo BOOLEAN NOT NULL DEFAULT true,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_objeto_imp_activo ON sat_objeto_imp(activo)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_impuesto (
            codigo VARCHAR(3) PRIMARY KEY,
            descripcion TEXT NOT NULL,
            aplica_traslado BOOLEAN NOT NULL DEFAULT false,
            aplica_retencion BOOLEAN NOT NULL DEFAULT false,
            activo BOOLEAN NOT NULL DEFAULT true,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_impuesto_activo ON sat_impuesto(activo)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_tipo_factor (
            codigo VARCHAR(10) PRIMARY KEY,
            descripcion TEXT NOT NULL,
            activo BOOLEAN NOT NULL DEFAULT true,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_tipo_factor_activo ON sat_tipo_factor(activo)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_tasa_o_cuota (
            id_local VARCHAR(30) PRIMARY KEY,
            impuesto VARCHAR(3) NOT NULL,
            tipo_factor VARCHAR(10) NOT NULL,
            valor NUMERIC(7,6) NOT NULL,
            descripcion TEXT NOT NULL,
            es_retencion BOOLEAN NOT NULL DEFAULT false,
            activo BOOLEAN NOT NULL DEFAULT true,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_tasa_impuesto ON sat_tasa_o_cuota(impuesto)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_tasa_es_retencion ON sat_tasa_o_cuota(es_retencion)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_moneda (
            codigo VARCHAR(3) PRIMARY KEY,
            descripcion TEXT NOT NULL,
            decimales VARCHAR(2) NOT NULL DEFAULT '2',
            activo BOOLEAN NOT NULL DEFAULT true,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_moneda_activo ON sat_moneda(activo)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sat_tipo_comprobante (
            codigo VARCHAR(2) PRIMARY KEY,
            descripcion TEXT NOT NULL,
            activo BOOLEAN NOT NULL DEFAULT true,
            creado_en TIMESTAMPTZ DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sat_tipo_comprobante_activo ON sat_tipo_comprobante(activo)")


def downgrade() -> None:
    for tbl in [
        "sat_tipo_comprobante", "sat_moneda", "sat_tasa_o_cuota", "sat_tipo_factor",
        "sat_impuesto", "sat_objeto_imp", "sat_regimen_fiscal",
        "sat_uso_cfdi", "sat_metodo_pago", "sat_forma_pago",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {tbl}")
