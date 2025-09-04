from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models import Material as MaterialModel
from packages.schemas.models import Material, MaterialCreate, MaterialUpdate

router = APIRouter(prefix="/materials", tags=["materials"])

@router.get("/", response_model=List[Material])
async def get_materials(db: Session = Depends(get_db)):
    """Get all materials"""
    try:
        materials = db.query(MaterialModel).order_by(MaterialModel.name).all()
        return materials
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching materials: {e}")

@router.get("/{material_id}", response_model=Material)
async def get_material(material_id: UUID, db: Session = Depends(get_db)):
    """Get a specific material by ID"""
    try:
        material = db.query(MaterialModel).filter(MaterialModel.id == str(material_id)).first()
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        return material
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching material: {e}")

@router.post("/", response_model=Material)
async def create_material(material: MaterialCreate, db: Session = Depends(get_db)):
    """Create a new material"""
    try:
        db_material = MaterialModel(
            name=material.name,
            spec=material.spec,
            unit=material.unit,
            category=material.category,
            typical_waste_pct=material.typical_waste_pct,
            notes=material.notes
        )
        
        db.add(db_material)
        db.commit()
        db.refresh(db_material)
        
        return db_material
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating material: {e}")

@router.put("/{material_id}", response_model=Material)
async def update_material(material_id: UUID, material: MaterialUpdate, db: Session = Depends(get_db)):
    """Update a material"""
    try:
        db_material = db.query(MaterialModel).filter(MaterialModel.id == str(material_id)).first()
        if not db_material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        # Update only provided fields
        if material.name is not None:
            db_material.name = material.name
        if material.spec is not None:
            db_material.spec = material.spec
        if material.unit is not None:
            db_material.unit = material.unit
        if material.category is not None:
            db_material.category = material.category
        if material.typical_waste_pct is not None:
            db_material.typical_waste_pct = material.typical_waste_pct
        if material.notes is not None:
            db_material.notes = material.notes
        
        db.commit()
        db.refresh(db_material)
        
        return db_material
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating material: {e}")

@router.delete("/{material_id}")
async def delete_material(material_id: UUID, db: Session = Depends(get_db)):
    """Delete a material"""
    try:
        db_material = db.query(MaterialModel).filter(MaterialModel.id == str(material_id)).first()
        if not db_material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        db.delete(db_material)
        db.commit()
        
        return {"message": "Material deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting material: {e}")