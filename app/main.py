# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .routers import auth, ventas, clientes, productos

# Crear tablas al iniciar (por si acaso no corriste el seed)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dasic ERP")

# Servir Frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Registro de Rutas
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(ventas.router, prefix="/api/ventas", tags=["Ventas"])
app.include_router(clientes.router, prefix="/api/clientes", tags=["Clientes"])
app.include_router(productos.router, prefix="/api/inventario", tags=["Inventario"])