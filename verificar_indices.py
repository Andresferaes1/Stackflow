# verificar_indices.py
from sqlalchemy import inspect
from src.database.database import engine

def verificar_indices():
    inspector = inspect(engine)
    
    print("📋 ÍNDICES EN TABLA PRODUCTS:")
    indexes = inspector.get_indexes('products')
    
    for index in indexes:
        print(f"  - {index['name']}: {index['column_names']}")
    
    print(f"\n📊 Total índices: {len(indexes)}")

if __name__ == "__main__":
    verificar_indices()