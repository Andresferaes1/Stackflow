# create_tables.py
from src.database.base import Base
from src.database.database import engine
from src.models.Auth import User  # Modelo de usuario
from src.models.clients import Client  # Modelo de cliente
from src.models.quotation import Quotation  # Modelo de cotización
from src.models.product import Product  # Modelo de producto

# Crea todas las tablas definidas en los modelos
Base.metadata.create_all(bind=engine)

from sqlalchemy import inspect

# Verifica las tablas creadas
inspector = inspect(engine)
print("Tablas creadas en la base de datos:", inspector.get_table_names())
print("✅ Tablas creadas correctamente")

