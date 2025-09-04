from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session

from database import get_db
from models import RateCard as RateCardModel
from packages.schemas.models import RateCard, RateCardCreate, RateCardUpdate

router = APIRouter(prefix="/rate-cards", tags=["rate-cards"])

@router.get("/", response_model=List[RateCard])
async def get_rate_cards(db: Session = Depends(get_db)):
    """Get all rate cards"""
    try:
        rate_cards = db.query(RateCardModel).order_by(RateCardModel.role).all()
        return rate_cards
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rate cards: {e}")

@router.get("/{role}", response_model=RateCard)
async def get_rate_card(role: str, db: Session = Depends(get_db)):
    """Get a specific rate card by role"""
    try:
        rate_card = db.query(RateCardModel).filter(RateCardModel.role == role).first()
        if not rate_card:
            raise HTTPException(status_code=404, detail="Rate card not found")
        
        return rate_card
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rate card: {e}")

@router.post("/", response_model=RateCard)
async def create_rate_card(rate_card: RateCardCreate, db: Session = Depends(get_db)):
    """Create a new rate card"""
    try:
        db_rate_card = RateCardModel(
            role=rate_card.role,
            hourly_rate_nis=rate_card.hourly_rate_nis,
            overtime_rules_json=rate_card.overtime_rules_json,
            default_efficiency=rate_card.default_efficiency
        )
        
        db.add(db_rate_card)
        db.commit()
        db.refresh(db_rate_card)
        
        return db_rate_card
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating rate card: {e}")

@router.put("/{role}", response_model=RateCard)
async def update_rate_card(role: str, rate_card: RateCardUpdate, db: Session = Depends(get_db)):
    """Update a rate card"""
    try:
        db_rate_card = db.query(RateCardModel).filter(RateCardModel.role == role).first()
        if not db_rate_card:
            raise HTTPException(status_code=404, detail="Rate card not found")
        
        # Update only provided fields
        if rate_card.hourly_rate_nis is not None:
            db_rate_card.hourly_rate_nis = rate_card.hourly_rate_nis
        if rate_card.overtime_rules_json is not None:
            db_rate_card.overtime_rules_json = rate_card.overtime_rules_json
        if rate_card.default_efficiency is not None:
            db_rate_card.default_efficiency = rate_card.default_efficiency
        
        db.commit()
        db.refresh(db_rate_card)
        
        return db_rate_card
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating rate card: {e}")

@router.delete("/{role}")
async def delete_rate_card(role: str, db: Session = Depends(get_db)):
    """Delete a rate card"""
    try:
        db_rate_card = db.query(RateCardModel).filter(RateCardModel.role == role).first()
        if not db_rate_card:
            raise HTTPException(status_code=404, detail="Rate card not found")
        
        db.delete(db_rate_card)
        db.commit()
        
        return {"message": "Rate card deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting rate card: {e}")