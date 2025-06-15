from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from jose.exceptions import ExpiredSignatureError

# Cargar variables de entorno
load_dotenv()

# 🔑 Clave secreta para firmar los tokens
SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta_super_segura")
ALGORITHM = "HS256"
# Tiempo de expiración del token de acceso (en minutos)
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # El token expira en 30 minutos

# Tiempo de expiración de los tokens (puedes diferenciarlos si quieres)
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES = 60  # 1 hora
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 30  # 30 minutos

def create_access_token(email: str):
    """
    Función para crear un token de acceso (JWT) que se usará para autenticar al usuario.

    Parámetros:
    - email: El correo electrónico del usuario, usado como 'sub' (subject) en el payload.

    Retorna:
    - Un string que es el token JWT codificado.
    """

    # Establecer el tiempo de expiración del token (actual + 30 minutos)
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Payload que contiene la información del token
    to_encode = {
        "sub": email,  # Aquí almacenamos el email del usuario (identificador)
        "exp": expire  # Tiempo de expiración del token
    }

    # Codificar el payload con la clave secreta y el algoritmo elegido
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

# ✅ Crear token para verificación de correo
def create_email_verification_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ Verificar token de verificación
def verify_email_verification_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        return email
    except JWTError:
        return None

# ✅ Crear token para recuperación de contraseña
def create_password_reset_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ✅ Verificar token de recuperación de contraseña
def verify_password_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
        return email
    except ExpiredSignatureError:
        return "expired"
    except JWTError:
        return None

# === NUEVA FUNCIÓN PARA VERIFICAR TOKEN DE ACCESO ===
def verify_access_token(token: str):
    """
    FUNCIÓN PARA VERIFICAR TOKEN DE ACCESO
    Decodifica el token JWT y retorna el email del usuario
    Usada por get_current_user para autenticación
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
        return email
    except ExpiredSignatureError:
        return None  # Token expirado
    except JWTError:
        return None  # Token inválido

