# models.py
from sqlalchemy import Column, Integer, String, Boolean
from src.database.base import Base



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    age = Column(Integer)
    password = Column(String) 
    is_verified = Column(Boolean, default=False)
    
