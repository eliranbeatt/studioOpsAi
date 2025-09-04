"""Estimation router for shipping, labor, and project cost estimation"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from uuid import UUID

from packages.schemas.estimation import (
    ShippingEstimateRequest, ShippingEstimate,
    LaborEstimateRequest, LaborEstimate,
    ProjectEstimateRequest, ProjectEstimate,
    RateCardUpdate, ShippingQuoteCreate
)
from packages.schemas.auth import UserInDB
from services.estimation_service import estimation_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/estimation", tags=["estimation"])

@router.post("/shipping", response_model=ShippingEstimate)
async def estimate_shipping(
    request: ShippingEstimateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Estimate shipping costs for a shipment"""
    try:
        return estimation_service.estimate_shipping(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error estimating shipping costs: {e}"
        )

@router.post("/labor", response_model=LaborEstimate)
async def estimate_labor(
    request: LaborEstimateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Estimate labor costs for a specific role"""
    try:
        return estimation_service.estimate_labor(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error estimating labor costs: {e}"
        )

@router.post("/project", response_model=ProjectEstimate)
async def estimate_project(
    request: ProjectEstimateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Estimate complete project costs including materials, labor, and shipping"""
    try:
        return estimation_service.estimate_project(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error estimating project costs: {e}"
        )

@router.post("/shipping-quotes")
async def create_shipping_quote(
    quote: ShippingQuoteCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Save a shipping quote to the database for future reference"""
    try:
        success = estimation_service.save_shipping_quote(quote)
        if success:
            return {"message": "Shipping quote saved successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save shipping quote"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving shipping quote: {e}"
        )

@router.put("/rate-cards/{role}")
async def update_rate_card(
    role: str,
    update: RateCardUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Update or create a labor rate card"""
    try:
        success = estimation_service.update_rate_card(role, update)
        if success:
            return {"message": f"Rate card for {role} updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update rate card for {role}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating rate card: {e}"
        )

@router.get("/rate-cards/{role}")
async def get_rate_card(
    role: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get labor rate card for a specific role"""
    try:
        # Use the pricing resolver to get rate data
        rate_data = estimation_service.pricing_resolver.get_labor_rate(role.title())
        if rate_data:
            return rate_data
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rate card not found for role: {role}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching rate card: {e}"
        )

@router.get("/rate-cards")
async def list_rate_cards(
    current_user: UserInDB = Depends(get_current_user)
):
    """List all available labor rate cards"""
    try:
        conn = estimation_service.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT role, hourly_rate_nis, default_efficiency, overtime_rules_json,
                       created_at, updated_at
                FROM rate_cards 
                ORDER BY role
            """)
            
            rate_cards = []
            for row in cursor.fetchall():
                rate_cards.append({
                    'role': row[0],
                    'hourly_rate_nis': float(row[1]),
                    'default_efficiency': float(row[2]),
                    'overtime_rules': row[3],
                    'created_at': row[4],
                    'updated_at': row[5]
                })
            
            return rate_cards
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing rate cards: {e}"
        )
    finally:
        conn.close()

@router.get("/shipping-quotes")
async def list_shipping_quotes(
    method: Optional[str] = None,
    min_distance: Optional[float] = None,
    max_distance: Optional[float] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """List shipping quotes with optional filtering"""
    try:
        conn = estimation_service.get_db_connection()
        with conn.cursor() as cursor:
            query = """
                SELECT id, route_hash, distance_km, weight_kg, type, 
                       base_fee_nis, per_km_nis, per_kg_nis, 
                       source, confidence, fetched_at, created_at
                FROM shipping_quotes 
                WHERE 1=1
            """
            params = []
            
            if method:
                query += " AND type = %s"
                params.append(method)
            
            if min_distance is not None:
                query += " AND distance_km >= %s"
                params.append(min_distance)
            
            if max_distance is not None:
                query += " AND distance_km <= %s"
                params.append(max_distance)
            
            query += " ORDER BY fetched_at DESC, confidence DESC"
            
            cursor.execute(query, params)
            
            quotes = []
            for row in cursor.fetchall():
                quotes.append({
                    'id': row[0],
                    'route_hash': row[1],
                    'distance_km': float(row[2]),
                    'weight_kg': float(row[3]),
                    'type': row[4],
                    'base_fee_nis': float(row[5]),
                    'per_km_nis': float(row[6]),
                    'per_kg_nis': float(row[7]),
                    'source': row[8],
                    'confidence': float(row[9]),
                    'fetched_at': row[10],
                    'created_at': row[11]
                })
            
            return quotes
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing shipping quotes: {e}"
        )
    finally:
        conn.close()

@router.get("/health")
async def estimation_health():
    """Estimation service health check"""
    try:
        # Test database connection
        conn = estimation_service.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        conn.close()
        
        return {
            "status": "healthy",
            "service": "estimation",
            "database": "connected"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Estimation service unhealthy: {e}"
        )