from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

# Importaciones locales
from src.database.database import get_db
from src.schemas.quotation import (
    QuotationCreate, QuotationUpdate, QuotationResponse, 
    QuotationListResponse, QuotationFilters, QuotationStatus
)
from src.crud.quotation_service import QuotationService
from src.routes.auth import get_current_user
from src.models.Auth import User  

# Crear router para cotizaciones
quotation_router = APIRouter(
    prefix="/quotations",
    tags=["Cotizaciones"],
    dependencies=[Depends(get_current_user)]  # Requiere autenticación
)

# === ENDPOINT: OBTENER TODAS LAS COTIZACIONES CON FILTROS ===
@quotation_router.get("/", response_model=dict)
async def get_quotations(
    # Parámetros de filtrado opcionales
    quotation_number: Optional[str] = Query(None, description="Buscar por número de cotización"),
    client_name: Optional[str] = Query(None, description="Buscar por nombre de cliente"),
    status: Optional[QuotationStatus] = Query(None, description="Filtrar por estado"),
    start_date: Optional[datetime] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, description="Monto mínimo"),
    max_amount: Optional[float] = Query(None, description="Monto máximo"),
    
    # Parámetros de paginación
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Elementos por página"),
    
    # Dependencias
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de cotizaciones con filtros y paginación
    
    **Funcionalidades:**
    - Búsqueda por número de cotización
    - Búsqueda por nombre de cliente
    - Filtros por estado, fecha y monto
    - Paginación de resultados
    - Estadísticas incluidas
    """
    try:
        # Crear objeto de filtros
        filters = QuotationFilters(
            quotation_number=quotation_number,
            client_name=client_name,
            status=status,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            page=page,
            limit=limit
        )
        
        # Obtener cotizaciones filtradas
        result = QuotationService.get_quotations_with_filters(db, filters)
        
        # Obtener estadísticas
        stats = QuotationService.get_quotation_stats(db, current_user.id)
        
        # Convertir cotizaciones a formato de respuesta
        quotations_data = [
            QuotationListResponse.from_orm(quotation) 
            for quotation in result["quotations"]
        ]
        
        return {
            "quotations": quotations_data,
            "pagination": {
                "total_count": result["total_count"],
                "total_pages": result["total_pages"],
                "current_page": result["current_page"],
                "per_page": result["per_page"],
                "has_next": result["has_next"],
                "has_prev": result["has_prev"]
            },
            "stats": stats,
            "filters_applied": {
                "quotation_number": quotation_number,
                "client_name": client_name,
                "status": status,
                "date_range": f"{start_date} - {end_date}" if start_date or end_date else None,
                "amount_range": f"{min_amount} - {max_amount}" if min_amount or max_amount else None
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener cotizaciones: {str(e)}"
        )

# === ENDPOINT: OBTENER COTIZACIÓN POR ID ===
@quotation_router.get("/{quotation_id}", response_model=QuotationResponse)
async def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener una cotización específica por su ID
    
    **Incluye:**
    - Información completa de la cotización
    - Todos los items con detalles
    - Información del cliente
    - Totales y cálculos
    """
    try:
        # Buscar la cotización
        quotation = QuotationService.get_quotation_by_id(db, quotation_id)
        
        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cotización con ID {quotation_id} no encontrada"
            )
        
        # Verificar que el usuario tenga acceso (opcional: implementar permisos)
        # if quotation.created_by != current_user.id and not current_user.is_admin:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="No tienes permiso para ver esta cotización"
        #     )
        
        return QuotationResponse.from_orm(quotation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la cotización: {str(e)}"
        )

