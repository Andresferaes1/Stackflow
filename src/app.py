from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Importar CORSMiddleware
from src.routes.auth import auth_router
from src.routes.client import client_router      # Importar rutas de clientes
from src.routes.product import product_router    # Importar rutas de productos
from src.routes.quotations import quotation_router
from src.database.database import get_db
from pydantic import BaseModel, Field

def get_app():
    app = FastAPI()

    # Configuración de CORS: Permitir peticiones desde Vue.js (en localhost:5173)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Permitir peticiones desde Vue.js (cambiar si usas otro puerto)
        allow_credentials=True,
        allow_methods=["*"],  # Permitir todos los métodos (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],  # Permitir todos los headers
    )

    # Registrar las rutas de tu API
    app.include_router(auth_router)
    app.include_router(client_router)  # Registrar rutas de clientes
    app.include_router(product_router)  # Registrar rutas de productos
    app.include_router(quotation_router)
    
    return app

class Client(BaseModel):
    client_email: str = Field(..., pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

    class Config:
        from_attributes = True  # ✅ CORRECTO
