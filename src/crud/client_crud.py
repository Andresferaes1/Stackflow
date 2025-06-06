from sqlalchemy.orm import Session
from src.models.clients import Client
from src.schemas.client import ClientCreate, ClientUpdate

# Crear un cliente
def create_client(db: Session, client: ClientCreate):
    db_client = Client(
       
    name=client.name,
    nit=client.nit,
    legalRepresentative=client.legalRepresentative,
    email=client.email,
    phone=client.phone,
    altPhone=client.altPhone,
    address=client.address
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

# Obtener todos los clientes
def get_clients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Client).offset(skip).limit(limit).all()

# Obtener cliente por ID
def get_client_by_id(db: Session, client_id: int):
    return db.query(Client).filter(Client.id == client_id).first()

def search_clients_by_name(db: Session, name: str):
    """
    Busca clientes por nombre (búsqueda parcial, no sensible a mayúsculas/minúsculas)
    """
    return db.query(Client).filter(Client.name.ilike(f"%{name}%")).all()

# Actualizar un cliente
def update_client(db: Session, client_id: int, client_data: ClientUpdate):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if db_client:
        db_client.name = client_data.name
        db_client.email = client_data.email
        db_client.phone = client_data.phone
        db_client.address = client_data.address
        db.commit()
        db.refresh(db_client)
        return db_client
    return None

# Eliminar un cliente
def delete_client(db: Session, client_id: int):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if db_client:
        db.delete(db_client)
        db.commit()
        return db_client
    return None
