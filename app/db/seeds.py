"""
Database seeding.

Single-tenant: solo crea el usuario administrador inicial si la tabla está vacía.

También aplica DDL idempotente para columnas/tablas nuevas, como puente
entre instancias en producción que arrancan sin correr `alembic upgrade head`
(el Procfile sólo levanta uvicorn). Las migraciones siguen siendo la
fuente de verdad para entornos limpios.
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.schemas import UsuarioCreate
from app.services import UserService

logger = logging.getLogger(__name__)


# DDL idempotente: cada sentencia debe ser segura de re-ejecutar.
# Solo agregar entradas para cambios que YA viven en migrations/versions/.
_BACKFILL_DDL = [
    # 20260430_01: cotizador robusto
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS proveedor_principal_id INTEGER REFERENCES proveedores(id)",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS proveedor_alterno_id INTEGER REFERENCES proveedores(id)",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS tiempo_entrega_dias INTEGER NOT NULL DEFAULT 7",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS es_servicio BOOLEAN NOT NULL DEFAULT false",
    "CREATE INDEX IF NOT EXISTS ix_productos_proveedor_principal_id ON productos (proveedor_principal_id)",
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS tipo_linea VARCHAR(20) NOT NULL DEFAULT 'producto_catalogo'",
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS proveedor_sugerido_id INTEGER REFERENCES proveedores(id)",
    # 20260429_02: marca + unidad
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS marca VARCHAR(80)",
    "ALTER TABLE IF EXISTS productos ADD COLUMN IF NOT EXISTS unidad VARCHAR(20) DEFAULT 'PZA'",
    "CREATE INDEX IF NOT EXISTS ix_productos_marca ON productos (marca)",
    # 20260430_02: RBAC owner scoping para clientes
    "ALTER TABLE IF EXISTS clientes ADD COLUMN IF NOT EXISTS creado_por_id INTEGER REFERENCES usuarios(id)",
    "CREATE INDEX IF NOT EXISTS ix_clientes_creado_por_id ON clientes (creado_por_id)",
    # 20260430_03 (no migration formal): gastos.moneda
    "ALTER TABLE IF EXISTS gastos ADD COLUMN IF NOT EXISTS moneda VARCHAR(3) NOT NULL DEFAULT 'MXN'",
]


def run_backfill_ddl(db: Session) -> None:
    """Ejecuta DDL idempotente para columnas nuevas. Tolera errores individuales."""
    for stmt in _BACKFILL_DDL:
        try:
            db.execute(text(stmt))
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Backfill DDL skip (%s): %s", stmt[:80], exc)


def seed_super_admin(db: Session) -> None:
    """Crea el usuario administrador inicial si no existe ningún usuario."""
    if db.query(models.Usuario).first():
        logger.info("DASIC ERP online")
        return

    logger.info("Inicializando sistema DASIC ERP — creando administrador...")
    admin = UsuarioCreate(
        nombre="Administrador Principal",
        email="admin@dasic.com",
        password="admin123",
        rol=models.RolUsuario.ADMIN,
        activo=True,
    )
    UserService.create_user(db, admin)
    logger.info("Admin creado: admin@dasic.com / admin123")


def run_all_seeds(db: Session) -> None:
    """Punto de entrada único para tareas de startup."""
    run_backfill_ddl(db)
    seed_super_admin(db)
    logger.info("Startup completado correctamente.")