# === ENDPOINT: CREAR NUEVA COTIZACIÓN ===
@quotation_router.post("/", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
async def create_quotation(
    quotation_data: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crear una nueva cotización
    
    **Proceso:**
    1. Validar datos de entrada
    2. Generar número de cotización automático
    3. Crear cotización con items
    4. Calcular totales automáticamente
    5. Retornar cotización creada
    """
    try:
        # Validaciones adicionales
        if not quotation_data.items or len(quotation_data.items) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cotización debe tener al menos un item"
            )
        
        # Validar que todos los items tengan cantidad y precio positivos
        for i, item in enumerate(quotation_data.items):
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {i+1}: La cantidad debe ser mayor a 0"
                )
            if item.unit_price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {i+1}: El precio unitario debe ser mayor a 0"
                )
        
        # Crear la cotización
        quotation = QuotationService.create_quotation(db, quotation_data, current_user.id)
        
        return QuotationResponse.from_orm(quotation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la cotización: {str(e)}"
        )

# === ENDPOINT: ACTUALIZAR COTIZACIÓN ===
@quotation_router.put("/{quotation_id}", response_model=QuotationResponse)
async def update_quotation(
    quotation_id: int,
    quotation_data: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar una cotización existente
    
    **Restricciones:**
    - Solo se pueden editar cotizaciones en estado 'borrador' o 'enviada'
    - El usuario debe ser el creador (o admin)
    """
    try:
        # Buscar la cotización
        existing_quotation = QuotationService.get_quotation_by_id(db, quotation_id)
        
        if not existing_quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cotización con ID {quotation_id} no encontrada"
            )
        
        # Verificar permisos
        if existing_quotation.created_by != current_user.id:
            # Solo permitir si es admin (implementar según tu lógica)
            # if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para editar esta cotización"
            )
        
        # Verificar que se pueda editar según el estado
        if existing_quotation.status in ["aprobada", "rechazada"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede editar una cotización en estado '{existing_quotation.status}'"
            )
        
        # Validar items si se incluyen
        if quotation_data.items is not None:
            if len(quotation_data.items) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La cotización debe tener al menos un item"
                )
            
            for i, item in enumerate(quotation_data.items):
                if item.quantity <= 0 or item.unit_price <= 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Item {i+1}: Cantidad y precio deben ser mayores a 0"
                    )
        
        # Actualizar la cotización
        updated_quotation = QuotationService.update_quotation(db, quotation_id, quotation_data)
        
        return QuotationResponse.from_orm(updated_quotation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la cotización: {str(e)}"
        )

# === ENDPOINT: ELIMINAR COTIZACIÓN ===
@quotation_router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar una cotización
    
    **Restricciones:**
    - Solo se pueden eliminar cotizaciones en estado 'borrador'
    - El usuario debe ser el creador (o admin)
    """
    try:
        # Buscar la cotización
        quotation = QuotationService.get_quotation_by_id(db, quotation_id)
        
        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cotización con ID {quotation_id} no encontrada"
            )
        
        # Verificar permisos
        if quotation.created_by != current_user.id:
            # Solo permitir si es admin
            # if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta cotización"
            )
        
        # Intentar eliminar
        success = QuotationService.delete_quotation(db, quotation_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar la cotización. Solo se pueden eliminar borradores."
            )
        
        # Retorno vacío con código 204
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la cotización: {str(e)}"
        )

# === ENDPOINT: OBTENER PRÓXIMO NÚMERO DE COTIZACIÓN ===
@quotation_router.get("/next-number/", response_model=dict)
async def get_next_quotation_number(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener el próximo número de cotización disponible
    
    **Utilidad:**
    - Para mostrar en el frontend antes de crear
    - Formato: COT-YYYY-NNN
    """
    try:
        next_number = QuotationService.generate_quotation_number(db)
        
        return {
            "next_number": next_number,
            "format": "COT-YYYY-NNN",
            "year": datetime.now().year,
            "message": "Número de cotización disponible"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar número de cotización: {str(e)}"
        )

