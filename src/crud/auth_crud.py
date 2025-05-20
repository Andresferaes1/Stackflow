# src/crud/auth_crud.py
import bcrypt
from sqlalchemy.orm import Session
from src.models.Auth import User
from src.schemas.auth import RegisterSchema, LoginSchema
from sqlalchemy.orm import Session
from src.models.Auth import User  # Importa el modelo de Usuario
from passlib.context import CryptContext  # Para la encriptación de la contraseña

# Función para hashear la contraseña
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Función para verificar la contraseña
def verify_password(stored_password: str, provided_password: str) -> bool:
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

# Crear un usuario
def create_user(db: Session, user: RegisterSchema):
    hashed_password = hash_password(user.password)
    db_user = User(
        email=user.email,
        name=user.name,
        age=user.age,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Obtener usuario por email
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# Autenticación de usuario (verifica la contraseña)
def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if user and verify_password(user.password, password):
        return user
    return None

# Inicializamos el contexto para encriptar la contraseña
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Función para actualizar la contraseña de un usuario
def update_user_password(db: Session, user: User, new_password: str):
    """Actualiza la contraseña del usuario."""
    hashed_password = pwd_context.hash(new_password)
    user.password = hashed_password
    db.commit()
    return user  # Puedes retornarlo si necesitas usarlo después

def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()  # Buscar el usuario
    if user:
        db.delete(user)  # Eliminar el usuario
        db.commit()  # Confirmar los cambios
        return user  # Retorna el usuario eliminado
    return None  # Si no se encuentra, devuelve None