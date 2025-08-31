from fastapi import APIRouter, HTTPException, Depends
from typing import List
import psycopg2
import os
from uuid import UUID

from packages.schemas.models import Vendor, VendorCreate, VendorUpdate

router = APIRouter(prefix="/vendors", tags=["vendors"])

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@router.get("/", response_model=List[Vendor])
async def get_vendors():
    """Get all vendors"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, contact, url, rating, notes, created_at, updated_at
            FROM vendors ORDER BY name
        """)
        
        vendors = []
        for row in cursor.fetchall():
            vendors.append({
                "id": row[0],
                "name": row[1],
                "contact": row[2],
                "url": row[3],
                "rating": row[4],
                "notes": row[5],
                "created_at": row[6],
                "updated_at": row[7]
            })
        
        cursor.close()
        conn.close()
        return vendors
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vendors: {e}")

@router.get("/{vendor_id}", response_model=Vendor)
async def get_vendor(vendor_id: UUID):
    """Get a specific vendor by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, name, contact, url, rating, notes, created_at, updated_at
               FROM vendors WHERE id = %s""",
            (str(vendor_id),)
        )
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        vendor = {
            "id": row[0],
            "name": row[1],
            "contact": row[2],
            "url": row[3],
            "rating": row[4],
            "notes": row[5],
            "created_at": row[6],
            "updated_at": row[7]
        }
        
        cursor.close()
        conn.close()
        return vendor
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vendor: {e}")

@router.post("/", response_model=Vendor)
async def create_vendor(vendor: VendorCreate):
    """Create a new vendor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO vendors (name, contact, url, rating, notes)
               VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at, updated_at""",
            (vendor.name, vendor.contact, vendor.url, vendor.rating, vendor.notes)
        )
        
        result = cursor.fetchone()
        conn.commit()
        
        new_vendor = {
            "id": result[0],
            "name": vendor.name,
            "contact": vendor.contact,
            "url": vendor.url,
            "rating": vendor.rating,
            "notes": vendor.notes,
            "created_at": result[1],
            "updated_at": result[2]
        }
        
        cursor.close()
        conn.close()
        return new_vendor
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating vendor: {e}")

@router.put("/{vendor_id}", response_model=Vendor)
async def update_vendor(vendor_id: UUID, vendor: VendorUpdate):
    """Update a vendor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE vendors SET name = %s, contact = %s, url = %s, rating = %s, notes = %s
               WHERE id = %s RETURNING created_at, updated_at""",
            (vendor.name, vendor.contact, vendor.url, vendor.rating, vendor.notes, str(vendor_id))
        )
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        conn.commit()
        
        updated_vendor = {
            "id": vendor_id,
            "name": vendor.name,
            "contact": vendor.contact,
            "url": vendor.url,
            "rating": vendor.rating,
            "notes": vendor.notes,
            "created_at": result[0],
            "updated_at": result[1]
        }
        
        cursor.close()
        conn.close()
        return updated_vendor
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating vendor: {e}")

@router.delete("/{vendor_id}")
async def delete_vendor(vendor_id: UUID):
    """Delete a vendor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM vendors WHERE id = %s RETURNING id", (str(vendor_id),))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Vendor not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Vendor deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting vendor: {e}")