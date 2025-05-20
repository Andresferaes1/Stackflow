print("Ejecutando main.py...")  

from uvicorn import run 
from src.app import get_app

if __name__ == "__main__":
    app = get_app()
    run(app, host="0.0.0.0", port=8000)