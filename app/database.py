from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. URL DE LA BASE DE DATOS
# "sqlite:///./cotizador_pro.db" significa que el archivo se creará 
# en la misma carpeta donde ejecutes el proyecto.
SQLALCHEMY_DATABASE_URL = "sqlite:///./cotizador_pro.db"

# 2. CREAR EL MOTOR (ENGINE)
# connect_args={"check_same_thread": False} es NECESARIO solo para SQLite
# porque por defecto SQLite no permite que varios hilos (requests) usen la misma conexión.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. CREAR LA FÁBRICA DE SESIONES
# Cada vez que llega una petición, usamos esto para crear una sesión temporal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. BASE DECLARATIVA
# De esta clase heredarán todos tus modelos en models.py
Base = declarative_base()

# 5. DEPENDENCIA (VITAL PARA FASTAPI)
# Esta función se usa en todos los endpoints: 
#   - Abre la BD cuando llega la petición.
#   - Cierra la BD pase lo que pase (incluso si hay error).
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()