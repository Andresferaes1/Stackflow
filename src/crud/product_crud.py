# src/crud/product_crud.py

from sqlalchemy.orm import Session
from src.models.product import Product  # Importamos el modelo de Producto

# Crear un producto
def create_product(db: Session, name: str, description: str, price: float, stock_quantity: int):
    """ Crea un nuevo producto en la base de datos """
    db_product = Product(name=name, description=description, price=price, stock_quantity=stock_quantity)
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

# Eliminar un producto
def delete_product(db: Session, product_id: int):
    """ Elimina un producto por su ID """
    db_product = db.query(Product).filter(Product.id == product_id).first()  # Buscamos el producto por ID
    if db_product:  # Si lo encontramos
        db.delete(db_product)  # Eliminamos el producto de la base de datos
        db.commit()  # Confirmamos los cambios
        return db_product  # Retornamos el producto eliminado
    return None  # Si no encontramos el producto, retornamos None
