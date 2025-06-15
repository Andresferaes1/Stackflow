from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import math

from src.models.quotation import Quotation, QuotationItem, QuotationStatusEnum
from src.schemas.quotation import (
    QuotationCreate, QuotationUpdate, QuotationFilters,
    QuotationItemCreate
)

class QuotationService:
    
    @staticmethod
    def generate_quotation_number(db: Session) -> str:
        """
        Generar número de cotización único con formato COT-YYYY-NNN
        """
        current_year = datetime.now().year
        
        # Buscar el último número del año actual
        last_quotation = db.query(Quotation).filter(
            Quotation.quotation_number.like(f"COT-{current_year}-%")
        ).order_by(desc(Quotation.quotation_number)).first()
        
        if last_quotation:
            # Extraer el número secuencial
            last_number = int(last_quotation.quotation_number.split('-')[-1])
            next_number = last_number + 1
        else:
            next_number = 1
        
        return f"COT-{current_year}-{next_number:03d}"
    
    @staticmethod
    def calculate_item_totals(item_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcular totales para un item
        """
        quantity = item_data.get('quantity', 0)
        unit_price = item_data.get('unit_price', 0)
        discount_percentage = item_data.get('discount_percentage', 0)
        
        subtotal = quantity * unit_price
        discount_amount = subtotal * (discount_percentage / 100)
        total = subtotal - discount_amount
        
        return {
            'subtotal': round(subtotal, 2),
            'discount_amount': round(discount_amount, 2),
            'total': round(total, 2)
        }
    
    @staticmethod
    def calculate_quotation_totals(items: List[QuotationItem]) -> Dict[str, float]:
        """
        Calcular totales de la cotización
        """
        subtotal = sum(item.subtotal for item in items)
        discount_total = sum(item.discount_amount for item in items)
        tax_total = 0.0  # Implementar lógica de impuestos si es necesario
        total = subtotal - discount_total + tax_total
        
        return {
            'subtotal': round(subtotal, 2),
            'discount_total': round(discount_total, 2),
            'tax_total': round(tax_total, 2),
            'total': round(total, 2)
        }
    
    @staticmethod
    def create_quotation(db: Session, quotation_data: QuotationCreate, user_id: int) -> Quotation:
        """
        Crear una nueva cotización con sus items
        """
        try:
            # Generar número de cotización
            quotation_number = QuotationService.generate_quotation_number(db)
            
            # Crear la cotización principal
            db_quotation = Quotation(
                quotation_number=quotation_number,
                client_name=quotation_data.client_name,
                client_email=quotation_data.client_email,
                client_phone=quotation_data.client_phone,
                client_address=quotation_data.client_address,
                client_document=quotation_data.client_document,
                valid_until=quotation_data.valid_until,
                notes=quotation_data.notes,
                internal_notes=quotation_data.internal_notes,
                created_by=user_id,
                status=QuotationStatusEnum.borrador
            )
            
            db.add(db_quotation)
            db.flush()  # Para obtener el ID
            
            # Crear los items
            total_items = []
            for item_data in quotation_data.items:
                # Calcular totales del item
                totals = QuotationService.calculate_item_totals(item_data.dict())
                
                db_item = QuotationItem(
                    quotation_id=db_quotation.id,
                    product_id=item_data.product_id,
                    product_name=item_data.product_name,
                    product_description=item_data.product_description,
                    product_code=item_data.product_code,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    discount_percentage=item_data.discount_percentage,
                    subtotal=totals['subtotal'],
                    discount_amount=totals['discount_amount'],
                    total=totals['total']
                )
                
                db.add(db_item)
                total_items.append(db_item)
            
            db.flush()  # Para tener los items con ID
            
            # Calcular totales de la cotización
            quotation_totals = QuotationService.calculate_quotation_totals(total_items)
            
            # Actualizar totales en la cotización
            db_quotation.subtotal = quotation_totals['subtotal']
            db_quotation.discount_total = quotation_totals['discount_total']
            db_quotation.tax_total = quotation_totals['tax_total']
            db_quotation.total = quotation_totals['total']
            
            db.commit()
            db.refresh(db_quotation)
            
            return db_quotation
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_quotation_by_id(db: Session, quotation_id: int) -> Optional[Quotation]:
        """
        Obtener cotización por ID con todos sus items
        """
        return db.query(Quotation).filter(Quotation.id == quotation_id).first()
    
    @staticmethod
    def get_quotations_with_filters(db: Session, filters: QuotationFilters) -> Dict[str, Any]:
        """
        Obtener cotizaciones con filtros y paginación
        """
        query = db.query(Quotation)
        
        # Aplicar filtros
        if filters.quotation_number:
            query = query.filter(Quotation.quotation_number.ilike(f"%{filters.quotation_number}%"))
        
        if filters.client_name:
            query = query.filter(Quotation.client_name.ilike(f"%{filters.client_name}%"))
        
        if filters.status:
            query = query.filter(Quotation.status == filters.status)
        
        if filters.start_date:
            query = query.filter(Quotation.created_at >= filters.start_date)
        
        if filters.end_date:
            query = query.filter(Quotation.created_at <= filters.end_date)
        
        if filters.min_amount:
            query = query.filter(Quotation.total >= filters.min_amount)
        
        if filters.max_amount:
            query = query.filter(Quotation.total <= filters.max_amount)
        
        # Contar total de resultados
        total_count = query.count()
        
        # Aplicar paginación
        offset = (filters.page - 1) * filters.limit
        quotations = query.order_by(desc(Quotation.created_at)).offset(offset).limit(filters.limit).all()
        
        # Calcular información de paginación
        total_pages = math.ceil(total_count / filters.limit)
        has_next = filters.page < total_pages
        has_prev = filters.page > 1
        
        return {
            "quotations": quotations,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": filters.page,
            "per_page": filters.limit,
            "has_next": has_next,
            "has_prev": has_prev
        }
    
    @staticmethod
    def update_quotation(db: Session, quotation_id: int, quotation_data: QuotationUpdate) -> Optional[Quotation]:
        """
        Actualizar cotización existente
        """
        try:
            db_quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
            
            if not db_quotation:
                return None
            
            # Actualizar campos básicos
            update_data = quotation_data.dict(exclude_unset=True, exclude={'items'})
            for field, value in update_data.items():
                if hasattr(db_quotation, field):
                    setattr(db_quotation, field, value)
            
            # Si se incluyen items, reemplazar todos
            if quotation_data.items is not None:
                # Eliminar items existentes
                db.query(QuotationItem).filter(QuotationItem.quotation_id == quotation_id).delete()
                
                # Crear nuevos items
                new_items = []
                for item_data in quotation_data.items:
                    totals = QuotationService.calculate_item_totals(item_data.dict())
                    
                    db_item = QuotationItem(
                        quotation_id=quotation_id,
                        product_id=item_data.product_id,
                        product_name=item_data.product_name,
                        product_description=item_data.product_description,
                        product_code=item_data.product_code,
                        quantity=item_data.quantity,
                        unit_price=item_data.unit_price,
                        discount_percentage=item_data.discount_percentage,
                        subtotal=totals['subtotal'],
                        discount_amount=totals['discount_amount'],
                        total=totals['total']
                    )
                    
                    db.add(db_item)
                    new_items.append(db_item)
                
                db.flush()
                
                # Recalcular totales
                quotation_totals = QuotationService.calculate_quotation_totals(new_items)
                db_quotation.subtotal = quotation_totals['subtotal']
                db_quotation.discount_total = quotation_totals['discount_total']
                db_quotation.tax_total = quotation_totals['tax_total']
                db_quotation.total = quotation_totals['total']
            
            db.commit()
            db.refresh(db_quotation)
            
            return db_quotation
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def delete_quotation(db: Session, quotation_id: int) -> bool:
        """
        Eliminar cotización (solo si está en borrador)
        """
        try:
            db_quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
            
            if not db_quotation:
                return False
            
            # Solo permitir eliminar borradores
            if db_quotation.status != QuotationStatusEnum.borrador:
                return False
            
            # Eliminar items primero (por la relación)
            db.query(QuotationItem).filter(QuotationItem.quotation_id == quotation_id).delete()
            
            # Eliminar cotización
            db.delete(db_quotation)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_quotation_stats(db: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtener estadísticas de cotizaciones
        """
        query = db.query(Quotation)
        
        if user_id:
            query = query.filter(Quotation.created_by == user_id)
        
        total_quotations = query.count()
        
        # Estadísticas por estado
        stats_by_status = {}
        for status in QuotationStatusEnum:
            count = query.filter(Quotation.status == status).count()
            total_value = db.query(func.sum(Quotation.total)).filter(
                and_(Quotation.status == status, Quotation.created_by == user_id) if user_id 
                else Quotation.status == status
            ).scalar() or 0
            
            stats_by_status[status.value] = {
                "count": count,
                "total_value": round(float(total_value), 2)
            }
        
        # Total general
        total_value = db.query(func.sum(Quotation.total)).filter(
            Quotation.created_by == user_id if user_id else True
        ).scalar() or 0
        
        return {
            "total_quotations": total_quotations,
            "total_value": round(float(total_value), 2),
            "by_status": stats_by_status,
            "avg_value": round(float(total_value) / total_quotations, 2) if total_quotations > 0 else 0
        }