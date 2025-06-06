# src/models/Product.py

from sqlalchemy import Column, Integer, String, Float, DateTime
from src.database.base import Base
from datetime import datetime

class Product(Base):
    __tablename__ = "products"  # Nombre de la tabla en la base de datos

    id = Column(Integer, primary_key=True, index=True)  # ID único de producto
    code = Column(String, unique=True, nullable=False)  # Código único del producto
    name = Column(String, index=True)  # Nombre del producto, lo indexamos para búsquedas rápidas
    description = Column(String, nullable=True)  # Descripción del producto (opcional)
    price = Column(Float, nullable=False)  # Precio del producto, no puede ser nulo
    stock_quantity = Column(Integer, default=0)  # Cantidad de stock del producto, valor por defecto es 0
    created_at = Column(DateTime, default=datetime.utcnow)  # Usar DateTime de SQLAlchemy
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_stock_update = Column(DateTime, nullable=True) # Permitimos que sea null inicialmente
    
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, stock={self.stock_quantity}, last_updated={self.last_updated})>"