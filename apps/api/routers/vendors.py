from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models import Vendor as VendorModel
from packages.schemas.models import Vendor, VendorCreate, VendorUpdate

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.get("/", response_model=List[Vendor])
async def get_vendors(db: Session = Depends(get_db)):
    """Get all vendors"""
    try:
        vendors = db.query(VendorModel).order_by(VendorModel.name).all()
        return vendors
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vendors: {e}")

@router.get("/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    """Get a specific vendor by ID"""
    try:
        vendor = db.query(VendorModel).filter(VendorModel.id == str(vendor_id)).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        return vendor
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vendor: {e}")

@router.post("/", response_model=Vendor)
async def create_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
    """Create a new vendor"""
    try:
        db_vendor = VendorModel(
            name=vendor.name,
            contact=vendor.contact,
            url=vendor.url,
            rating=vendor.rating,
            notes=vendor.notes
        )
        
        db.add(db_vendor)
        db.commit()
        db.refresh(db_vendor)
        
        return db_vendor
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating vendor: {e}")

@router.put("/{vendor_id}", response_model=Vendor)
async def update_vendor(vendor_id: UUID, vendor: VendorUpdate, db: Session = Depends(get_db)):
    """Update a vendor"""
    try:
        db_vendor = db.query(VendorModel).filter(VendorModel.id == str(vendor_id)).first()
        if not db_vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        # Update only provided fields
        if vendor.name is not None:
            db_vendor.name = vendor.name
        if vendor.contact is not None:
            db_vendor.contact = vendor.contact
        if vendor.url is not None:
            db_vendor.url = vendor.url
        if vendor.rating is not None:
            db_vendor.rating = vendor.rating
        if vendor.notes is not None:
            db_vendor.notes = vendor.notes
        
        db.commit()
        db.refresh(db_vendor)
        
        return db_vendor
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating vendor: {e}")

@router.delete("/{vendor_id}")
async def delete_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    """Delete a vendor"""
    try:
        db_vendor = db.query(VendorModel).filter(VendorModel.id == str(vendor_id)).first()
        if not db_vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        db.delete(db_vendor)
        db.commit()
        
        return {"message": "Vendor deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting vendor: {e}")