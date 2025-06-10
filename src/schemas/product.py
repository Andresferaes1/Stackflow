# src/schemas/product.py

from pydantic import BaseModel,  validator, Field # Importar BaseModel de Pydantic
from datetime import datetime  # Importar datetime de Python
from typing import Optional

# Esquema base para el producto
class ProductBase(BaseModel):
    # Validación de nombre: mínimo 3 caracteres, máximo 100
    name: str = Field(..., min_length=3, max_length=100, description="Nombre del producto")
    
    # Descripción opcional, máximo 500 caracteres
    description: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Descripción detallada del producto"
    )
    
    # Precio: debe ser positivo
    price: float = Field(..., gt=0, description="Precio del producto")
    
    # Stock: no puede ser negativo
    stock_quantity: int = Field(..., ge=0, description="Cantidad disponible en inventario")
    
    # Código: patrón específico para códigos de producto
    code: str = Field(
        ..., 
        pattern="^PRD[0-9]{4}$", 
        description="Código único del producto (formato: PRDxxxx)"
    )
    
    # Fecha de creación automática
    created_at: datetime | None = None

    @validator('price')
    def validate_price(cls, v):
        """Validación adicional para el precio"""
        if v > 1000000:  # Ejemplo: límite máximo de precio
            raise ValueError("El precio no puede ser mayor a 1,000,000")
        return round(v, 2)  # Redondear a 2 decimales

    @validator('code')
    def validate_code(cls, v):
        """Validación adicional para el código"""
        if not v.startswith('PRD'):
            raise ValueError("El código debe comenzar con 'PRD'")
        return v.upper()  # Convertir a mayúsculas

    
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
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Formato ISO para fechas
        }