from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.base import Base
import enum

# === ENUM PARA ESTADO ===
class QuotationStatusEnum(enum.Enum):
    borrador = "borrador"
    enviada = "enviada"
    aprobada = "aprobada"
    rechazada = "rechazada"

# === MODELO PRINCIPAL DE COTIZACIÓN ===
class Quotation(Base):
    __tablename__ = "quotations"

    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Información del cliente
    client_name = Column(String(200), nullable=False)
    client_email = Column(String(150), nullable=False)
    client_phone = Column(String(20), nullable=True)
    client_address = Column(Text, nullable=True)
    client_document = Column(String(50), nullable=True)
    
    # Estado y fechas
    status = Column(SQLEnum(QuotationStatusEnum), default=QuotationStatusEnum.borrador, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    valid_until = Column(Date, nullable=False)
    
    # Totales
    subtotal = Column(Float, default=0.0, nullable=False)
    discount_total = Column(Float, default=0.0, nullable=False)
    tax_total = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)
    
    # Notas
    notes = Column(Text, nullable=True)  # Notas para el cliente
    internal_notes = Column(Text, nullable=True)  # Notas internas
    
    # Relaciones
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relaciones ORM
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Quotation(number={self.quotation_number}, client={self.client_name}, total={self.total})>"

# === MODELO PARA ITEMS DE COTIZACIÓN ===
class QuotationItem(Base):
    __tablename__ = "quotation_items"

    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    
    # Información del producto
    product_id = Column(Integer, nullable=True)  # Referencia opcional a tabla productos
    product_name = Column(String(200), nullable=False)
    product_description = Column(Text, nullable=True)
    product_code = Column(String(50), nullable=True)
    
    # Cantidades y precios
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, default=0.0, nullable=False)
    
    # Totales calculados
    subtotal = Column(Float, nullable=False)  # quantity * unit_price
    discount_amount = Column(Float, nullable=False)  # subtotal * (discount_percentage / 100)
    total = Column(Float, nullable=False)  # subtotal - discount_amount
    
    # Relaciones
    quotation = relationship("Quotation", back_populates="items")
    
    def __repr__(self):
        return f"<QuotationItem(product={self.product_name}, qty={self.quantity}, total={self.total})>"