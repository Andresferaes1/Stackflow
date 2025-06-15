from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.base import Base

class User(Base):
    """
    Modelo principal de usuarios del sistema StackFlow
    Incluye campos básicos de autenticación y campos adicionales para UserView.vue
    """
    __tablename__ = "users"

    # === CAMPOS ORIGINALES OBLIGATORIOS (NO MODIFICAR) ===
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    password = Column(String)
    age = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # === NUEVOS CAMPOS OPCIONALES PARA USERVIEW.VUE ===
    # Información empresarial del asesor comercial
    company_name = Column(String(255), nullable=True)
    company_address = Column(Text, nullable=True)
    
    # Información de contacto adicional
    phone = Column(String(20), nullable=True)
    recovery_email = Column(String(255), nullable=True)
    
    # Información personal complementaria
    city = Column(String(100), nullable=True)
    blood_type = Column(String(5), nullable=True)