# src/crud/product_crud.py

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, List, Tuple, Optional
import math

from src.models.product import Product
from src.schemas.product import ProductCreate, ProductCreateFrontend, ProductUpdate
from datetime import datetime
from io import StringIO
import random
import string
import csv

def generate_product_code() -> str:
    """Genera código único PRD + 6 dígitos"""
    while True:
        numbers = ''.join(random.choices(string.digits, k=6))
        code = f"PRD{numbers}"
        # Verificar que no exista en BD (se hará en la función que use esto)
        return code

# Crear un producto
def create_product(db: Session, name: str, description: str, price: float, stock_quantity: int, code: str = None):
    """ Crea un nuevo producto en la base de datos """
    if code is None:
        # Generar código único
        while True:
            code = generate_product_code()
            if not db.query(Product).filter(Product.code == code).first():
                break
    
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

# === NUEVA FUNCIÓN PARA FRONTEND ===
def create_product_from_frontend(db: Session, product_data: ProductCreateFrontend) -> Product:
    """
    Nueva función específica para datos del frontend
    Mapea unit_price → price y maneja todos los campos nuevos
    """
    # Generar código si no viene del frontend
    code = product_data.code
    if not code:
        while True:
            code = generate_product_code()
            if not db.query(Product).filter(Product.code == code).first():
                break
    
    db_product = Product(
        code=code,
        name=product_data.name,
        description=product_data.description,
        price=product_data.unit_price,  # ✅ MAPEO CRÍTICO unit_price → price
        stock_quantity=product_data.stock_quantity,
        category=product_data.category,
        brand=product_data.brand,
        supplier=product_data.supplier,
        min_stock=product_data.min_stock,
        warehouse_location=product_data.warehouse_location,
        profit_margin=product_data.profit_margin,
        product_status=product_data.product_status,
        weight=product_data.weight,
        dimensions=product_data.dimensions,
        last_stock_update=datetime.utcnow() if product_data.stock_quantity > 0 else None
    )
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

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
def update_product(db: Session, product_id: int, product_data: ProductUpdate) -> Product:
    """Actualiza los detalles de un producto"""
    db_product = db.query(Product).filter(Product.id == product_id).first()  # Buscamos el producto por ID
    if not db_product:  # Si no lo encontramos
        return None  

    # Actualizar solo campos proporcionados
    update_fields = product_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        if hasattr(db_product, field) and value is not None:
            setattr(db_product, field, value)
    
    db_product.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(db_product)
    return db_product  # Retornamos el producto actualizado

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

# === MEJORAR FUNCIONES CSV ===
def validate_csv_row(row: Dict) -> Tuple[bool, str]:
    """Validación mejorada para CSV"""
    # Validar campos obligatorios
    if not row.get('name'):
        return False, "El campo 'name' es requerido"
    
    # Validar precio
    try:
        price = float(row.get('unit_price', 0))
        if price <= 0:
            return False, "unit_price debe ser mayor que 0"
    except (ValueError, TypeError):
        return False, "unit_price debe ser un número válido"
    
    # Validar stock
    try:
        stock = int(row.get('stock_quantity', 0))
        if stock < 0:
            return False, "stock_quantity no puede ser negativo"
    except (ValueError, TypeError):
        return False, "stock_quantity debe ser un número entero"
    
    return True, ""

def process_csv_updates(db: Session, csv_content: str) -> Dict[str, List]:
    """Procesamiento mejorado de CSV"""
    results = {
        "updated": [],
        "created": [],
        "errors": []
    }
    
    try:
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Validar fila
                is_valid, error_message = validate_csv_row(row)
                if not is_valid:
                    results["errors"].append(f"Fila {row_num}: {error_message}")
                    continue
                
                # Crear ProductCreateFrontend desde CSV
                frontend_data = ProductCreateFrontend(
                    code=row.get('code'),
                    name=row['name'],
                    description=row.get('description', ''),
                    category=row.get('category', ''),
                    brand=row.get('brand', ''),
                    supplier=row.get('supplier', ''),
                    unit_price=float(row['unit_price']),
                    profit_margin=float(row.get('profit_margin', 0)),
                    stock_quantity=int(row.get('stock_quantity', 0)),
                    min_stock=int(row.get('min_stock', 0)),
                    warehouse_location=row.get('warehouse_location', ''),
                    weight=row.get('weight', ''),
                    dimensions=row.get('dimensions', ''),
                    product_status=row.get('product_status', 'active')
                )
                
                # Crear producto
                product = create_product_from_frontend(db, frontend_data)
                results["created"].append({
                    'code': product.code,
                    'name': product.name,
                    'id': product.id
                })
                
            except Exception as e:
                db.rollback()
                results["errors"].append(f"Fila {row_num}: {str(e)}")
    
    except Exception as e:
        results["errors"].append(f"Error procesando CSV: {str(e)}")
    
    return results

