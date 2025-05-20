from pydantic import BaseModel
from typing import Optional

# Esquema para la creación de un cliente
class ClientCreate(BaseModel):
    name: str
    nit: str
    legalRepresentative: str
    email: str
    phone: str
    altPhone: str = None
    address: str

# Esquema para la actualización de un cliente
class ClientUpdate(BaseModel):
    name: Optional[str] = None
    nit:  Optional[str] = None
    legalRepresentative: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

# Esquema para la respuesta de un cliente
class ClientResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None

    class Config:
        orm_mode = True
