from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.database.base import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    nit = Column(String, nullable=False, unique=True)
    legalRepresentative = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=False)
    altPhone = Column(String, nullable=True)
    address = Column(String, nullable=False)

    # Relación con las cotizaciones (usando una cadena de texto para evitar la importación circular)
    quotations = relationship("Quotation", back_populates="client")

    def __repr__(self):
        return f"<Client(name={self.name}, email={self.email})>"
