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
    # En producción `alembic upgrade head` debería ser el path canónico para
    # el esquema, pero el Procfile de Railway no lo corre y la app necesita
    # bootstrap automático si la DB se dropeó. create_all() es idempotente:
    # CREATE TABLE IF NOT EXISTS por cada modelo. _BACKFILL_DDL en seeds.py
    # cubre columnas/tablas legacy como segundo puente.
    #
    # Override opcional: DASIC_AUTO_CREATE_TABLES=0 para desactivar (solo
    # útil si migras a Alembic puro en deploy y quieres garantizar que
    # create_all no enmascara drift).
    if os.getenv("DASIC_AUTO_CREATE_TABLES", "1").strip().lower() in {"1", "true", "yes", "on"}:
        try:
            models.Base.metadata.create_all(bind=engine)
            logger.info("Tables OK (create_all idempotente al boot).")
        except Exception as exc:
            logger.error("Error en create_all: %s", exc, exc_info=True)
            raise
    else:
        logger.info(
            "create_all desactivado vía env. Usa 'alembic upgrade head' "
            "para schema; seeds.py corre DDL backfill idempotente como puente."
        )

    # 2. Seeds y backfill
    db = SessionLocal()
    try:
        run_all_seeds(db)

        # 3. Ingesta de datos de context/ — SOLO en bootstrap inicial (DB sin
        #    clientes). NO es idempotente como se creía: su dedup es por EMAIL,
        #    así que cuando una empresa se fusiona/renombra y desaparece ese
        #    email, el siguiente deploy la RE-CREA como duplicado (caso real:
        #    Vitracoat/auxcompras3 reaparecía id8→id9→id10 en cada deploy,
        #    fragmentando el historial del cliente). Con datos reales ya
        #    presentes, jamás se re-siembra. Para forzar desactivado: env
        #    SEED_CONTEXT_DISABLED=1.
        if os.getenv("SEED_CONTEXT_DISABLED", "").strip() != "1":
            try:
                n_clientes = db.query(models.Cliente).count()
                if n_clientes == 0:
                    from scripts.import_context_data import run_seed
                    resultado = run_seed(db, dry_run=False)
                    logger.info("Seed context/ (bootstrap) OK → %s", resultado)
                else:
                    logger.info(
                        "Seed context/ OMITIDO: la DB ya tiene %d cliente(s) "
                        "(no es bootstrap inicial; evita recrear duplicados).",
                        n_clientes,
                    )
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
