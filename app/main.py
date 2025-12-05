from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from database import engine, SessionLocal
import models
import services
from schemas import UsuarioCreate, RolUsuario

# Importamos todos los módulos de lógica (Routers)
from routers import auth, productos, ventas, clientes, compras, usuarios

# 1. Crear las tablas en la Base de Datos (si no existen)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DASIC ERP", version="1.0.0")

# 2. Configuración de Archivos Estáticos y Plantillas HTML
# "static": Aquí viven tus JS (navbar.js), CSS y Logos.
app.mount("/static", StaticFiles(directory="static"), name="static")

# "templates": Aquí viven tus archivos HTML (login, dashboard, inventario).
templates = Jinja2Templates(directory="templates")

# 3. Configuración CORS (Seguridad del Navegador)
# Permite que el frontend (JS) hable con el backend sin bloqueos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Incluir las Rutas de la API (El Cerebro del Sistema)
app.include_router(auth.router)
app.include_router(productos.router)
app.include_router(ventas.router)
app.include_router(clientes.router)
app.include_router(compras.router)
app.include_router(usuarios.router)
# 5. RUTAS VISUALES (FRONTEND - VISTAS HTML)

@app.get("/", response_class=HTMLResponse)
async def view_login(request: Request):
    """Muestra la pantalla de Login en la raíz"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    """Muestra el Panel Principal con gráficas"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/inventario", response_class=HTMLResponse)
async def view_inventario(request: Request):
    """Muestra la Tabla de Inventario"""
    return templates.TemplateResponse("inventario.html", {"request": request})

# --- Placeholders (Rutas pendientes de HTML propio) ---
# Estas rutas cargan el dashboard temporalmente para que el menú no dé error 404
# hasta que creemos clientes.html, ventas.html, etc.

@app.get("/clientes", response_class=HTMLResponse)
async def view_clientes(request: Request):
    return templates.TemplateResponse("clientes.html", {"request": request})

@app.get("/ventas", response_class=HTMLResponse)
async def view_ventas(request: Request):
    # TODO: Crear templates/ventas.html (o cotizador.html)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/compras", response_class=HTMLResponse)
async def view_compras(request: Request):
    return templates.TemplateResponse("compras.html", {"request": request})

# ESTA ES LA NUEVA RUTA PARA EL COTIZADOR
@app.get("/ventas/cotizador", response_class=HTMLResponse)
async def view_cotizador(request: Request):
    return templates.TemplateResponse("cotizador.html", {"request": request})

@app.get("/reportes", response_class=HTMLResponse)
async def view_reportes(request: Request):
    return templates.TemplateResponse("reportes.html", {"request": request})

@app.get("/usuarios", response_class=HTMLResponse)
async def view_usuarios(request: Request):
    return templates.TemplateResponse("usuarios.html", {"request": request})

# 6. EVENTO DE ARRANQUE (Crear Super Admin)
@app.on_event("startup")
def startup_db_check():
    db = SessionLocal()
    try:
        # Verificamos si la base de datos está vacía de usuarios
        if not db.query(models.Usuario).first():
            print("--- INICIALIZANDO SISTEMA DASIC ---")
            print("Creando usuario Administrador por defecto...")
            
            admin = UsuarioCreate(
                nombre="Administrador Principal",
                email="admin@dasic.com",
                password="admin123", # ¡Recuerda cambiarla en producción!
                rol=RolUsuario.ADMIN,
                activo=True
            )
            services.UserService.create_user(db, admin)
            print("CREADO EXITOSAMENTE: admin@dasic.com / admin123")
            print("---------------------------------------")
        else:
            print("--- SISTEMA DASIC INICIADO CORRECTAMENTE ---")
    finally:
        db.close()