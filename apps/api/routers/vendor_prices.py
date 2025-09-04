from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from database import get_db
from models import VendorPrice as VendorPriceModel
from packages.schemas.models import VendorPrice, VendorPriceCreate, VendorPriceUpdate

router = APIRouter(prefix="/vendor-prices", tags=["vendor-prices"])

@router.get("/", response_model=List[VendorPrice])
async def get_vendor_prices(db: Session = Depends(get_db)):
    """Get all vendor prices"""
    try:
        vendor_prices = db.query(VendorPriceModel).order_by(VendorPriceModel.fetched_at.desc()).all()
        return vendor_prices
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vendor prices: {e}")

@router.get("/vendor/{vendor_id}", response_model=List[VendorPrice])
async def get_vendor_prices_by_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    """Get vendor prices for a specific vendor"""
    try:
        vendor_prices = db.query(VendorPriceModel).filter(
            VendorPriceModel.vendor_id == str(vendor_id)
        ).order_by(VendorPriceModel.fetched_at.desc()).all()
        return vendor_prices
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vendor prices: {e}")

@router.get("/material/{material_id}", response_model=List[VendorPrice])
async def get_vendor_prices_by_material(material_id: UUID, db: Session = Depends(get_db)):
    """Get vendor prices for a specific material"""
    try:
        vendor_prices = db.query(VendorPriceModel).filter(
            VendorPriceModel.material_id == str(material_id)
        ).order_by(VendorPriceModel.fetched_at.desc()).all()
        return vendor_prices
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vendor prices: {e}")

@router.get("/search", response_model=List[VendorPrice])
async def search_vendor_prices(
    q: Optional[str] = None,
    material_id: Optional[UUID] = None,
    vendor_id: Optional[UUID] = None,
    since: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Search vendor prices with filters"""
    try:
        query = db.query(VendorPriceModel)
        
        if q:
            # Search in SKU or material name (would need join with materials table)
            query = query.filter(VendorPriceModel.sku.ilike(f"%{q}%"))
        
        if material_id:
            query = query.filter(VendorPriceModel.material_id == str(material_id))
        
        if vendor_id:
            query = query.filter(VendorPriceModel.vendor_id == str(vendor_id))
        
        if since:
            query = query.filter(VendorPriceModel.fetched_at >= since)
        
        vendor_prices = query.order_by(VendorPriceModel.fetched_at.desc()).all()
        return vendor_prices
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching vendor prices: {e}")

@router.get("/{price_id}", response_model=VendorPrice)
async def get_vendor_price(price_id: UUID, db: Session = Depends(get_db)):
    """Get a specific vendor price by ID"""
    try:
        vendor_price = db.query(VendorPriceModel).filter(VendorPriceModel.id == str(price_id)).first()
        if not vendor_price:
            raise HTTPException(status_code=404, detail="Vendor price not found")
        
        return vendor_price
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vendor price: {e}")

@router.post("/", response_model=VendorPrice)
async def create_vendor_price(vendor_price: VendorPriceCreate, db: Session = Depends(get_db)):
    """Create a new vendor price"""
    try:
        db_vendor_price = VendorPriceModel(
            vendor_id=str(vendor_price.vendor_id) if vendor_price.vendor_id else None,
            material_id=str(vendor_price.material_id) if vendor_price.material_id else None,
            sku=vendor_price.sku,
            price_nis=vendor_price.price_nis,
            fetched_at=vendor_price.fetched_at,
            source_url=vendor_price.source_url,
            confidence=vendor_price.confidence,
            is_quote=vendor_price.is_quote
        )
        
        db.add(db_vendor_price)
        db.commit()
        db.refresh(db_vendor_price)
        
        return db_vendor_price
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating vendor price: {e}")

@router.put("/{price_id}", response_model=VendorPrice)
async def update_vendor_price(price_id: UUID, vendor_price: VendorPriceUpdate, db: Session = Depends(get_db)):
    """Update a vendor price"""
    try:
        db_vendor_price = db.query(VendorPriceModel).filter(VendorPriceModel.id == str(price_id)).first()
        if not db_vendor_price:
            raise HTTPException(status_code=404, detail="Vendor price not found")
        
        # Update only provided fields
        if vendor_price.vendor_id is not None:
            db_vendor_price.vendor_id = str(vendor_price.vendor_id) if vendor_price.vendor_id else None
        if vendor_price.material_id is not None:
            db_vendor_price.material_id = str(vendor_price.material_id) if vendor_price.material_id else None
        if vendor_price.sku is not None:
            db_vendor_price.sku = vendor_price.sku
        if vendor_price.price_nis is not None:
            db_vendor_price.price_nis = vendor_price.price_nis
        if vendor_price.fetched_at is not None:
            db_vendor_price.fetched_at = vendor_price.fetched_at
        if vendor_price.source_url is not None:
            db_vendor_price.source_url = vendor_price.source_url
        if vendor_price.confidence is not None:
            db_vendor_price.confidence = vendor_price.confidence
        if vendor_price.is_quote is not None:
            db_vendor_price.is_quote = vendor_price.is_quote
        
        db.commit()
        db.refresh(db_vendor_price)
        
        return db_vendor_price
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating vendor price: {e}")

@router.delete("/{price_id}")
async def delete_vendor_price(price_id: UUID, db: Session = Depends(get_db)):
    """Delete a vendor price"""
    try:
        db_vendor_price = db.query(VendorPriceModel).filter(VendorPriceModel.id == str(price_id)).first()
        if not db_vendor_price:
            raise HTTPException(status_code=404, detail="Vendor price not found")
        
        db.delete(db_vendor_price)
        db.commit()
        
        return {"message": "Vendor price deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting vendor price: {e}")