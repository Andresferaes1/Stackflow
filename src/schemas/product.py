# src/schemas/product.py

from pydantic import BaseModel
from typing import Optional

# Esquema base para el producto
class ProductBase(BaseModel):
    name: str  # Nombre del producto
    description: Optional[str] = None  # Descripción del producto (opcional)
    price: float  # Precio del producto
    stock_quantity: int  # Cantidad en stock

    
# Esquema para crear un producto
class ProductCreate(ProductBase):
    pass  # El esquema para crear un producto es igual al base, no hace falta nada más

# Esquema para actualizar un producto
class ProductUpdate(ProductBase):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    quantity: int | None = None  # ✅ Para actualizar cantidad

# Esquema para la respuesta de un producto
class ProductResponse(ProductBase):
    id: int  # ID del producto que será devuelto en la respuesta
    
    class Config:
        orm_mode = True  # Esto le dice a Pydantic que puede trabajar con ORM (como SQLAlchemy)