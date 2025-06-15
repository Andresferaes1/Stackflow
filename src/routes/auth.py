from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from src.schemas.tokens import create_access_token, verify_access_token
from src.crud import auth_crud as crud_users
from src.crud.auth_crud import get_user_complete_info, update_user_profile, calculate_profile_completion
from src.models.Auth import User
from src.database.database import get_db
from src.schemas.auth import (
    RegisterSchema, LoginSchema, PasswordRecoverySchema,
    ResetPasswordSchema, UserResponse, LoginResponse,
    UserCompleteResponse, UserProfileUpdate
)
from src.schemas.tokens import (
    create_email_verification_token, verify_email_verification_token,
    create_password_reset_token, verify_password_reset_token
)
from src.utils.email_service import send_email_verification, send_password_recovery_email

# === CONFIGURACIÓN DE SEGURIDAD PARA JWT ===
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FUNCIÓN PARA OBTENER USUARIO ACTUAL DESDE TOKEN JWT
    """
    try:
        # Extraer el token del header Authorization
        token = credentials.credentials
        
        # Verificar el token y obtener el email
        email = verify_access_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Buscar el usuario por email en la base de datos
        user = crud_users.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        # Re-lanzar HTTPExceptions para que FastAPI las maneje
        raise
    except Exception as e:
        # Cualquier otro error se convierte en 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo autenticar el usuario",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Definimos el router
auth_router = APIRouter()

# === CÓDIGO ORIGINAL EXISTENTE (NO MODIFICADO) ===

# ✅ Registro de usuario
@auth_router.post("/register", response_model=UserResponse)
async def register(register_schema: RegisterSchema, db: Session = Depends(get_db)):
    # Verificamos si el email ya está registrado
    existing_user = crud_users.get_user_by_email(db, register_schema.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    # Creamos el usuario en la base de datos
    user = crud_users.create_user(db, register_schema)

    # ✅ Generación de token de verificación
    token = create_email_verification_token(user.email)
    verification_url = f"http://localhost:8000/verify-email?token={token}"

    # Envío del correo de verificación
    await send_email_verification(user.email, verification_url)

    return user

# ✅ Verificación de correo electrónico
@auth_router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    # Verificamos el token
    email = verify_email_verification_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    # Buscamos al usuario
    user = crud_users.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Marcamos al usuario como verificado
    user.is_verified = True
    db.commit()

    return {"message": "Correo verificado correctamente ✅"}

# ✅ Inicio de sesión
@auth_router.post("/login", response_model=LoginResponse)
def login(login_schema: LoginSchema, db: Session = Depends(get_db)):
    # Autenticamos al usuario con la función que hemos creado
    user = crud_users.authenticate_user(db, login_schema.email, login_schema.password)
    
    # Si no encontramos al usuario o las credenciales son incorrectas, lanzamos un error
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    # Creamos un token de acceso para este usuario
    access_token = create_access_token(user.email)

    # Devolvemos el token de acceso junto con la información básica del usuario
    return {
        "access_token": access_token,  # El token generado
        "token_type": "bearer",        # El tipo de token, que es "bearer"
        "user": user                    # Información del usuario (ej. email, nombre, etc.)
    }

# ✅ Recuperación de contraseña
@auth_router.post("/recovery", response_model=UserResponse )
async def recovery(password_recovery: PasswordRecoverySchema, db: Session = Depends(get_db)):
    # Obtenemos el correo
    email = password_recovery.email

    # Buscamos al usuario por su correo
    user = crud_users.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Generamos el token para recuperación de contraseña
    token = create_password_reset_token(email)

    # Creamos el enlace con el token
    recovery_url = f"http://localhost:8000/reset-password?token={token}"

    # Enviamos el correo de recuperación
    await send_password_recovery_email(email, recovery_url)

  
    return {"message": "Correo enviado con instrucciones para restablecer la contraseña ✅"}

# ✅ Restablecer contraseña
@auth_router.post("/reset-password")
def reset_password(reset_data: ResetPasswordSchema, db: Session = Depends(get_db)):
    email = verify_password_reset_token(reset_data.token)

    if email == "expired":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token ha expirado. Solicita uno nuevo."
        )
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )

    user = crud_users.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    crud_users.update_user_password(db, user, reset_data.new_password)

    return {"message": "Contraseña actualizada correctamente ✅"}

# ✅ Eliminar usuario por correo
@auth_router.delete("/delete-user", response_model=UserResponse)
def delete_user_by_email(email: str, db: Session = Depends(get_db)):
    # Buscamos al usuario por su correo
    user = crud_users.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Eliminamos al usuario
    db.delete(user)
    db.commit()

    return user

# === NUEVOS ENDPOINTS PARA USERVIEWVUE ===

# PRIMERO: Ruta específica /user/me (DEBE IR ANTES DE /user/{user_id})
@auth_router.get("/user/me")
async def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ENDPOINT PARA OBTENER PERFIL DEL USUARIO ACTUAL
    ============================================
    
    Obtiene el perfil usando solo el token, sin necesidad de ID.
    El token se valida automáticamente y se obtiene el usuario.
    """
    
    print("=== DEBUG USUARIO ACTUAL ===")
    print(f"ID: {current_user.id}")
    print(f"Email: {current_user.email}")
    print(f"Nombre: {current_user.name}")
    print(f"Todos los campos: {current_user.__dict__}")
    
    try:
        # Verificar si existe la función calculate_profile_completion
        completion = calculate_profile_completion(current_user)
        print(f"Profile completion: {completion}")
    except ImportError as e:
        print(f"Error importando calculate_profile_completion: {e}")
        completion = 50
    except Exception as e:
        print(f"Error ejecutando calculate_profile_completion: {e}")
        completion = 50
    
    # Respuesta completa para el frontend
    response = {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "age": getattr(current_user, 'age', 0),
        "is_verified": getattr(current_user, 'is_verified', False),
        "created_at": "2024-12-17T10:00:00",
        "company_name": getattr(current_user, 'company_name', None),
        "company_address": getattr(current_user, 'company_address', None),
        "phone": getattr(current_user, 'phone', None),
        "recovery_email": getattr(current_user, 'recovery_email', None),
        "city": getattr(current_user, 'city', None),
        "blood_type": getattr(current_user, 'blood_type', None),
        "notifications": [
            {
                "message": f"¡Bienvenido al sistema StackFlow, {current_user.name}!",
                "date": "2024-12-17T10:00:00"
            },
            {
                "message": "Tu cuenta está verificada ✅" if getattr(current_user, 'is_verified', False) else "⚠️ Verifica tu cuenta por email",
                "date": "2024-12-17T10:00:00"
            },
            {
                "message": f"Perfil completado al {completion}%",
                "date": "2024-12-17T10:00:00"
            }
        ],
        "stats": {
            "profile_completion": completion,
            "account_status": "Verificada" if getattr(current_user, 'is_verified', False) else "Pendiente verificación",
            "total_clients": 0,
            "total_quotations": 0
        }
    }
    
    print(f"Respuesta a enviar: {response}")
    return response  # ← AÑADIDO: return que faltaba

