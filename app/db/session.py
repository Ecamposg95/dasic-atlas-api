import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _database_url() -> str:
    # Temporary default for current prototype.
    # Target architecture will require PostgreSQL via DATABASE_URL.
    return os.getenv("DATABASE_URL", "sqlite:///./cotizador_pro.db")


SQLALCHEMY_DATABASE_URL = _database_url()

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # Required for SQLite when using multiple threads.
    connect_args = {"check_same_thread": False}


engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
