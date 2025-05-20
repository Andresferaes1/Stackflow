# src/utils/email_utils.py

def get_email_domain(email: str) -> str:
    """Obtiene el dominio del correo electrónico (por ejemplo, 'gmail.com')."""
    try:
        return email.split('@')[1]
    except IndexError:
        raise ValueError(f"Correo electrónico no válido: {email}")
