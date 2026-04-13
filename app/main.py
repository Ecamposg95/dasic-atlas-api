"""
DASIC ERP — Application entry point.

Este archivo solo hace bootstrap: configura logging, monta la app,
registra middleware y routers.
La lógica de startup/seeding vive en core/lifespan.py + db/seeds.py.
"""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.logging import configure_logging
from app.core.lifespan import lifespan
from app.db import SessionLocal, engine
from app import models

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging()

import logging
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Inicializar tablas (no gestionadas aún por Alembic)
# ---------------------------------------------------------------------------
models.Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DASIC ERP",
    version="2.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Static files & templates
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
origins = [o for o in _raw_origins.split(",") if o] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers (API)
# ---------------------------------------------------------------------------
from app.routers import auth, clientes, compras, gastos, productos, usuarios, ventas  # noqa: E402

app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(ventas.router)
app.include_router(clientes.router)
app.include_router(compras.router)
app.include_router(usuarios.router)
app.include_router(gastos.router)

# ---------------------------------------------------------------------------
# SSR Views (Jinja2)
# ---------------------------------------------------------------------------
_SSR_ROUTES: list[tuple[str, str]] = [
    ("/", "login.html"),
    ("/dashboard", "dashboard.html"),
    ("/ventas/cotizador", "cotizador.html"),
    ("/seguimiento", "seguimiento.html"),
    ("/inventario", "inventario.html"),
    ("/clientes", "clientes.html"),
    ("/compras", "compras.html"),
    ("/gastos", "gastos.html"),
    ("/reportes", "reportes.html"),
    ("/usuarios", "usuarios.html"),
]

for _path, _template in _SSR_ROUTES:
    # Closure captura el template correcto
    def _make_view(tmpl: str):
        async def _view(request: Request) -> HTMLResponse:
            return templates.TemplateResponse(request, tmpl)
        _view.__name__ = f"view_{tmpl.replace('.html', '').replace('/', '_')}"
        return _view

    app.add_api_route(_path, _make_view(_template), response_class=HTMLResponse)

# ---------------------------------------------------------------------------
# Health check  (Railway / monitoreo externo)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Ops"])
async def health_check() -> JSONResponse:
    """Endpoint de salud para Railway y monitoreo externo."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "ok"
    except Exception as exc:  # noqa: BLE001
        logger.error("Health check DB falló: %s", exc)
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"
    code = 200 if status == "ok" else 503
    return JSONResponse({"status": status, "db": db_status}, status_code=code)