def get_products_filtered(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    supplier: Optional[str] = None,
    product_status: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    skip: int = 0,
    limit: int = 20
):
    """Obtener productos con filtros aplicados"""
    
    # Query base
    base_query = db.query(Product)
    
    # Total sin filtros
    total = base_query.count()
    
    # Aplicar filtros
    query = base_query
    
    if search:
        search_filter = or_(
            Product.name.ilike(f"%{search}%"),
            Product.code.ilike(f"%{search}%"),
            Product.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if category:
        query = query.filter(Product.category == category)
    
    if brand:
        query = query.filter(Product.brand == brand)
    
    if supplier:
        query = query.filter(Product.supplier == supplier)
    
    if product_status:
        query = query.filter(Product.product_status == product_status)
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Total con filtros
    filtered_total = query.count()
    
    # Aplicar ordenamiento
    if hasattr(Product, sort_by):
        order_field = getattr(Product, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(order_field.desc())
        else:
            query = query.order_by(order_field.asc())
    
    # Aplicar paginación
    items = query.offset(skip).limit(limit).all()
    
    return {
        "items": items,
        "total": total,
        "filtered_total": filtered_total
    }

def get_products_statistics_filtered(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    supplier: Optional[str] = None,
    product_status: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    """Obtener estadísticas con filtros aplicados"""
    
    # Query base
    base_query = db.query(Product)
    total_products = base_query.count()
    
    # Aplicar mismos filtros
    filtered_query = base_query
    
    if search:
        search_filter = or_(
            Product.name.ilike(f"%{search}%"),
            Product.code.ilike(f"%{search}%"),
            Product.description.ilike(f"%{search}%")
        )
        filtered_query = filtered_query.filter(search_filter)
    
    if category:
        filtered_query = filtered_query.filter(Product.category == category)
    
    if brand:
        filtered_query = filtered_query.filter(Product.brand == brand)
    
    if supplier:
        filtered_query = filtered_query.filter(Product.supplier == supplier)
    
    if product_status:
        filtered_query = filtered_query.filter(Product.product_status == product_status)
    
    if min_price is not None:
        filtered_query = filtered_query.filter(Product.price >= min_price)
    
    if max_price is not None:
        filtered_query = filtered_query.filter(Product.price <= max_price)
    
    # Calcular estadísticas
    filtered_products = filtered_query.count()
    
    available_count = filtered_query.filter(
        Product.stock_quantity > 0,
        Product.product_status == 'active'
    ).count()
    
    low_stock_count = filtered_query.filter(
        Product.stock_quantity <= Product.min_stock,
        Product.stock_quantity > 0
    ).count()
    
    out_of_stock_count = filtered_query.filter(
        Product.stock_quantity == 0
    ).count()
    
    # Precios promedio
    avg_price_result = filtered_query.with_entities(func.avg(Product.price)).scalar()
    average_price = float(avg_price_result or 0)
    
    # Valor total inventario
    inventory_value_result = filtered_query.with_entities(
        func.sum(Product.price * Product.stock_quantity)
    ).scalar()
    total_inventory_value = float(inventory_value_result or 0)
    
    # Desglose por categoría
    categories_breakdown = {}
    category_stats = filtered_query.with_entities(
        Product.category,
        func.count(Product.id)
    ).group_by(Product.category).all()
    
    for cat, count in category_stats:
        if cat:
            categories_breakdown[cat] = count
    
    # Desglose por marca
    brands_breakdown = {}
    brand_stats = filtered_query.with_entities(
        Product.brand,
        func.count(Product.id)
    ).group_by(Product.brand).all()
    
    for brand, count in brand_stats:
        if brand:
            brands_breakdown[brand] = count
    
    return {
        "total_products": total_products,
        "filtered_products": filtered_products,
        "available_count": available_count,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "average_price": average_price,
        "total_inventory_value": total_inventory_value,
        "categories_breakdown": categories_breakdown,
        "brands_breakdown": brands_breakdown
    }

def get_unique_categories(db: Session) -> List[str]:
    """Obtener categorías únicas"""
    categories = db.query(Product.category).distinct().filter(
        Product.category.isnot(None),
        Product.category != ""
    ).all()
    return [cat[0] for cat in categories]

def get_unique_brands(db: Session) -> List[str]:
    """Obtener marcas únicas"""
    brands = db.query(Product.brand).distinct().filter(
        Product.brand.isnot(None),
        Product.brand != ""
    ).all()
    return [brand[0] for brand in brands]

def get_unique_suppliers(db: Session) -> List[str]:
    """Obtener proveedores únicos"""
    suppliers = db.query(Product.supplier).distinct().filter(
        Product.supplier.isnot(None),
        Product.supplier != ""
    ).all()
    return [supplier[0] for supplier in suppliers]

# src/schemas/product.py

from pydantic import BaseModel, Field
from typing import Optional

# Actualizar ProductUpdate
class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = None
    code: Optional[str] = None
    last_updated: Optional[datetime] = None

# AGREGAR después de ProductUpdate:

class ProductCreateFrontend(BaseModel):
    code: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    supplier: Optional[str] = None
    unit_price: float = Field(..., gt=0)
    profit_margin: Optional[float] = 0.0
    stock_quantity: int = 0
    min_stock: Optional[int] = 0
    warehouse_location: Optional[str] = None
    weight: Optional[str] = None
    dimensions: Optional[str] = None
    product_status: str = "active"

# ACTUALIZAR ProductResponse - AGREGAR estos campos:

category: Optional[str] = None
brand: Optional[str] = None
supplier: Optional[str] = None
min_stock: int = 0
warehouse_location: Optional[str] = None
profit_margin: float = 0.0
product_status: str = 'active'
weight: Optional[str] = None
dimensions: Optional[str] = None
