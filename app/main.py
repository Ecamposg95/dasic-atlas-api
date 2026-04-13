import logging
import logging.config
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db import SessionLocal, engine
from app import models
from app.services import UserService
from app.schemas import UsuarioCreate

# --- IMPORTACIÓN DE TODOS LOS MÓDULOS (ROUTERS) ---
from app.routers import auth, clientes, compras, gastos, productos, usuarios, ventas

# ---------------------------------------------------------------------------
# LOGGING ESTRUCTURADO
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured",
            }
        },
        "root": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
        },
    }
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. INICIALIZAR BASE DE DATOS (tablas no gestionadas aún por Alembic)
# ---------------------------------------------------------------------------
models.Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# 2. APP
# ---------------------------------------------------------------------------
app = FastAPI(title="DASIC ERP", version="2.0.0")

# 3. Configuración de Archivos Estáticos y Plantillas
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 4. Configuración CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
# En desarrollo permitir todos; en producción se deben listar explícitamente.
origins = ALLOWED_ORIGINS if any(ALLOWED_ORIGINS) else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# 5. ROUTERS
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(ventas.router)
app.include_router(clientes.router)
app.include_router(compras.router)
app.include_router(usuarios.router)
app.include_router(gastos.router)

# ---------------------------------------------------------------------------
# 6. RUTAS VISUALES (FRONTEND SSR)
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def view_login(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/ventas/cotizador", response_class=HTMLResponse)
async def view_cotizador(request: Request):
    return templates.TemplateResponse(request, "cotizador.html")


@app.get("/seguimiento", response_class=HTMLResponse)
async def view_seguimiento(request: Request):
    return templates.TemplateResponse(request, "seguimiento.html")


@app.get("/inventario", response_class=HTMLResponse)
async def view_inventario(request: Request):
    return templates.TemplateResponse(request, "inventario.html")


@app.get("/clientes", response_class=HTMLResponse)
async def view_clientes(request: Request):
    return templates.TemplateResponse(request, "clientes.html")


@app.get("/compras", response_class=HTMLResponse)
async def view_compras(request: Request):
    return templates.TemplateResponse(request, "compras.html")


@app.get("/gastos", response_class=HTMLResponse)
async def view_gastos(request: Request):
    return templates.TemplateResponse(request, "gastos.html")


@app.get("/reportes", response_class=HTMLResponse)
async def view_reportes(request: Request):
    return templates.TemplateResponse(request, "reportes.html")


@app.get("/usuarios", response_class=HTMLResponse)
async def view_usuarios(request: Request):
    return templates.TemplateResponse(request, "usuarios.html")


# ---------------------------------------------------------------------------
# 7. HEALTH CHECK  (Railway lo usa para saber si el servicio está vivo)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Ops"])
async def health_check():
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


# ---------------------------------------------------------------------------
# 8. EVENTO DE ARRANQUE (SEEDING)
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup_db_check():
    db = SessionLocal()
    try:
        # ----------------------------------------------------------------
        # Retrocompatibilidad: columnas de multi-tenancy para tablas legacy
        # (se eliminará cuando Alembic controle el esquema completo)
        # ----------------------------------------------------------------
        ddl_statements = [
            "ALTER TABLE IF EXISTS clientes ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
            "ALTER TABLE IF EXISTS transacciones_clientes ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
            "ALTER TABLE IF EXISTS ordenes_venta ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
            "ALTER TABLE IF EXISTS detalles_orden ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36)",
            "CREATE INDEX IF NOT EXISTS ix_clientes_organization_id ON clientes (organization_id)",
            "CREATE INDEX IF NOT EXISTS ix_transacciones_clientes_organization_id ON transacciones_clientes (organization_id)",
            "CREATE INDEX IF NOT EXISTS ix_ordenes_venta_organization_id ON ordenes_venta (organization_id)",
            "CREATE INDEX IF NOT EXISTS ix_detalles_orden_organization_id ON detalles_orden (organization_id)",
        ]
        for statement in ddl_statements:
            db.execute(text(statement))
        db.commit()

        # ---- Tenant base ----
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

        # ---- Super Admin inicial ----
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

        # ---- Asegurar membresías ----
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

        # ---- Backfill organization_id en registros legacy ----
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
        logger.info("Startup completado correctamente.")
    except Exception as exc:
        logger.error("Error en startup: %s", exc, exc_info=True)
        raise
    finally:
        db.close()
