"""
Database seeding and startup DDL backfill.

Separado de main.py para mantenerlo limpio.
TODO (Fase 6): migrar el DDL backfill a migraciones Alembic formales.
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.schemas import UsuarioCreate
from app.services import UserService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DDL Backfill (retrocompatibilidad pre-Alembic)
# ---------------------------------------------------------------------------
_BACKFILL_DDL = [
    "ALTER TABLE IF EXISTS clientes ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
    "ALTER TABLE IF EXISTS transacciones_clientes ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
    "ALTER TABLE IF EXISTS ordenes_venta ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
    "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
    "CREATE INDEX IF NOT EXISTS ix_clientes_organization_id ON clientes (organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_transacciones_clientes_organization_id ON transacciones_clientes (organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_ordenes_venta_organization_id ON ordenes_venta (organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_detalles_orden_organization_id ON detalles_orden (organization_id)",
]


def run_backfill_ddl(db: Session) -> None:
    """Aplica columnas/índices legacy que aún no están en Alembic."""
    for stmt in _BACKFILL_DDL:
        db.execute(text(stmt))
    db.commit()
    logger.debug("DDL backfill completado.")


def seed_base_tenant(db: Session) -> tuple[models.Organization, models.Branch]:
    """Garantiza que exista la organización base y su HQ branch."""
    org = db.query(models.Organization).first()
    if not org:
        org = models.Organization(name="DASIC Industrial", industry_type="DASIC_INDUSTRIAL")
        db.add(org)
        db.commit()
        db.refresh(org)
        logger.info("Organización base creada: %s", org.id)

    hq_branch = (
        db.query(models.Branch)
        .filter(
            models.Branch.organization_id == org.id,
            models.Branch.branch_type == models.BranchType.HQ,
        )
        .first()
    )
    if not hq_branch:
        hq_branch = models.Branch(
            organization_id=org.id,
            name="HQ",
            branch_type=models.BranchType.HQ,
        )
        db.add(hq_branch)
        db.commit()
        db.refresh(hq_branch)
        logger.info("HQ Branch creada: %s", hq_branch.id)

    return org, hq_branch


def seed_super_admin(db: Session) -> None:
    """Crea el usuario administrador inicial si no existe ningún usuario."""
    if not db.query(models.Usuario).first():
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
    else:
        logger.info("DASIC ERP online")


def ensure_memberships(
    db: Session,
    org: models.Organization,
    hq_branch: models.Branch,
) -> None:
    """Asegura que todos los usuarios tengan membresía en la organización base."""
    users = db.query(models.Usuario).all()
    for user in users:
        membership = (
            db.query(models.UserOrganization)
            .filter(
                models.UserOrganization.user_id == user.id,
                models.UserOrganization.organization_id == org.id,
            )
            .first()
        )
        if not membership:
            db.add(
                models.UserOrganization(
                    user_id=user.id,
                    organization_id=org.id,
                    branch_id=hq_branch.id,
                    is_active=True,
                )
            )
    db.commit()


def backfill_organization_ids(db: Session, org: models.Organization) -> None:
    """Retroactivamente asigna organization_id a registros legacy (sin org)."""
    db.query(models.Cliente).filter(models.Cliente.organization_id.is_(None)).update(
        {models.Cliente.organization_id: org.id}, synchronize_session=False
    )
    db.query(models.TransaccionCliente).filter(
        models.TransaccionCliente.organization_id.is_(None)
    ).update({models.TransaccionCliente.organization_id: org.id}, synchronize_session=False)
    db.query(models.OrdenVenta).filter(models.OrdenVenta.organization_id.is_(None)).update(
        {models.OrdenVenta.organization_id: org.id}, synchronize_session=False
    )
    db.query(models.DetalleOrden).filter(models.DetalleOrden.organization_id.is_(None)).update(
        {models.DetalleOrden.organization_id: org.id}, synchronize_session=False
    )
    db.commit()
    logger.debug("Backfill de organization_id completado.")


def run_all_seeds(db: Session) -> None:
    """Punto de entrada único para todas las tareas de startup."""
    run_backfill_ddl(db)
    org, hq_branch = seed_base_tenant(db)
    seed_super_admin(db)
    ensure_memberships(db, org, hq_branch)
    backfill_organization_ids(db, org)
    logger.info("Startup completado correctamente.")
