from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from src.database.base import Base

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"))
    client = relationship("Client", back_populates="quotations")