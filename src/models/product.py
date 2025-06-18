# src/models/Product.py

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from src.database.base import Base
from datetime import datetime

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {'extend_existing': True}  

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)  # RESTAURAR index=True
    name = Column(String, nullable=False, index=True)  # RESTAURAR index=True
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False, index=True)
    stock_quantity = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_stock_update = Column(DateTime, nullable=True) # Permitimos que sea null inicialmente
    
    # NUEVOS CAMPOS CON ÍNDICES ESTRATÉGICOS
    category = Column(String(100), nullable=True, index=True)  # Para filtros por categoría
    brand = Column(String(100), nullable=True, index=True)     # Para filtros por marca
    supplier = Column(String(150), nullable=True, index=True)
    min_stock = Column(Integer, default=0)
    warehouse_location = Column(String(50), nullable=True)
    profit_margin = Column(Float, default=0.0)
    product_status = Column(String(20), default='active', index=True)  # Para filtros por estado
    weight = Column(String(20), nullable=True)
    dimensions = Column(String(50), nullable=True)

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, stock={self.stock_quantity}, last_updated={self.last_updated})>"