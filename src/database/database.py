# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.database.base import Base
from src.models.clients import Client
from src.models.quotation import Quotation

# Base de datos SQLite

# Archivo .db creado automáticamente
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Conexión especial para SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Crea sesiones de conexión con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Función para obtener la base de datos de manera que podamos usarla en dependencias
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()