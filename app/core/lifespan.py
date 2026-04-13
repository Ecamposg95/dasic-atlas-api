"""
Application lifespan (FastAPI modern pattern).

Reemplaza el deprecado @app.on_event("startup") / ("shutdown").
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import SessionLocal
from app.db.seeds import run_all_seeds

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    Startup: corre seeds / DDL backfill.
    Shutdown: (extensible para cerrar conexiones, caches, etc.)
    """
    db = SessionLocal()
    try:
        run_all_seeds(db)
    except Exception as exc:
        logger.error("Error en startup: %s", exc, exc_info=True)
        raise
    finally:
        db.close()

    yield  # ← La app corre aquí

    # Shutdown hooks (agregar cuando sea necesario)
    logger.info("DASIC ERP apagado.")
