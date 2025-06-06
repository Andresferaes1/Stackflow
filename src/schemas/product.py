# src/schemas/product.py

from pydantic import BaseModel
from datetime import datetime  # Importar datetime de Python
from typing import Optional

# Esquema base para el producto
class ProductBase(BaseModel):
    name: str  # Nombre del producto
    description: Optional[str] = None  # Descripción del producto (opcional)
    price: float  # Precio del producto
    stock_quantity: int  # Cantidad en stock
    code: str  # Código único del producto
    created_at: datetime | None = None  # Fecha de creación del producto

    
# Esquema para crear un producto
class ProductCreate(ProductBase):
    pass  # El esquema para crear un producto es igual al base, no hace falta nada más

# Esquema para actualizar un producto
class ProductUpdate(ProductBase):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    stock_quantity: int | None = None  # ✅ Para actualizar cantidad

# Esquema para la respuesta de un producto
class ProductResponse(ProductBase):
    id: int  # ID del producto que será devuelto en la respuesta
    code: str
    name: str
    description: str | None
    price: float
    stock_quantity: int
    created_at: datetime
    last_updated: datetime
    last_stock_update: datetime | None
    
    class Config:
        from_attributes = True  # Nuevo en Pydantic v2