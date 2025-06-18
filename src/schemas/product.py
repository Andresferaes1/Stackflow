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

# Esquema para crear un producto desde el frontend
class ProductCreateFrontend(BaseModel):
    code: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    supplier: Optional[str] = None
    unit_price: float = Field(..., gt=0)
    profit_margin: Optional[float] = 0.0
    stock_quantity: int = 0
    min_stock: Optional[int] = 0
    warehouse_location: Optional[str] = None
    weight: Optional[str] = None
    dimensions: Optional[str] = None
    product_status: str = "active"

# Esquema para actualizar un producto
class ProductUpdate(ProductBase):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    stock_quantity: int | None = None  # ✅ Para actualizar cantidad

# Esquema para la respuesta de un producto
class ProductResponse(BaseModel):
    # === SISTEMA ===
    id: int
    created_at: datetime
    last_updated: datetime
    last_stock_update: datetime | None
    
    # === IDENTIFICACIÓN ===
    code: str
    name: str
    description: str | None
    
    # === PRECIOS ===
    price: float
    profit_margin: float
    
    # === INVENTARIO ===
    stock_quantity: int
    stock: int = None  # ALIAS para compatibilidad frontend
    min_stock: int
    warehouse_location: str | None
    
    # === CATEGORIZACIÓN ===
    category: str | None
    brand: str | None
    supplier: str | None
    
    # === CARACTERÍSTICAS ===
    weight: str | None
    dimensions: str | None
    product_status: str
    
    @validator('stock', pre=True, always=True)
    def set_stock_alias(cls, v, values):
        """Alias de stock_quantity para compatibilidad frontend"""
        return values.get('stock_quantity', 0)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# AGREGAR nuevos esquemas para respuestas paginadas
class ProductsPaginatedResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    filtered_total: int
    page: int
    pages: int
    per_page: int
    filters_applied: dict

class ProductStatistics(BaseModel):
    total_products: int
    filtered_products: int
    available_count: int
    low_stock_count: int
    out_of_stock_count: int
    average_price: float
    total_inventory_value: float
    categories_breakdown: dict
    brands_breakdown: dict