# === ENDPOINT: CAMBIAR ESTADO DE COTIZACIÓN ===
@quotation_router.patch("/{quotation_id}/status", response_model=QuotationResponse)
async def update_quotation_status(
    quotation_id: int,
    new_status: QuotationStatus,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cambiar el estado de una cotización
    
    **Estados disponibles:**
    - borrador → enviada
    - enviada → aprobada/rechazada
    - aprobada → (no se puede cambiar)
    - rechazada → borrador (solo admin)
    """
    try:
        # Buscar la cotización
        quotation = QuotationService.get_quotation_by_id(db, quotation_id)
        
        if not quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cotización con ID {quotation_id} no encontrada"
            )
        
        # Validar transición de estado
        current_status = quotation.status
        
        # Reglas de transición de estado
        valid_transitions = {
            "borrador": ["enviada"],
            "enviada": ["aprobada", "rechazada", "borrador"],
            "aprobada": [],  # Estado final
            "rechazada": ["borrador"]  # Solo admin puede reactivar
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede cambiar de estado '{current_status}' a '{new_status}'"
            )
        
        # Actualizar estado
        update_data = QuotationUpdate(
            status=new_status,
            internal_notes=f"{quotation.internal_notes or ''}\n{datetime.now()}: Estado cambiado a {new_status} por {current_user.name}. {notes or ''}".strip()
        )
        
        updated_quotation = QuotationService.update_quotation(db, quotation_id, update_data)
        
        return QuotationResponse.from_orm(updated_quotation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar estado de la cotización: {str(e)}"
        )

# === ENDPOINT: DUPLICAR COTIZACIÓN ===
@quotation_router.post("/{quotation_id}/duplicate", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Duplicar una cotización existente
    
    **Proceso:**
    1. Copia todos los datos de la cotización original
    2. Genera nuevo número de cotización
    3. Estado inicial: 'borrador'
    4. Fecha: actual
    """
    try:
        # Buscar la cotización original
        original_quotation = QuotationService.get_quotation_by_id(db, quotation_id)
        
        if not original_quotation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cotización con ID {quotation_id} no encontrada"
            )
        
        # Crear datos para la nueva cotización
        items_data = [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "product_description": item.product_description,
                "product_code": item.product_code,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "discount_percentage": item.discount_percentage
            }
            for item in original_quotation.items
        ]
        
        duplicate_data = QuotationCreate(
            client_name=original_quotation.client_name,
            client_email=original_quotation.client_email,
            client_phone=original_quotation.client_phone,
            client_address=original_quotation.client_address,
            client_document=original_quotation.client_document,
            valid_until=original_quotation.valid_until,
            notes=f"Duplicado de {original_quotation.quotation_number}\n{original_quotation.notes or ''}".strip(),
            items=items_data
        )
        
        # Crear la cotización duplicada
        new_quotation = QuotationService.create_quotation(db, duplicate_data, current_user.id)
        
        return QuotationResponse.from_orm(new_quotation)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al duplicar la cotización: {str(e)}"
        )

# === ENDPOINT: ESTADÍSTICAS DE COTIZACIONES ===
@quotation_router.get("/stats/summary", response_model=dict)
async def get_quotations_stats(
    period: Optional[str] = Query("month", pattern="^(week|month|quarter|year)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas resumidas de cotizaciones
    
    **Períodos disponibles:**
    - week: Última semana
    - month: Último mes (por defecto)
    - quarter: Último trimestre
    - year: Último año
    """
    try:
        # Calcular fecha de inicio según el período
        now = datetime.now()
        period_days = {
            "week": 7,
            "month": 30,
            "quarter": 90,
            "year": 365
        }
        
        start_date = now - timedelta(days=period_days[period])
        
        # Obtener estadísticas generales
        general_stats = QuotationService.get_quotation_stats(db, current_user.id)
        
        # Estadísticas del período específico
        period_filters = QuotationFilters(
            start_date=start_date,
            page=1,
            limit=1000  # Alto para obtener todas
        )
        period_result = QuotationService.get_quotations_with_filters(db, period_filters)
        period_quotations = period_result["quotations"]
        
        # Calcular métricas del período
        period_stats = {
            "total_quotations": len(period_quotations),
            "total_value": sum([q.total for q in period_quotations]),
            "avg_value": sum([q.total for q in period_quotations]) / len(period_quotations) if period_quotations else 0,
            "by_status": {}
        }
        
        # Agrupar por estado
        for status_value in ["borrador", "enviada", "aprobada", "rechazada"]:
            status_quotations = [q for q in period_quotations if q.status == status_value]
            period_stats["by_status"][status_value] = {
                "count": len(status_quotations),
                "value": sum([q.total for q in status_quotations])
            }
        
        return {
            "period": period,
            "start_date": start_date,
            "end_date": now,
            "general_stats": general_stats,
            "period_stats": period_stats,
            "growth": {
                "quotations_vs_previous": 0,  # TODO: Calcular crecimiento
                "value_vs_previous": 0       # TODO: Calcular crecimiento
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )