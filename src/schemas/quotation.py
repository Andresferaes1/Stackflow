from pydantic import BaseModel, validator, Field
from typing import List, Optional
from datetime import datetime, date
from enum import Enum

# === ENUMS ===
class QuotationStatus(str, Enum):
    borrador = "borrador"
    enviada = "enviada"
    aprobada = "aprobada"
    rechazada = "rechazada"

# === SCHEMAS PARA ITEMS DE COTIZACIÓN ===
class QuotationItemBase(BaseModel):
    product_id: Optional[int] = None
    product_name: str = Field(..., min_length=1, max_length=200)
    product_description: Optional[str] = Field(None, max_length=500)
    product_code: Optional[str] = Field(None, max_length=50)
    quantity: float = Field(..., gt=0, description="Cantidad debe ser mayor a 0")
    unit_price: float = Field(..., gt=0, description="Precio unitario debe ser mayor a 0")
    discount_percentage: float = Field(0, ge=0, le=100, description="Descuento entre 0 y 100%")

class QuotationItemCreate(QuotationItemBase):
    pass

class QuotationItemUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=1, max_length=200)
    product_description: Optional[str] = Field(None, max_length=500)
    product_code: Optional[str] = Field(None, max_length=50)
    quantity: Optional[float] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)

class QuotationItemResponse(QuotationItemBase):
    id: int
    subtotal: float
    discount_amount: float
    total: float
    
    class Config:
        from_attributes = True

# === SCHEMAS PARA COTIZACIONES ===
class QuotationBase(BaseModel):
    client_name: str = Field(..., min_length=2, max_length=200)
    client_email: str = Field(..., pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    client_phone: Optional[str] = Field(None, max_length=20)
    client_address: Optional[str] = Field(None, max_length=500)
    client_document: Optional[str] = Field(None, max_length=50)
    valid_until: date = Field(..., description="Fecha de validez de la cotización")
    notes: Optional[str] = Field(None, max_length=1000)
    internal_notes: Optional[str] = Field(None, max_length=1000)

class QuotationCreate(QuotationBase):
    items: List[QuotationItemCreate] = Field(..., min_items=1, description="Debe tener al menos un item")
    
    @validator('valid_until')
    def validate_valid_until(cls, v):
        if v <= date.today():
            raise ValueError('La fecha de validez debe ser futura')
        return v

class QuotationUpdate(BaseModel):
    client_name: Optional[str] = Field(None, min_length=2, max_length=200)
    client_email: Optional[str] = Field(None, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    client_phone: Optional[str] = Field(None, max_length=20)
    client_address: Optional[str] = Field(None, max_length=500)
    client_document: Optional[str] = Field(None, max_length=50)
    valid_until: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    internal_notes: Optional[str] = Field(None, max_length=1000)
    status: Optional[QuotationStatus] = None
    items: Optional[List[QuotationItemCreate]] = None
    
    @validator('valid_until')
    def validate_valid_until(cls, v):
        if v and v <= date.today():
            raise ValueError('La fecha de validez debe ser futura')
        return v

class QuotationResponse(QuotationBase):
    id: int
    quotation_number: str
    status: QuotationStatus
    created_at: datetime
    updated_at: datetime
    created_by: int
    subtotal: float
    discount_total: float
    tax_total: float
    total: float
    items: List[QuotationItemResponse]
    
    class Config:
        from_attributes = True

class QuotationListResponse(BaseModel):
    id: int
    quotation_number: str
    client_name: str
    client_email: str
    status: QuotationStatus
    created_at: datetime
    valid_until: date
    total: float
    items_count: int
    
    class Config:
        from_attributes = True

# === FILTROS Y PAGINACIÓN ===
class QuotationFilters(BaseModel):
    quotation_number: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[QuotationStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    
    @validator('max_amount')
    def validate_amount_range(cls, v, values):
        if v and 'min_amount' in values and values['min_amount'] and v < values['min_amount']:
            raise ValueError('El monto máximo debe ser mayor al mínimo')
        return v