"""
Database seeding.

Single-tenant: solo crea el usuario administrador inicial si la tabla está vacía.
"""

import logging

from sqlalchemy.orm import Session

from app import models
from app.schemas import UsuarioCreate
from app.services import UserService

logger = logging.getLogger(__name__)


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
    seed_super_admin(db)
    logger.info("Startup completado correctamente.")
