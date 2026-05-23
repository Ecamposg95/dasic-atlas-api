"""reportes_servicio — acta de servicio ejecutado

Tabla análoga a `remisiones` pero para documentar la ejecución de líneas
de tipo servicio (vs. entrega física de productos). Cada OrdenVenta con
al menos 1 línea `tipo_linea = 'servicio_catalogo'` puede generar 1+
Reportes de Servicio.

Revision ID: 20260525_01
Revises: 20260524_01
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa


revision = "20260525_01"
down_revision = "20260524_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reportes_servicio",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("folio", sa.String(40), nullable=True),
        sa.Column("orden_venta_id", sa.Integer(), sa.ForeignKey("ordenes_venta.id"), nullable=False),
        sa.Column("fecha_reporte", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tecnico_nombre", sa.String(150), nullable=True),
        sa.Column("cliente_recibe_nombre", sa.String(150), nullable=True),
        sa.Column("recibido_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("creado_por_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("folio"),
    )
    op.create_index("ix_reportes_servicio_orden_venta_id", "reportes_servicio", ["orden_venta_id"])
    op.create_index("ix_reportes_servicio_folio", "reportes_servicio", ["folio"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_reportes_servicio_folio", table_name="reportes_servicio")
    op.drop_index("ix_reportes_servicio_orden_venta_id", table_name="reportes_servicio")
    op.drop_table("reportes_servicio")
