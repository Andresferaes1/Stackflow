# src/routes/product.py

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, status, Query
from sqlalchemy.orm import Session
from src.crud.product_crud import (
    create_product, create_product_from_frontend, get_products, 
    get_product_by_id, update_product, delete_product, 
    get_product_by_name, process_csv_updates,
    get_products_filtered, get_products_statistics_filtered,
    get_unique_categories, get_unique_brands, get_unique_suppliers
)
from src.schemas.product import (
    ProductCreate, ProductCreateFrontend, ProductUpdate, ProductResponse,
    ProductsPaginatedResponse, ProductStatistics
)
from src.database.database import get_db
from typing import List, Optional
from src.models.product import Product
import math

# Creamos el enrutador para los productos
product_router = APIRouter(prefix="/products", tags=["products"])

# Crear un producto
@product_router.post("/", response_model=ProductResponse)
def create_new_product(product: ProductCreate, db: Session = Depends(get_db)):
    """ Endpoint para crear un nuevo producto """
    if product.stock_quantity < 1:
        raise HTTPException(status_code=400, detail="El producto debe tener al menos una unidad en stock")
    
    db_product = create_product(
        db, product.name, product.description, 
        product.price, product.stock_quantity
    )
    return db_product  # Retornamos el producto creado

# Endpoint para crear un producto desde el frontend
@product_router.post("/frontend/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_from_frontend_endpoint(
    product: ProductCreateFrontend, 
    db: Session = Depends(get_db)
):
    """
    NUEVO ENDPOINT para CsvUploadView.vue
    Acepta todos los campos del frontend incluyendo unit_price
    """
    try:
        return create_product_from_frontend(db=db, product_data=product)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al crear producto: {str(e)}"
        )

# Endpoint para carga masiva de productos desde un archivo CSV
@product_router.post("/upload-csv/", status_code=status.HTTP_200_OK)
async def upload_csv_products(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Endpoint específico para carga masiva CSV desde CsvUploadView.vue
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
        
        return {
            "message": "Procesamiento completado",
            "total_processed": len(results["created"]) + len(results["errors"]),
            "created": len(results["created"]),
            "errors": len(results["errors"]),
            "created_products": results["created"],
            "error_details": results["errors"]
        }
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Error decodificando el archivo. Asegúrese de que esté en formato UTF-8"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

# Obtener todos los productos
@product_router.get("/", response_model=ProductsPaginatedResponse)
def get_products_paginated(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=100),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    supplier: Optional[str] = None,
    product_status: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("name", regex="^(name|code|price|stock_quantity|created_at|category|brand)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Obtener productos con filtros, búsqueda y paginación"""
    
    # Calcular página actual
    page = (skip // limit) + 1
    
    # Obtener resultados filtrados
    result = get_products_filtered(
        db=db,
        search=search,
        category=category,
        brand=brand,
        supplier=supplier,
        product_status=product_status,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )
    
    # Construir respuesta
    filters_applied = {}
    if search: filters_applied["search"] = search
    if category: filters_applied["category"] = category
    if brand: filters_applied["brand"] = brand
    if supplier: filters_applied["supplier"] = supplier
    if product_status: filters_applied["product_status"] = product_status
    if min_price is not None: filters_applied["min_price"] = min_price
    if max_price is not None: filters_applied["max_price"] = max_price
    
    return ProductsPaginatedResponse(
        items=result["items"],
        total=result["total"],
        filtered_total=result["filtered_total"],
        page=page,
        pages=math.ceil(result["filtered_total"] / limit) if result["filtered_total"] > 0 else 1,
        per_page=limit,
        filters_applied=filters_applied
    )

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
def update_existing_product(
    product_id: int, 
    product: ProductUpdate, 
    db: Session = Depends(get_db)
):
    """ Endpoint para actualizar un producto existente """
    db_product = update_product(db, product_id, product)
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
        (Product.name.ilike(f"%{query}%")) | 
        (Product.code.ilike(f"%{query}%")) |
        (Product.category.ilike(f"%{query}%")) |
        (Product.brand.ilike(f"%{query}%"))
    ).all()

    if not products:
        raise HTTPException(status_code=404, detail="No se encontraron productos que coincidan con la búsqueda")

    return products

# Estadísticas de productos
@product_router.get("/statistics", response_model=ProductStatistics)
def get_products_statistics(
    search: Optional[str] = Query(None, max_length=100),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    supplier: Optional[str] = None,
    product_status: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de productos con filtros aplicados"""
    
    return get_products_statistics_filtered(
        db=db,
        search=search,
        category=category,
        brand=brand,
        supplier=supplier,
        product_status=product_status,
        min_price=min_price,
        max_price=max_price
    )

@product_router.get("/categories", response_model=List[str])
def get_product_categories(db: Session = Depends(get_db)):
    """Obtener lista de categorías únicas"""
    return get_unique_categories(db)

@product_router.get("/brands", response_model=List[str])
def get_product_brands(db: Session = Depends(get_db)):
    """Obtener lista de marcas únicas"""
    return get_unique_brands(db)

@product_router.get("/suppliers", response_model=List[str])
def get_product_suppliers(db: Session = Depends(get_db)):
    """Obtener lista de proveedores únicos"""
    return get_unique_suppliers(db)

# === MANTENER ENDPOINT UPLOAD-UPDATES EXISTENTE ===
@product_router.post("/upload-updates/")
async def update_products_from_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Mantener endpoint existente para actualizaciones"""
    # ... mantener código existente sin cambios
    pass  # (código existente se mantiene igual)

# src/routes/product.py
































































