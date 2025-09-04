from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta

from database import get_db
from models import ShippingQuote as ShippingQuoteModel
from packages.schemas.models import ShippingQuote, ShippingQuoteCreate, ShippingQuoteUpdate

router = APIRouter(prefix="/shipping-quotes", tags=["shipping-quotes"])

@router.get("/", response_model=List[ShippingQuote])
async def get_shipping_quotes(db: Session = Depends(get_db)):
    """Get all shipping quotes"""
    try:
        shipping_quotes = db.query(ShippingQuoteModel).order_by(ShippingQuoteModel.fetched_at.desc()).all()
        return shipping_quotes
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching shipping quotes: {e}")

@router.get("/route/{route_hash}", response_model=List[ShippingQuote])
async def get_shipping_quotes_by_route(route_hash: str, db: Session = Depends(get_db)):
    """Get shipping quotes for a specific route"""
    try:
        shipping_quotes = db.query(ShippingQuoteModel).filter(
            ShippingQuoteModel.route_hash == route_hash
        ).order_by(ShippingQuoteModel.fetched_at.desc()).all()
        return shipping_quotes
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching shipping quotes: {e}")

@router.get("/{quote_id}", response_model=ShippingQuote)
async def get_shipping_quote(quote_id: UUID, db: Session = Depends(get_db)):
    """Get a specific shipping quote by ID"""
    try:
        shipping_quote = db.query(ShippingQuoteModel).filter(ShippingQuoteModel.id == str(quote_id)).first()
        if not shipping_quote:
            raise HTTPException(status_code=404, detail="Shipping quote not found")
        
        return shipping_quote
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching shipping quote: {e}")

@router.post("/", response_model=ShippingQuote)
async def create_shipping_quote(shipping_quote: ShippingQuoteCreate, db: Session = Depends(get_db)):
    """Create a new shipping quote"""
    try:
        db_shipping_quote = ShippingQuoteModel(
            route_hash=shipping_quote.route_hash,
            distance_km=shipping_quote.distance_km,
            weight_kg=shipping_quote.weight_kg,
            type=shipping_quote.type,
            base_fee_nis=shipping_quote.base_fee_nis,
            per_km_nis=shipping_quote.per_km_nis,
            per_kg_nis=shipping_quote.per_kg_nis,
            surge_json=shipping_quote.surge_json,
            fetched_at=shipping_quote.fetched_at,
            source=shipping_quote.source,
            confidence=shipping_quote.confidence
        )
        
        db.add(db_shipping_quote)
        db.commit()
        db.refresh(db_shipping_quote)
        
        return db_shipping_quote
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating shipping quote: {e}")

@router.put("/{quote_id}", response_model=ShippingQuote)
async def update_shipping_quote(quote_id: UUID, shipping_quote: ShippingQuoteUpdate, db: Session = Depends(get_db)):
    """Update a shipping quote"""
    try:
        db_shipping_quote = db.query(ShippingQuoteModel).filter(ShippingQuoteModel.id == str(quote_id)).first()
        if not db_shipping_quote:
            raise HTTPException(status_code=404, detail="Shipping quote not found")
        
        # Update only provided fields
        if shipping_quote.route_hash is not None:
            db_shipping_quote.route_hash = shipping_quote.route_hash
        if shipping_quote.distance_km is not None:
            db_shipping_quote.distance_km = shipping_quote.distance_km
        if shipping_quote.weight_kg is not None:
            db_shipping_quote.weight_kg = shipping_quote.weight_kg
        if shipping_quote.type is not None:
            db_shipping_quote.type = shipping_quote.type
        if shipping_quote.base_fee_nis is not None:
            db_shipping_quote.base_fee_nis = shipping_quote.base_fee_nis
        if shipping_quote.per_km_nis is not None:
            db_shipping_quote.per_km_nis = shipping_quote.per_km_nis
        if shipping_quote.per_kg_nis is not None:
            db_shipping_quote.per_kg_nis = shipping_quote.per_kg_nis
        if shipping_quote.surge_json is not None:
            db_shipping_quote.surge_json = shipping_quote.surge_json
        if shipping_quote.fetched_at is not None:
            db_shipping_quote.fetched_at = shipping_quote.fetched_at
        if shipping_quote.source is not None:
            db_shipping_quote.source = shipping_quote.source
        if shipping_quote.confidence is not None:
            db_shipping_quote.confidence = shipping_quote.confidence
        
        db.commit()
        db.refresh(db_shipping_quote)
        
        return db_shipping_quote
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating shipping quote: {e}")

@router.delete("/{quote_id}")
async def delete_shipping_quote(quote_id: UUID, db: Session = Depends(get_db)):
    """Delete a shipping quote"""
    try:
        db_shipping_quote = db.query(ShippingQuoteModel).filter(ShippingQuoteModel.id == str(quote_id)).first()
        if not db_shipping_quote:
            raise HTTPException(status_code=404, detail="Shipping quote not found")
        
        db.delete(db_shipping_quote)
        db.commit()
        
        return {"message": "Shipping quote deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting shipping quote: {e}")

@router.post("/estimate", response_model=dict)
async def estimate_shipping(
    distance_km: float,
    weight_kg: float,
    type: Optional[str] = "standard",
    db: Session = Depends(get_db)
):
    """Estimate shipping costs based on distance and weight"""
    try:
        # Look for recent quotes for similar routes
        route_hash = f"{distance_km:.1f}_{weight_kg:.1f}_{type}"
        
        recent_quotes = db.query(ShippingQuoteModel).filter(
            ShippingQuoteModel.route_hash == route_hash,
            ShippingQuoteModel.fetched_at >= datetime.now() - timedelta(days=7)
        ).order_by(ShippingQuoteModel.fetched_at.desc()).all()
        
        if recent_quotes:
            # Use the most recent quote
            quote = recent_quotes[0]
            return {
                "cost": float(quote.base_fee_nis or 0) + 
                       float(quote.per_km_nis or 0) * distance_km + 
                       float(quote.per_kg_nis or 0) * weight_kg,
                "components": {
                    "base": float(quote.base_fee_nis or 0),
                    "per_km": float(quote.per_km_nis or 0),
                    "per_kg": float(quote.per_kg_nis or 0)
                },
                "confidence": float(quote.confidence or 0.7),
                "source": "historical_quote"
            }
        
        # Fallback to default rates if no recent quotes found
        default_rates = {
            "standard": {"base": 50, "per_km": 2, "per_kg": 5},
            "express": {"base": 80, "per_km": 3, "per_kg": 8},
            "freight": {"base": 200, "per_km": 1, "per_kg": 2}
        }
        
        rates = default_rates.get(type, default_rates["standard"])
        cost = rates["base"] + rates["per_km"] * distance_km + rates["per_kg"] * weight_kg
        
        return {
            "cost": cost,
            "components": rates,
            "confidence": 0.5,
            "source": "default_rates"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error estimating shipping: {e}")