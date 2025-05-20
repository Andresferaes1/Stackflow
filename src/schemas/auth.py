# Importamos BaseModel para definir los esquemas y EmailStr para validar correos electrónicos
from pydantic import BaseModel, EmailStr

# ------------------------------
# 📝 Esquema para registro de usuario
# ------------------------------
class RegisterSchema(BaseModel):
    name: str          # Nombre del usuario (requerido)
    email: EmailStr    # Correo electrónico (valida que sea formato email)
    password: str      # Contraseña
    age: int           # Edad del usuario

# ------------------------------
# 🔐 Esquema para inicio de sesión
# ------------------------------
class LoginSchema(BaseModel):
    email: EmailStr    # Correo del usuario
    password: str      # Contraseña del usuario

# ------------------------------
# 🔁 Esquema para solicitud de recuperación de contraseña
# ------------------------------
class PasswordRecoverySchema(BaseModel):
    email: EmailStr    # Solo se requiere el correo para enviar el enlace de recuperación

# ------------------------------
# ✅ Esquema de respuesta con los datos del usuario
# Este modelo se utiliza para estructurar la salida de datos de usuario
# ------------------------------
class UserResponse(BaseModel):
    email: EmailStr    # Correo electrónico
    name: str          # Nombre del usuario
    age: int           # Edad del usuario

    class Config:
        from_attributes = True  # Permite usar objetos ORM (de SQLAlchemy) directamente

# ------------------------------
# 🔓 Esquema de respuesta para el login
# Agrupa el token, tipo de token y los datos del usuario
# ------------------------------
class LoginResponse(BaseModel):
    access_token: str         # JWT generado al iniciar sesión
    token_type: str           # Tipo de token (por lo general "bearer")
    user: UserResponse        # Datos del usuario autenticado

# ------------------------------
# 🔁 Esquema para restablecimiento de contraseña
# Este se usa cuando el usuario ya tiene un token de recuperación
# ------------------------------
class ResetPasswordSchema(BaseModel):
    token: str                # Token JWT que se recibió por correo
    new_password: str         # Nueva contraseña que el usuario desea establecer
    
# Esquema para los datos del cliente
class Client(BaseModel):
    name: str
    nit: str
    legalRepresentative: str
    email: str
    phone: str
    altPhone: str = None
    address: str

