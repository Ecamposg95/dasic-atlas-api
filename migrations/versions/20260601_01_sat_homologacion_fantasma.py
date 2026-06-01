"""sat_homologacion_fantasma — homologa fantasma con producto (marca + SAT + obs)
y agrega snapshot SAT a la línea de cotización para PDFs.

Todas las columnas son NULL → filas existentes intactas. marca_id usa
ON DELETE SET NULL para que borrar una marca no rompa fantasmas.

Revision ID: 20260601_01
Revises: 20260526_01
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20260601_01"
down_revision = "20260526_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # productos_fantasma: homologación con producto
    op.add_column("productos_fantasma", sa.Column("marca", sa.String(80), nullable=True))
    op.add_column("productos_fantasma", sa.Column("marca_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_productos_fantasma_marca_id", "productos_fantasma", "marcas",
        ["marca_id"], ["id"], ondelete="SET NULL",
    )
    op.add_column("productos_fantasma", sa.Column("clave_prod_serv", sa.String(8), nullable=True))
    op.add_column("productos_fantasma", sa.Column("clave_unidad_sat", sa.String(10), nullable=True))
    op.add_column("productos_fantasma", sa.Column("observaciones", sa.Text(), nullable=True))
    # detalles_orden: snapshot SAT por línea (para PDFs estables)
    op.add_column("detalles_orden", sa.Column("clave_prod_serv", sa.String(8), nullable=True))
    op.add_column("detalles_orden", sa.Column("clave_unidad_sat", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("detalles_orden", "clave_unidad_sat")
    op.drop_column("detalles_orden", "clave_prod_serv")
    op.drop_column("productos_fantasma", "observaciones")
    op.drop_column("productos_fantasma", "clave_unidad_sat")
    op.drop_column("productos_fantasma", "clave_prod_serv")
    op.drop_constraint("fk_productos_fantasma_marca_id", "productos_fantasma", type_="foreignkey")
    op.drop_column("productos_fantasma", "marca_id")
    op.drop_column("productos_fantasma", "marca")
