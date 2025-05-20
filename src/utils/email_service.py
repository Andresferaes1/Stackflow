import os
from dotenv import load_dotenv
import aiosmtplib
from email.message import EmailMessage
from src.utils.smtp_config import SMTP_CONFIG
from src.utils.email_utils import get_email_domain

# ⬇️ Cargar las variables del archivo .env
load_dotenv()

EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# Función genérica para enviar correos
async def send_email(to_email: str, subject: str, content: str):
    """Envía un correo electrónico genérico."""

    domain = get_email_domain(to_email)
    smtp_config = SMTP_CONFIG.get(domain)

    if not smtp_config:
        raise ValueError(f"SMTP no configurado para el dominio: {domain}")

    # Preparamos el correo
    message = EmailMessage()
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(content)

    try:
        # Enviamos el correo usando aiosmtplib
        await aiosmtplib.send(
            message,
            hostname=smtp_config["host"],
            port=smtp_config["port"],
            start_tls=smtp_config["use_tls"],
            username=EMAIL_USERNAME,
            password=EMAIL_PASSWORD,
        )
        print(f"Correo enviado a {to_email} con el asunto: {subject}")

    except aiosmtplib.SMTPAuthenticationError as e:
        print(f"Error de autenticación: {e}")
        raise Exception(f"Error de autenticación: {e}")

    except aiosmtplib.SMTPException as e:
        print(f"Error al enviar el correo: {e}")
        raise Exception(f"Error al enviar el correo: {e}")

    except Exception as e:
        print(f"Error inesperado: {e}")
        raise Exception(f"Error inesperado: {e}")

# Función específica para el envío de correo de verificación
async def send_email_verification(to_email: str, verification_url: str):
    """Envía un correo de verificación al usuario."""
    subject = "Verifica tu cuenta"
    content = f"Por favor, verifica tu cuenta haciendo clic en el siguiente enlace: {verification_url}"
    await send_email(to_email, subject, content)

# Función específica para el envío de correo de recuperación de contraseña
async def send_password_recovery_email(to_email: str, recovery_url: str):
    """Envía un correo de recuperación de contraseña al usuario."""
    subject = "Recupera tu contraseña"
    content = f"Para recuperar tu contraseña, haz clic en el siguiente enlace: {recovery_url}"
    await send_email(to_email, subject, content)
    
    

