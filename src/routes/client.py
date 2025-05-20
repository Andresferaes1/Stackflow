from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.crud.client_crud import create_client, get_clients, get_client_by_id, update_client, delete_client
from src.schemas.client import ClientCreate, ClientUpdate, ClientResponse

from src.database.database import get_db
from sqlalchemy.exc import IntegrityError
from src.database.database import Base # Importar la base de datos

client_router = APIRouter()

# Crear cliente
@client_router.post("/clients/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client_endpoint(client: ClientCreate, db: Session = Depends(get_db)):
    # # Verificamos si el correo ya está en la base de datos (si aplica para clientes con correo)
    # existing_client = crud.get_client_by_email(db, email=client.email)
    # if existing_client:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo electrónico ya está registrado")
    
    try:
        return create_client(db=db, client=client)
    except IntegrityError:
        db.rollback()  # Revertir los cambios si hay un error de integridad
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error al crear el cliente: Verifique los datos ingresados.")

# Obtener clientes con paginación
@client_router.get("/clients/", response_model=List[ClientResponse])
def get_clients_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    if limit > 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El límite de resultados no puede ser mayor a 1000")
    
    clients = get_clients(db, skip=skip, limit=limit)
    if not clients:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron clientes.")
    
    return clients

# Obtener cliente por ID
@client_router.get("/clients/{client_id}", response_model=ClientResponse)
def get_client_by_id_endpoint(client_id: int, db: Session = Depends(get_db)):
    client = get_client_by_id(db, client_id=client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")
    
    return client

# Actualizar cliente
@client_router.put("/clients/{client_id}", response_model=ClientResponse)
def update_client_endpoint(client_id: int, client: ClientUpdate, db: Session = Depends(get_db)):
    updated_client = update_client(db, client_id, client)
    if updated_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")
    
    return updated_client

# Eliminar cliente
@client_router.delete("/clients/{client_id}", response_model=ClientResponse)
def delete_client_endpo(client_id: int, db: Session = Depends(get_db)):
    deleted_client = delete_client(db, client_id)
    if deleted_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")
    
    return deleted_client
