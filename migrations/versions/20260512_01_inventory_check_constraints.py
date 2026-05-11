"""CHECK constraints sobre productos y movimientos_stock.

Revision ID: 20260512_01
Revises: 20260510_01
Create Date: 2026-05-12

Capa de defensa en profundidad: los Pydantic ya validan en API, las CHECK
atrapan inserts manuales por psql, bugs futuros, e imports SQL directos.

Pre-flight: aborta si hay filas violatorias preexistentes. Sanear primero.
"""

from alembic import op
from sqlalchemy import text


revision = "20260512_01"
down_revision = "20260510_01"
branch_labels = None
depends_on = None


# Whitelist de referencia_tipo usados por la app (auditado con grep).
_REFERENCIA_TIPO_VALIDOS = (
    "cotizacion",
    "venta",
    "venta_directa",
    "oc",
    "compra_directa",
    "ajuste_manual",
    "manual",
    "stock_inicial",
    "import_csv",
    "put_producto",
)

_TIPO_MOVIMIENTO_VALIDOS = (
    "entrada",
    "salida",
    "ajuste",
    "reserva",
    "liberacion",
)


def _preflight(conn) -> None:
    """Aborta si hay datos que violarían los CHECK."""
    checks = [
        ("productos", "stock_actual < 0", "stock_actual negativo"),
        ("productos", "stock_minimo < 0", "stock_minimo negativo"),
        ("productos", "costo_compra < 0", "costo_compra negativo"),
        ("productos", "precio_publico < 0", "precio_publico negativo"),
        ("productos", "precio_mayorista < 0", "precio_mayorista negativo"),
        ("productos", "precio_distribuidor < 0", "precio_distribuidor negativo"),
        ("movimientos_stock", "cantidad = 0", "cantidad = 0"),
    ]
    problemas = []
    for tabla, expr, label in checks:
        row = conn.execute(text(f"SELECT count(*) FROM {tabla} WHERE {expr}")).first()
        n = int(row[0]) if row else 0
        if n > 0:
            problemas.append(f"  {tabla}: {n} filas con {label}")

    # tipos inválidos
    tipos = ",".join(f"'{t}'" for t in _TIPO_MOVIMIENTO_VALIDOS)
    row = conn.execute(text(
        f"SELECT count(*) FROM movimientos_stock WHERE tipo NOT IN ({tipos})"
    )).first()
    n = int(row[0]) if row else 0
    if n > 0:
        problemas.append(f"  movimientos_stock: {n} filas con tipo fuera de la whitelist")

    refs = ",".join(f"'{r}'" for r in _REFERENCIA_TIPO_VALIDOS)
    row = conn.execute(text(
        f"SELECT count(*) FROM movimientos_stock "
        f"WHERE referencia_tipo IS NOT NULL AND referencia_tipo NOT IN ({refs})"
    )).first()
    n = int(row[0]) if row else 0
    if n > 0:
        problemas.append(f"  movimientos_stock: {n} filas con referencia_tipo desconocido")

    if problemas:
        raise RuntimeError(
            "Migración 20260512_01 aborta por datos violatorios preexistentes. "
            "Sanear antes de aplicar:\n" + "\n".join(problemas)
        )


def upgrade() -> None:
    conn = op.get_bind()
    _preflight(conn)

    # Productos: no-negatividad
    op.execute("ALTER TABLE productos ADD CONSTRAINT ck_productos_stock_actual_ge0 CHECK (stock_actual >= 0)")
    op.execute("ALTER TABLE productos ADD CONSTRAINT ck_productos_stock_minimo_ge0 CHECK (stock_minimo >= 0)")
    op.execute("ALTER TABLE productos ADD CONSTRAINT ck_productos_costo_compra_ge0 CHECK (costo_compra >= 0)")
    op.execute("ALTER TABLE productos ADD CONSTRAINT ck_productos_precio_publico_ge0 CHECK (precio_publico IS NULL OR precio_publico >= 0)")
    op.execute("ALTER TABLE productos ADD CONSTRAINT ck_productos_precio_mayorista_ge0 CHECK (precio_mayorista >= 0)")
    op.execute("ALTER TABLE productos ADD CONSTRAINT ck_productos_precio_distribuidor_ge0 CHECK (precio_distribuidor >= 0)")

    # Movimientos_stock: cantidad != 0 + tipo y referencia_tipo en whitelist
    op.execute("ALTER TABLE movimientos_stock ADD CONSTRAINT ck_mov_cantidad_nonzero CHECK (cantidad <> 0)")

    tipos = ", ".join(f"'{t}'" for t in _TIPO_MOVIMIENTO_VALIDOS)
    op.execute(
        f"ALTER TABLE movimientos_stock ADD CONSTRAINT ck_mov_tipo_valido "
        f"CHECK (tipo IN ({tipos}))"
    )

    refs = ", ".join(f"'{r}'" for r in _REFERENCIA_TIPO_VALIDOS)
    op.execute(
        f"ALTER TABLE movimientos_stock ADD CONSTRAINT ck_mov_referencia_tipo_valido "
        f"CHECK (referencia_tipo IS NULL OR referencia_tipo IN ({refs}))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE productos DROP CONSTRAINT IF EXISTS ck_productos_stock_actual_ge0")
    op.execute("ALTER TABLE productos DROP CONSTRAINT IF EXISTS ck_productos_stock_minimo_ge0")
    op.execute("ALTER TABLE productos DROP CONSTRAINT IF EXISTS ck_productos_costo_compra_ge0")
    op.execute("ALTER TABLE productos DROP CONSTRAINT IF EXISTS ck_productos_precio_publico_ge0")
    op.execute("ALTER TABLE productos DROP CONSTRAINT IF EXISTS ck_productos_precio_mayorista_ge0")
    op.execute("ALTER TABLE productos DROP CONSTRAINT IF EXISTS ck_productos_precio_distribuidor_ge0")
    op.execute("ALTER TABLE movimientos_stock DROP CONSTRAINT IF EXISTS ck_mov_cantidad_nonzero")
    op.execute("ALTER TABLE movimientos_stock DROP CONSTRAINT IF EXISTS ck_mov_tipo_valido")
    op.execute("ALTER TABLE movimientos_stock DROP CONSTRAINT IF EXISTS ck_mov_referencia_tipo_valido")