# DESPUÉS: Ruta genérica /user/{user_id}
@auth_router.get("/user/{user_id}", response_model=UserCompleteResponse)
async def get_user_complete(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ENDPOINT PRINCIPAL PARA USERVIEWVUE POR ID
    =========================================
    
    Obtiene información completa del usuario para el frontend
    Solo usuarios pueden ver su propio perfil (seguridad)
    """
    
    # === VERIFICAR PERMISOS DE ACCESO ===
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este usuario"
        )
    
    # === OBTENER USUARIO USANDO CRUD EXISTENTE ===
    user = get_user_complete_info(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # === CONSTRUIR RESPUESTA COMPLETA PARA EL FRONTEND ===
    user_data = {
        # Campos básicos del usuario
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "age": user.age,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
        
        # Campos del perfil extendido
        "company_name": user.company_name,
        "company_address": user.company_address,
        "phone": user.phone,
        "recovery_email": user.recovery_email,
        "city": user.city,
        "blood_type": user.blood_type,
        
        # Notificaciones dinámicas para el dashboard
        "notifications": [
            {
                "message": f"¡Bienvenido al sistema StackFlow, {user.name}!",
                "date": datetime.now().isoformat()
            },
            {
                "message": "Tu cuenta está verificada ✅" if user.is_verified else "⚠️ Verifica tu cuenta por email",
                "date": datetime.now().isoformat()
            },
            {
                "message": f"Perfil completado al {calculate_profile_completion(user)}%",
                "date": datetime.now().isoformat()
            }
        ],
        
        # Estadísticas del usuario para el dashboard
        "stats": {
            "profile_completion": calculate_profile_completion(user),
            "account_status": "Verificada" if user.is_verified else "Pendiente verificación",
            "total_clients": 0,      # TODO: Implementar cuando tengamos módulo de clientes
            "total_quotations": 0    # TODO: Implementar cuando tengamos cotizaciones
        }
    }
    
    return user_data

@auth_router.put("/user/{user_id}/profile", response_model=UserCompleteResponse)
async def update_user_profile_endpoint(
    user_id: int,
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ENDPOINT PARA ACTUALIZAR PERFIL DE USUARIO
    ==========================================
    
    Permite actualización segura del perfil usando CRUD existente
    Solo usuarios pueden actualizar su propio perfil
    """
    
    # === VERIFICAR PERMISOS DE ACTUALIZACIÓN ===
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar este perfil"
        )
    
    # === ACTUALIZAR USANDO CRUD EXISTENTE ===
    # Convertir modelo Pydantic a diccionario, excluyendo campos no enviados
    profile_dict = profile_data.dict(exclude_unset=True)
    updated_user = update_user_profile(db, user_id, profile_dict)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se pudo actualizar el perfil"
        )
    
    # === RETORNAR INFORMACIÓN ACTUALIZADA ===
    # Reutilizar endpoint GET para obtener datos completos actualizados
    return await get_user_complete(user_id, db, current_user)