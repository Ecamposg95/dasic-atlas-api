from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
import models
import services
from schemas import UsuarioCreate, RolUsuario

# --- IMPORTACIÓN DE TODOS LOS MÓDULOS (ROUTERS) ---
from routers import (
    auth, 
    productos, 
    ventas, 
    clientes, 
    compras, 
    usuarios, 
    gastos
)

# 1. Inicializar Base de Datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DASIC ERP", version="2.0.0")

# 2. Configuración de Archivos Estáticos y Plantillas
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
    return templates.TemplateResponse("login.html", {"request": request})

# Panel Principal
@app.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Operación Comercial
@app.get("/ventas/cotizador", response_class=HTMLResponse)
async def view_cotizador(request: Request):
    return templates.TemplateResponse("cotizador.html", {"request": request})

@app.get("/seguimiento", response_class=HTMLResponse)
async def view_seguimiento(request: Request):
    return templates.TemplateResponse("seguimiento.html", {"request": request})

# Gestión de Recursos
@app.get("/inventario", response_class=HTMLResponse)
async def view_inventario(request: Request):
    return templates.TemplateResponse("inventario.html", {"request": request})

@app.get("/clientes", response_class=HTMLResponse)
async def view_clientes(request: Request):
    return templates.TemplateResponse("clientes.html", {"request": request})

@app.get("/compras", response_class=HTMLResponse)
async def view_compras(request: Request):
    return templates.TemplateResponse("compras.html", {"request": request})

# Administración y Finanzas
@app.get("/gastos", response_class=HTMLResponse)
async def view_gastos(request: Request):
    return templates.TemplateResponse("gastos.html", {"request": request})

@app.get("/reportes", response_class=HTMLResponse)
async def view_reportes(request: Request):
    return templates.TemplateResponse("reportes.html", {"request": request})

@app.get("/usuarios", response_class=HTMLResponse)
async def view_usuarios(request: Request):
    return templates.TemplateResponse("usuarios.html", {"request": request})


# --- 6. EVENTO DE ARRANQUE (SEEDING) ---
@app.on_event("startup")
def startup_db_check():
    db = SessionLocal()
    try:
        # Si no hay usuarios, crea el Super Admin
        if not db.query(models.Usuario).first():
            print("--- INICIALIZANDO SISTEMA DASIC ERP ---")
            print("Creando usuario Administrador Maestro...")
            
            admin = UsuarioCreate(
                nombre="Administrador Principal",
                email="admin@dasic.com",
                password="admin123", 
                rol=RolUsuario.ADMIN,
                activo=True
            )
            services.UserService.create_user(db, admin)
            print(">> CREADO: admin@dasic.com / admin123")
            print("---------------------------------------")
        else:
            print("--- SISTEMA DASIC ONLINE ---")
    finally:
        db.close()