"""
DASIC ERP — Application entry point.
Bootstrap limpio: logging, lifespan, middlewares, routers y vistas SSR.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from jose import JWTError, jwt
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.lifespan import lifespan
from app.db import SessionLocal, engine
from app import models
from app.services import UserService

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Tablas: create_all se ejecuta en lifespan (core/lifespan.py) no aquí.
# Aquí solo importamos engine para que el pool se configure.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DASIC ERP",
    version="2.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Static & Templates
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------------------------------------------------------------------------
# Proxy headers (Railway/Render/etc) — para que url_for genere https://
# detrás del load balancer. Tomado de uvicorn (incluido por defecto).
# ---------------------------------------------------------------------------
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_raw = os.getenv("ALLOWED_ORIGINS", "")
origins = [o for o in _raw.split(",") if o] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers API
# ---------------------------------------------------------------------------
from app.routers import (  # noqa: E402
    admin, auth, clientes, compras, dashboard, fx, gastos,
    inventario, productos, usuarios, ventas,
)

app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(ventas.router)
app.include_router(clientes.router)
app.include_router(compras.router)
app.include_router(usuarios.router)
app.include_router(gastos.router)
app.include_router(dashboard.router)
app.include_router(fx.router)
app.include_router(inventario.router)
app.include_router(admin.router)

# ---------------------------------------------------------------------------
# Helper: obtener current_user opcional desde cookie (para SSR)
# ---------------------------------------------------------------------------
def _get_user_from_cookie(request: Request) -> Optional[models.Usuario]:
    """Decodifica el JWT de la cookie HttpOnly sin lanzar excepción."""
    try:
        raw = request.cookies.get(settings.token_cookie_name, "")
        token = raw.replace("Bearer ", "", 1) if raw.startswith("Bearer ") else raw
        if not token:
            return None
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email: str = payload.get("sub", "")
        if not email:
            return None
        db = SessionLocal()
        try:
            return UserService.get_user_by_email(db, email)
        finally:
            db.close()
    except (JWTError, Exception):
        return None


def _protected_view(template_name: str):
    """
    Fábrica de vistas SSR protegidas.
    - Si no hay sesión válida → redirect /
    - Si hay sesión → renderiza template con request + current_user
    """
    async def _view(request: Request) -> HTMLResponse:
        user = _get_user_from_cookie(request)
        if user is None:
            return RedirectResponse("/", status_code=302)
        return templates.TemplateResponse(
            request,
            template_name,
            context={"request": request, "current_user": user},
        )
    _view.__name__ = f"view_{template_name.replace('.html','').replace('/','_')}"
    return _view


# ---------------------------------------------------------------------------
# SSR Routes
# ---------------------------------------------------------------------------

# Login (pública)
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def view_login(request: Request) -> HTMLResponse:
    # Si ya está autenticado → dashboard directamente
    if _get_user_from_cookie(request):
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html", context={"request": request})


# Rutas protegidas
_SSR_ROUTES = [
    ("/dashboard",          "dashboard.html"),
    ("/ventas/cotizador",   "cotizador.html"),
    ("/seguimiento",        "seguimiento.html"),
    ("/inventario",         "inventario.html"),
    ("/clientes",           "clientes.html"),
    ("/compras",            "compras.html"),
    ("/gastos",             "gastos.html"),
    ("/reportes",           "reportes.html"),
    ("/usuarios",           "usuarios.html"),
]

for _path, _tmpl in _SSR_ROUTES:
    app.add_api_route(
        _path,
        _protected_view(_tmpl),
        response_class=HTMLResponse,
        include_in_schema=False,
    )

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Ops"])
async def health_check() -> JSONResponse:
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False
    status_str = "ok" if db_ok else "degraded"
    return JSONResponse({"status": status_str, "db": "ok" if db_ok else "error"},
                        status_code=200 if db_ok else 503)
