# src/utils/smtp_config.py 
# define las configuraciones de SMTP
SMTP_CONFIG = {
    "gmail.com": {
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": True
    },
    "outlook.com": {
        "host": "smtp-mail.outlook.com",
        "port": 587,
        "use_tls": True
    },
    "yahoo.com": {
        "host": "smtp.mail.yahoo.com",
        "port": 587,
        "use_tls": True
    }
    # Puedes agregar más proveedores aquí si es necesario
}
