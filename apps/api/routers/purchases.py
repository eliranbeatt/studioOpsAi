from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models import Purchase as PurchaseModel
from packages.schemas.models import Purchase, PurchaseCreate, PurchaseUpdate

router = APIRouter(prefix="/purchases", tags=["purchases"])

@router.get("/", response_model=List[Purchase])
async def get_purchases(db: Session = Depends(get_db)):
    """Get all purchases"""
    try:
        purchases = db.query(PurchaseModel).order_by(PurchaseModel.occurred_at.desc()).all()
        return purchases
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching purchases: {e}")

@router.get("/vendor/{vendor_id}", response_model=List[Purchase])
async def get_purchases_by_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    """Get purchases for a specific vendor"""
    try:
        purchases = db.query(PurchaseModel).filter(
            PurchaseModel.vendor_id == str(vendor_id)
        ).order_by(PurchaseModel.occurred_at.desc()).all()
        return purchases
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching purchases: {e}")

@router.get("/material/{material_id}", response_model=List[Purchase])
async def get_purchases_by_material(material_id: UUID, db: Session = Depends(get_db)):
    """Get purchases for a specific material"""
    try:
        purchases = db.query(PurchaseModel).filter(
            PurchaseModel.material_id == str(material_id)
        ).order_by(PurchaseModel.occurred_at.desc()).all()
        return purchases
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching purchases: {e}")

@router.get("/{purchase_id}", response_model=Purchase)
async def get_purchase(purchase_id: UUID, db: Session = Depends(get_db)):
    """Get a specific purchase by ID"""
    try:
        purchase = db.query(PurchaseModel).filter(PurchaseModel.id == str(purchase_id)).first()
        if not purchase:
            raise HTTPException(status_code=404, detail="Purchase not found")
        
        return purchase
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching purchase: {e}")

@router.post("/", response_model=Purchase)
async def create_purchase(purchase: PurchaseCreate, db: Session = Depends(get_db)):
    """Create a new purchase"""
    try:
        db_purchase = PurchaseModel(
            vendor_id=str(purchase.vendor_id) if purchase.vendor_id else None,
            material_id=str(purchase.material_id) if purchase.material_id else None,
            sku=purchase.sku,
            qty=purchase.qty,
            unit=purchase.unit,
            unit_price_nis=purchase.unit_price_nis,
            total_nis=purchase.total_nis,
            currency=purchase.currency,
            tax_vat_pct=purchase.tax_vat_pct,
            occurred_at=purchase.occurred_at,
            receipt_path=purchase.receipt_path
        )
        
        db.add(db_purchase)
        db.commit()
        db.refresh(db_purchase)
        
        return db_purchase
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating purchase: {e}")

@router.put("/{purchase_id}", response_model=Purchase)
async def update_purchase(purchase_id: UUID, purchase: PurchaseUpdate, db: Session = Depends(get_db)):
    """Update a purchase"""
    try:
        db_purchase = db.query(PurchaseModel).filter(PurchaseModel.id == str(purchase_id)).first()
        if not db_purchase:
            raise HTTPException(status_code=404, detail="Purchase not found")
        
        # Update only provided fields
        if purchase.vendor_id is not None:
            db_purchase.vendor_id = str(purchase.vendor_id) if purchase.vendor_id else None
        if purchase.material_id is not None:
            db_purchase.material_id = str(purchase.material_id) if purchase.material_id else None
        if purchase.sku is not None:
            db_purchase.sku = purchase.sku
        if purchase.qty is not None:
            db_purchase.qty = purchase.qty
        if purchase.unit is not None:
            db_purchase.unit = purchase.unit
        if purchase.unit_price_nis is not None:
            db_purchase.unit_price_nis = purchase.unit_price_nis
        if purchase.total_nis is not None:
            db_purchase.total_nis = purchase.total_nis
        if purchase.currency is not None:
            db_purchase.currency = purchase.currency
        if purchase.tax_vat_pct is not None:
            db_purchase.tax_vat_pct = purchase.tax_vat_pct
        if purchase.occurred_at is not None:
            db_purchase.occurred_at = purchase.occurred_at
        if purchase.receipt_path is not None:
            db_purchase.receipt_path = purchase.receipt_path
        
        db.commit()
        db.refresh(db_purchase)
        
        return db_purchase
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating purchase: {e}")

@router.delete("/{purchase_id}")
async def delete_purchase(purchase_id: UUID, db: Session = Depends(get_db)):
    """Delete a purchase"""
    try:
        db_purchase = db.query(PurchaseModel).filter(PurchaseModel.id == str(purchase_id)).first()
        if not db_purchase:
            raise HTTPException(status_code=404, detail="Purchase not found")
        
        db.delete(db_purchase)
        db.commit()
        
        return {"message": "Purchase deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting purchase: {e}")