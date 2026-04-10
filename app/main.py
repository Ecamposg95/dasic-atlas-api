from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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

# 1. Inicializar Base de Datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DASIC ERP", version="2.0.0")

# 2. Configuración de Archivos Estáticos y Plantillas
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 3. Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. CONEXIÓN DE CEREBROS (API ENDPOINTS) ---
app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(ventas.router)
app.include_router(clientes.router)
app.include_router(compras.router)
app.include_router(usuarios.router)
app.include_router(gastos.router)

# --- 5. RUTAS VISUALES (FRONTEND) ---

# Acceso
@app.get("/", response_class=HTMLResponse)
async def view_login(request: Request):
    return templates.TemplateResponse(request, "login.html")

# Panel Principal
@app.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

# Operación Comercial
@app.get("/ventas/cotizador", response_class=HTMLResponse)
async def view_cotizador(request: Request):
    return templates.TemplateResponse(request, "cotizador.html")

@app.get("/seguimiento", response_class=HTMLResponse)
async def view_seguimiento(request: Request):
    return templates.TemplateResponse(request, "seguimiento.html")

# Gestión de Recursos
@app.get("/inventario", response_class=HTMLResponse)
async def view_inventario(request: Request):
    return templates.TemplateResponse(request, "inventario.html")

@app.get("/clientes", response_class=HTMLResponse)
async def view_clientes(request: Request):
    return templates.TemplateResponse(request, "clientes.html")

@app.get("/compras", response_class=HTMLResponse)
async def view_compras(request: Request):
    return templates.TemplateResponse(request, "compras.html")

# Administración y Finanzas
@app.get("/gastos", response_class=HTMLResponse)
async def view_gastos(request: Request):
    return templates.TemplateResponse(request, "gastos.html")

@app.get("/reportes", response_class=HTMLResponse)
async def view_reportes(request: Request):
    return templates.TemplateResponse(request, "reportes.html")

@app.get("/usuarios", response_class=HTMLResponse)
async def view_usuarios(request: Request):
    return templates.TemplateResponse(request, "usuarios.html")


# --- 6. EVENTO DE ARRANQUE (SEEDING) ---
@app.on_event("startup")
def startup_db_check():
    db = SessionLocal()
    try:
        # Transitional schema upgrades for legacy databases (without Alembic yet).
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

        org = db.query(models.Organization).first()
        if not org:
            org = models.Organization(name="DASIC Industrial", industry_type="DASIC_INDUSTRIAL")
            db.add(org)
            db.commit()
            db.refresh(org)
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

        # Si no hay usuarios, crea el Super Admin
        if not db.query(models.Usuario).first():
            print("--- INICIALIZANDO SISTEMA DASIC ERP ---")
            print("Creando usuario Administrador Maestro...")
            
            admin = UsuarioCreate(
                nombre="Administrador Principal",
                email="admin@dasic.com",
                password="admin123", 
                rol=models.RolUsuario.ADMIN,
                activo=True
            )
            UserService.create_user(db, admin)
            print(">> CREADO: admin@dasic.com / admin123")
            print("---------------------------------------")
        else:
            print("--- SISTEMA DASIC ONLINE ---")

        # Ensure every active user has at least one active membership.
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

        # Backfill pilot tables for existing records.
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
    finally:
        db.close()
