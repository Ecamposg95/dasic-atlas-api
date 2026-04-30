"""
Application lifespan (FastAPI modern pattern).

Reemplaza el deprecado @app.on_event("startup") / ("shutdown").
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import SessionLocal
from app.db.seeds import run_all_seeds

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    Startup: crea tablas (transitorio) y corre seeds / DDL backfill.
    Shutdown: extensible para cerrar conexiones, caches, etc.
    """
    # Imports locales para evitar circulares al nivel de módulo
    from app.db import engine
    from app import models

    # 1. Crear tablas que no existan (transitorio — Fase 6: migrar a Alembic)
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Tables OK (create_all ejecutado).")
    except Exception as exc:
        logger.error("Error en create_all: %s", exc, exc_info=True)
        raise

    # 2. Seeds y backfill
    db = SessionLocal()
    try:
        run_all_seeds(db)

        # 3. Opcional: ingesta inicial de context/ (productos/clientes/etc.).
        #    Activar con env var SEED_CONTEXT_ON_STARTUP=1. Idempotente.
        if os.getenv("SEED_CONTEXT_ON_STARTUP", "").strip() == "1":
            try:
                from scripts.import_context_data import run_seed
                resultado = run_seed(db, dry_run=False)
                logger.info("SEED_CONTEXT_ON_STARTUP resultado: %s", resultado)
            except Exception as exc:
                logger.warning("Seed de context/ falló (no bloqueante): %s", exc, exc_info=True)
    except Exception as exc:
        logger.error("Error en startup seeds: %s", exc, exc_info=True)
        raise
    finally:
        db.close()

    yield  # La app corre aquí

    # Shutdown
    logger.info("DASIC ERP apagado.")
