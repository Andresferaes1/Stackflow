"""
CRUD para gestión de usuarios del sistema StackFlow
Incluye autenticación, registro y gestión completa de perfiles
"""

import bcrypt
from sqlalchemy.orm import Session
from src.models.Auth import User
from src.schemas.auth import RegisterSchema, LoginSchema
from passlib.context import CryptContext

# Inicializar contexto para encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === FUNCIONES ORIGINALES (NO MODIFICADAS) ===

def hash_password(password: str) -> str:
    """Hashea la contraseña usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verifica la contraseña proporcionada contra la almacenada"""
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def create_user(db: Session, user: RegisterSchema):
    """Crear un nuevo usuario en el sistema"""
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

def get_user_by_email(db: Session, email: str):
    """Obtener usuario por email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    """Obtener usuario por ID"""
    return db.query(User).filter(User.id == user_id).first()

def authenticate_user(db: Session, email: str, password: str):
    """Autenticación de usuario (verifica email y contraseña)"""
    user = get_user_by_email(db, email)
    if user and verify_password(user.password, password):
        return user
    return None

def update_user_password(db: Session, user: User, new_password: str):
    """Actualiza la contraseña del usuario"""
    hashed_password = pwd_context.hash(new_password)
    user.password = hashed_password
    db.commit()
    return user

def delete_user(db: Session, user_id: int):
    """Eliminar usuario por ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return user
    return None

# === FUNCIONES NUEVAS PARA USERVIEWVUE (SOLO AÑADIDAS) ===

def get_user_complete_info(db: Session, user_id: int):
    """
    MÉTODO PRINCIPAL PARA USERVIEWVUE
    Obtiene información completa del usuario para mostrar en el frontend
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return user
    except Exception as e:
        print(f"Error al obtener información del usuario {user_id}: {str(e)}")
        return None

def update_user_profile(db: Session, user_id: int, profile_data: dict):
    """
    ACTUALIZACIÓN DE PERFIL COMPLETA
    Actualiza el perfil del usuario con nuevos campos del modelo extendido
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Campos actualizables del perfil extendido
        updatable_fields = [
            'name', 'age', 'company_name', 'company_address',
            'phone', 'recovery_email', 'city', 'blood_type'
        ]
        
        # Actualizar solo campos proporcionados y permitidos
        for field in updatable_fields:
            if field in profile_data and profile_data[field] is not None:
                setattr(user, field, profile_data[field])
        
        db.commit()
        db.refresh(user)
        return user
        
    except Exception as e:
        db.rollback()
        print(f"Error al actualizar usuario {user_id}: {str(e)}")
        return None

def calculate_profile_completion(user) -> int:
    """
    CÁLCULO DE COMPLETITUD DEL PERFIL
    Calcula porcentaje de campos completados
    """
    if not user:
        return 0
    
    # Campos importantes para un perfil completo
    profile_fields = [
        user.name, user.email, user.age,
        user.company_name, user.phone, user.city
    ]
    
    # Contar campos completados (no None y no vacíos)
    completed = sum(1 for field in profile_fields 
                   if field is not None and str(field).strip() != "")
    
    # Calcular porcentaje
    return int((completed / len(profile_fields)) * 100)