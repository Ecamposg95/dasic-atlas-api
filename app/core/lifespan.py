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

    # 1. Crear tablas que no existan.
    #
    # En producción `alembic upgrade head` debe ser el path canónico para el
    # esquema. create_all() salta migraciones y puede dejar drift entre el
    # modelo SQLAlchemy y lo que vive en BD (ej. CHECK constraints, índices,
    # políticas ON DELETE no se aplican).
    #
    # Mantenemos create_all detrás de un flag opt-in para dev/test rápido
    # (DB local recién creada). En prod el flag NO debería estar prendido;
    # el _BACKFILL_DDL idempotente de seeds.py cubre columnas/tablas nuevas
    # como puente.
    if os.getenv("DASIC_AUTO_CREATE_TABLES", "0").strip().lower() in {"1", "true", "yes", "on"}:
        try:
            models.Base.metadata.create_all(bind=engine)
            logger.info("Tables OK (create_all ejecutado vía DASIC_AUTO_CREATE_TABLES=1).")
        except Exception as exc:
            logger.error("Error en create_all: %s", exc, exc_info=True)
            raise
    else:
        logger.info(
            "create_all desactivado (default). Usa 'alembic upgrade head' "
            "para schema; seeds.py corre DDL backfill idempotente como puente."
        )

    # 2. Seeds y backfill
    db = SessionLocal()
    try:
        run_all_seeds(db)

        # 3. Ingesta de datos de context/ — siempre al startup. Idempotente:
        #    no duplica registros existentes (match por SKU / email / folio).
        #    Para desactivar setear env var SEED_CONTEXT_DISABLED=1.
        if os.getenv("SEED_CONTEXT_DISABLED", "").strip() != "1":
            try:
                from scripts.import_context_data import run_seed
                resultado = run_seed(db, dry_run=False)
                logger.info("Seed context/ OK → %s", resultado)
            except Exception as exc:
                logger.error("Seed context/ FALLÓ (no bloqueante): %s", exc, exc_info=True)
    except Exception as exc:
        logger.error("Error en startup seeds: %s", exc, exc_info=True)
        raise
    finally:
        db.close()

    yield  # La app corre aquí

    # Shutdown
    logger.info("DASIC ERP apagado.")
