# src/crud/product_crud.py

from sqlalchemy.orm import Session
from src.models.product import Product  # Importamos el modelo de Producto
from datetime import datetime
from typing import Dict, List, Tuple
import csv
from io import StringIO

# Crear un producto
def create_product(db: Session, name: str, description: str, price: float, stock_quantity: int, code: str):
    """ Crea un nuevo producto en la base de datos """
    db_product = Product(
        name=name, 
        description=description, 
        price=price, 
        stock_quantity=stock_quantity,
        code=code,
        created_at=datetime.utcnow(),
        last_stock_update=datetime.utcnow() if stock_quantity > 0 else None
    )
    db.add(db_product)  # Añadimos el producto a la sesión de la base de datos
    db.commit()  # Guardamos los cambios en la base de datos
    db.refresh(db_product)  # Refrescamos el producto para obtener sus valores actualizados
    return db_product  # Retornamos el producto creado

# Obtener todos los productos
def get_products(db: Session, skip: int = 0, limit: int = 100):
    """ Devuelve una lista de productos paginados """
    return db.query(Product).offset(skip).limit(limit).all()  # Realizamos la consulta y retornamos los productos

# Obtener un producto por su ID
def get_product_by_id(db: Session, product_id: int):
    """ Obtiene un producto mediante su ID """
    return db.query(Product).filter(Product.id == product_id).first()  # Filtramos por ID y devolvemos el primer resultado

# Obtener un producto por su nombre
def get_product_by_name(db: Session, name: str):
    """ Obtiene un producto mediante su nombre """
    return db.query(Product).filter(Product.name.ilike(f"%{name}%")).first()  # Usamos ilike para que sea insensible a mayúsculas/minúsculas


# Actualizar un producto
def update_product(db: Session, product_id: int, name: str, description: str, price: float, stock_quantity: int):
    """ Actualiza los detalles de un producto """
    db_product = db.query(Product).filter(Product.id == product_id).first()  # Buscamos el producto por ID
    if db_product:  # Si lo encontramos
        db_product.name = name  # Actualizamos el nombre
        db_product.description = description  # Actualizamos la descripción
        db_product.price = price  # Actualizamos el precio
        db_product.stock_quantity = stock_quantity  # Actualizamos la cantidad de stock
        db.commit()  # Guardamos los cambios
        db.refresh(db_product)  # Refrescamos el producto
        return db_product  # Retornamos el producto actualizado
    return None  # Si no encontramos el producto, retornamos None

def update_stock(db: Session, product_id: int, amount: int, is_addition: bool = True):
    """ 
    Actualiza el stock de un producto y registra la fecha de la operación
    """
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        return None

    # Actualizar stock
    if is_addition:
        db_product.stock_quantity += amount
    else:
        if db_product.stock_quantity < amount:
            raise ValueError("Stock insuficiente")
        db_product.stock_quantity -= amount

    # Actualizar fecha de modificación de stock
    db_product.last_stock_update = datetime.utcnow()
    
    db.commit()
    db.refresh(db_product)
    return db_product

# Eliminar un producto
def delete_product(db: Session, product_id: int):
    """ Elimina un producto por su ID """
    db_product = db.query(Product).filter(Product.id == product_id).first()  # Buscamos el producto por ID
    if db_product:  # Si lo encontramos
        db.delete(db_product)  # Eliminamos el producto de la base de datos
        db.commit()  # Confirmamos los cambios
        return db_product  # Retornamos el producto eliminado
    return None  # Si no encontramos el producto, retornamos None

def validate_csv_row(row: Dict) -> Tuple[bool, str]:
    """
    Valida los datos de una fila del CSV.
    
    Returns:
        Tuple[bool, str]: (es_válido, mensaje_error)
    """
    required_fields = ['code']
    numeric_fields = {
        'price': float,
        'stock_quantity': int
    }
    
    # Validar campos requeridos
    for field in required_fields:
        if field not in row or not row[field]:
            return False, f"El campo '{field}' es requerido"
    
    # Validar campos numéricos
    for field, type_func in numeric_fields.items():
        if field in row and row[field]:
            try:
                type_func(row[field])
            except ValueError:
                return False, f"El campo '{field}' debe ser un número válido"
    
    return True, ""

def process_csv_updates(db: Session, csv_content: str) -> Dict[str, List]:
    """
    Procesa las actualizaciones desde el contenido CSV.
    
    Args:
        db: Sesión de base de datos
        csv_content: Contenido del archivo CSV en formato string
    
    Returns:
        Dict con listas de productos actualizados y errores
    """
    results = {
        "updated": [],
        "errors": []
    }
    
    try:
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        # Validar encabezados del CSV
        required_headers = {'code'}
        if not required_headers.issubset(csv_reader.fieldnames):
            raise ValueError(f"El CSV debe contener los campos: {required_headers}")
        
        for row in csv_reader:
            try:
                # Validar datos de la fila
                is_valid, error_message = validate_csv_row(row)
                if not is_valid:
                    results["errors"].append(f"Fila {csv_reader.line_num}: {error_message}")
                    continue
                
                # Buscar producto por código
                product = db.query(Product).filter(Product.code == row['code']).first()
                if not product:
                    results["errors"].append(f"Producto con código {row['code']} no encontrado")
                    continue
                
                # Actualizar campos si están presentes
                if 'name' in row and row['name']:
                    product.name = row['name']
                if 'description' in row and row['description']:
                    product.description = row['description']
                if 'price' in row and row['price']:
                    product.price = float(row['price'])
                if 'stock_quantity' in row and row['stock_quantity']:
                    product.stock_quantity = int(row['stock_quantity'])
                
                # Actualizar timestamp
                product.last_updated = datetime.utcnow()
                
                db.commit()
                results["updated"].append(product.code)
                
            except Exception as e:
                db.rollback()
                results["errors"].append(f"Error en fila {csv_reader.line_num}: {str(e)}")
    
    except Exception as e:
        results["errors"].append(f"Error procesando CSV: {str(e)}")
    
    return results
