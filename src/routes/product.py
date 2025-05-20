# src/routes/product.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.crud.product_crud import create_product, get_products, get_product_by_id, update_product, delete_product, get_product_by_name
from src.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from src.database.database import get_db  # Importamos la función que nos da acceso a la base de datos

# Creamos el enrutador para los productos
product_router = APIRouter()

# Crear un producto
@product_router.post("/", response_model=ProductResponse)
def create_new_product(product: ProductCreate, db: Session = Depends(get_db)):
    """ Endpoint para crear un nuevo producto """
    if product.stock_quantity < 1:
        raise HTTPException(status_code=400, detail="El producto debe tener al menos una unidad en stock")
    
    db_product = create_product(db, product.name, product.description, product.price, product.stock_quantity)
    return db_product  # Retornamos el producto creado

# Obtener todos los productos
@product_router.get("/", response_model=list[ProductResponse])
def get_all_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """ Endpoint para obtener todos los productos con paginación """
    products = get_products(db, skip=skip, limit=limit)
    return products  # Retornamos la lista de productos

# Obtener un producto por su ID
@product_router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """ Endpoint para obtener un producto por su ID """
    db_product = get_product_by_id(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")  # Si no encontramos el producto, lanzamos un error
    return db_product  # Retornamos el producto encontrado

# Endpoint para obtener un producto por su nombre
@product_router.get("/name/{product_name}", response_model=ProductResponse)
def get_product_by_name_endpoint(product_name: str, db: Session = Depends(get_db)):
    """ Endpoint para obtener un producto por su nombre """
    db_product = get_product_by_name(db, product_name)  # Llamamos a la función que obtiene el producto por nombre
    if not db_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")  # Si no encontramos el producto, lanzamos un error
    return db_product  # Retornamos el producto encontrado

# Actualizar un producto
@product_router.put("/{product_id}", response_model=ProductResponse)
def update_existing_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    """ Endpoint para actualizar un producto existente """
    db_product = update_product(db, product_id, product.name, product.description, product.price, product.stock_quantity)
    if not db_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")  # Si no encontramos el producto, lanzamos un error
    return db_product  # Retornamos el producto actualizado

# Eliminar un producto
@product_router.delete("/{product_id}", response_model=ProductResponse)
def delete_existing_product(product_id: int, db: Session = Depends(get_db)):
    """ Endpoint para eliminar un producto """
    db_product = delete_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")  # Si no encontramos el producto, lanzamos un error
    return db_product  # Retornamos el producto eliminado

# src/routes/product.py

@product_router.post("/add-stock/{product_id}")
def add_stock(product_id: int, amount: int, db: Session = Depends(get_db)):
    """
    Aumenta el inventario del producto especificado
    """
    # Buscar el producto por su ID
    product = get_product_by_id(db, product_id)

    # Si el producto no existe, lanzamos un error 404
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Sumamos la cantidad al inventario actual del producto
    product.stock_quantity += amount

    # Guardamos los cambios en la base de datos
    db.commit()

    # Retornamos un mensaje indicando el nuevo inventario
    return {"message": f"Stock actualizado. Nuevo inventario: {product.quantity}"}

@product_router.post("/remove-stock/{product_id}")
def remove_stock(product_id: int, amount: int, db: Session = Depends(get_db)):
    """
    Disminuye el inventario del producto especificado
    """
    # Buscar el producto por su ID
    product = get_product_by_id(db, product_id)

    # Si el producto no existe, lanzamos un error 404
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Verificamos si hay suficiente stock para descontar la cantidad solicitada
    if product.stock_quantity < amount:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    # Restamos la cantidad al inventario actual del producto
    product.quantity -= amount

    # Guardamos los cambios en la base de datos
    db.commit()

    # Retornamos un mensaje indicando el nuevo inventario
    return {"message": f"Stock actualizado. Nuevo inventario: {product.quantity}"}

import csv
from fastapi import UploadFile

@product_router.post("/upload-products/")
def upload_products(file: UploadFile, db: Session = Depends(get_db)):
    """
    Carga productos desde un archivo CSV.
    El archivo debe tener las columnas: name, description, price, stock_quantity.
    """
    try:
        # Leer el archivo CSV
        content = file.file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(content)

        for row in reader:
            # Validar que el stock sea al menos 1
            stock_quantity = int(row["stock_quantity"])
            if stock_quantity < 1:
                raise HTTPException(status_code=400, detail=f"El producto '{row['name']}' debe tener al menos una unidad en stock")

            # Crear el producto
            create_product(db, row["name"], row["description"], float(row["price"]), stock_quantity)

        db.commit()
        return {"message": "Productos cargados exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar el archivo: {str(e)}")
    
    
@product_router.post("/upload-stock/")
def upload_stock(file: UploadFile, db: Session = Depends(get_db)):
    """
    Aumenta el stock de productos desde un archivo CSV.
    El archivo debe tener las columnas: name, stock_quantity.
    """
    try:
        # Leer el archivo CSV
        content = file.file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(content)

        for row in reader:
            # Buscar el producto por nombre
            product = get_product_by_name(db, row["name"])
            if not product:
                raise HTTPException(status_code=404, detail=f"Producto '{row['name']}' no encontrado")

            # Aumentar el stock
            product.stock_quantity += int(row["stock_quantity"])

        db.commit()
        return {"message": "Stock actualizado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al procesar el archivo: {str(e)}")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

