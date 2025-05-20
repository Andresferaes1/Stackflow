from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.schemas.tokens import create_access_token
from src.crud import auth_crud as crud_users


# Importamos las funciones de la base de datos y el CRUD de usuarios
from src.database.database import get_db
from src.schemas.auth import (
    RegisterSchema, LoginSchema, PasswordRecoverySchema,
    ResetPasswordSchema, UserResponse, LoginResponse
)
from src.schemas.tokens import (
    create_email_verification_token, verify_email_verification_token,
    create_password_reset_token, verify_password_reset_token
)
from src.utils.email_service import send_email_verification, send_password_recovery_email
from src.crud import auth_crud as crud_users

# Definimos el router
auth_router = APIRouter()

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





    
