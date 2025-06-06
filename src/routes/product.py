# src/routes/product.py

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from src.crud.product_crud import create_product, get_products, get_product_by_id, update_product, delete_product, get_product_by_name, process_csv_updates
from src.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from src.database.database import get_db  # Importamos la función que nos da acceso a la base de datos
from typing import List
from src.schemas.product import ProductResponse
from src.models.product import Product
import csv
from io import StringIO

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

@product_router.get("/search/", response_model=List[ProductResponse])
def search_products(query: str, db: Session = Depends(get_db)):
    """
    Buscar productos por nombre o código.
    """
    if not query:
        raise HTTPException(status_code=400, detail="El parámetro 'query' no puede estar vacío")

    products = db.query(Product).filter(
        (Product.name.ilike(f"%{query}%")) | (Product.code.ilike(f"%{query}%"))
    ).all()

    if not products:
        raise HTTPException(status_code=404, detail="No se encontraron productos que coincidan con la búsqueda")

    return products

@product_router.post("/upload-updates/")
async def update_products_from_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Actualiza productos desde un archivo CSV.
    
    El archivo CSV debe tener los siguientes campos:
    - code (requerido): Código único del producto
    - name (opcional): Nuevo nombre del producto
    - description (opcional): Nueva descripción
    - price (opcional): Nuevo precio (número)
    - stock_quantity (opcional): Nueva cantidad en stock (número entero)
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un CSV"
        )
    
    try:
        content = await file.read()
        csv_text = content.decode('utf-8')
        results = process_csv_updates(db, csv_text)
        
        if not results["updated"] and results["errors"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Error procesando el archivo CSV",
                    "errors": results["errors"]
                }
            )
        
        return {
            "message": "Actualización completada",
            "updated_products": len(results["updated"]),
            "errors": results["errors"]
        }
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Error decodificando el archivo. Asegúrese de que esté en formato UTF-8"
        )


# src/routes/product.py


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

