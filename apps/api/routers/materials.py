from fastapi import APIRouter, HTTPException, Depends
from typing import List
import psycopg2
import os
from uuid import UUID

from packages.schemas.models import Material, MaterialCreate, MaterialUpdate

router = APIRouter(prefix="/materials", tags=["materials"])

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@router.get("/", response_model=List[Material])
async def get_materials():
    """Get all materials"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, spec, unit, category, typical_waste_pct, notes, created_at, updated_at
            FROM materials ORDER BY name
        """)
        
        materials = []
        for row in cursor.fetchall():
            materials.append({
                "id": row[0],
                "name": row[1],
                "spec": row[2],
                "unit": row[3],
                "category": row[4],
                "typical_waste_pct": row[5],
                "notes": row[6],
                "created_at": row[7],
                "updated_at": row[8]
            })
        
        cursor.close()
        conn.close()
        return materials
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching materials: {e}")

@router.get("/{material_id}", response_model=Material)
async def get_material(material_id: UUID):
    """Get a specific material by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, name, spec, unit, category, typical_waste_pct, notes, created_at, updated_at
               FROM materials WHERE id = %s""",
            (str(material_id),)
        )
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Material not found")
        
        material = {
            "id": row[0],
            "name": row[1],
            "spec": row[2],
            "unit": row[3],
            "category": row[4],
            "typical_waste_pct": row[5],
            "notes": row[6],
            "created_at": row[7],
            "updated_at": row[8]
        }
        
        cursor.close()
        conn.close()
        return material
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching material: {e}")

@router.post("/", response_model=Material)
async def create_material(material: MaterialCreate):
    """Create a new material"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO materials (name, spec, unit, category, typical_waste_pct, notes)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, created_at, updated_at""",
            (material.name, material.spec, material.unit, material.category, 
             material.typical_waste_pct, material.notes)
        )
        
        result = cursor.fetchone()
        conn.commit()
        
        new_material = {
            "id": result[0],
            "name": material.name,
            "spec": material.spec,
            "unit": material.unit,
            "category": material.category,
            "typical_waste_pct": material.typical_waste_pct,
            "notes": material.notes,
            "created_at": result[1],
            "updated_at": result[2]
        }
        
        cursor.close()
        conn.close()
        return new_material
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating material: {e}")

@router.put("/{material_id}", response_model=Material)
async def update_material(material_id: UUID, material: MaterialUpdate):
    """Update a material"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE materials SET name = %s, spec = %s, unit = %s, category = %s, 
               typical_waste_pct = %s, notes = %s WHERE id = %s RETURNING created_at, updated_at""",
            (material.name, material.spec, material.unit, material.category,
             material.typical_waste_pct, material.notes, str(material_id))
        )
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Material not found")
        
        conn.commit()
        
        updated_material = {
            "id": material_id,
            "name": material.name,
            "spec": material.spec,
            "unit": material.unit,
            "category": material.category,
            "typical_waste_pct": material.typical_waste_pct,
            "notes": material.notes,
            "created_at": result[0],
            "updated_at": result[1]
        }
        
        cursor.close()
        conn.close()
        return updated_material
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating material: {e}")

@router.delete("/{material_id}")
async def delete_material(material_id: UUID):
    """Delete a material"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM materials WHERE id = %s RETURNING id", (str(material_id),))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Material not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Material deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting material: {e}")