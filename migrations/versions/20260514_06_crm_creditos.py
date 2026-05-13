"""CRM: campos de crédito en Cliente + cuentas por cobrar formal en transacciones.

Revision ID: 20260514_06
Revises: 20260514_05
Create Date: 2026-05-14

Cliente:
  + limite_credito NUMERIC(12,2) DEFAULT 0
  + dias_credito INT DEFAULT 0
  + dia_corte INT NULL  (1-28, día del mes; opcional)
  + moneda_credito VARCHAR(3) DEFAULT 'MXN'

TransaccionCliente:
  + orden_venta_id INT FK a ordenes_venta  (formal; reemplaza referencia_id
                                            laxo cuando origen = venta)
  + fecha_vencimiento DATE
  + estatus_pago VARCHAR(20) DEFAULT 'pendiente'  (pendiente|parcial|pagado|vencido)
  + monto_pagado NUMERIC(12,2) DEFAULT 0
"""

from alembic import op


revision = "20260514_06"
down_revision = "20260514_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cliente: campos de crédito
    op.execute("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS limite_credito NUMERIC(12,2) NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS dias_credito INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS dia_corte INTEGER")
    op.execute("ALTER TABLE clientes ADD COLUMN IF NOT EXISTS moneda_credito VARCHAR(3) NOT NULL DEFAULT 'MXN'")

    # TransaccionCliente: pagos formales por venta
    op.execute(
        "ALTER TABLE transacciones_clientes ADD COLUMN IF NOT EXISTS "
        "orden_venta_id INTEGER REFERENCES ordenes_venta(id) ON DELETE SET NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tx_cli_orden_venta ON transacciones_clientes (orden_venta_id)"
    )
    op.execute("ALTER TABLE transacciones_clientes ADD COLUMN IF NOT EXISTS fecha_vencimiento DATE")
    op.execute(
        "ALTER TABLE transacciones_clientes ADD COLUMN IF NOT EXISTS "
        "estatus_pago VARCHAR(20) NOT NULL DEFAULT 'pendiente'"
    )
    op.execute(
        "ALTER TABLE transacciones_clientes ADD COLUMN IF NOT EXISTS "
        "monto_pagado NUMERIC(12,2) NOT NULL DEFAULT 0"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tx_cli_estatus_pago ON transacciones_clientes (estatus_pago)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tx_cli_estatus_pago")
    op.execute("ALTER TABLE transacciones_clientes DROP COLUMN IF EXISTS monto_pagado")
    op.execute("ALTER TABLE transacciones_clientes DROP COLUMN IF EXISTS estatus_pago")
    op.execute("ALTER TABLE transacciones_clientes DROP COLUMN IF EXISTS fecha_vencimiento")
    op.execute("DROP INDEX IF EXISTS ix_tx_cli_orden_venta")
    op.execute("ALTER TABLE transacciones_clientes DROP COLUMN IF EXISTS orden_venta_id")
    op.execute("ALTER TABLE clientes DROP COLUMN IF EXISTS moneda_credito")
    op.execute("ALTER TABLE clientes DROP COLUMN IF EXISTS dia_corte")
    op.execute("ALTER TABLE clientes DROP COLUMN IF EXISTS dias_credito")
    op.execute("ALTER TABLE clientes DROP COLUMN IF EXISTS limite_credito")
