from fastapi import APIRouter, HTTPException
from typing import List, Optional
import psycopg2
import os
from uuid import UUID
import json
from pydantic import BaseModel

router = APIRouter(prefix="/mem0", tags=["mem0"])

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

class MemoryCreate(BaseModel):
    project_id: Optional[UUID] = None
    scope_keys: Optional[dict] = None
    text: str
    source_ref: Optional[str] = None

class MemorySearch(BaseModel):
    query: str
    project_id: Optional[UUID] = None
    limit: int = 10

@router.post("/add")
async def add_memory(memory: MemoryCreate):
    """Add a memory to the vector store"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # For now, we'll just store the text without embeddings
        # In production, you would generate embeddings using a model
        cursor.execute(
            """INSERT INTO memories (project_id, scope_keys, text, source_ref)
               VALUES (%s, %s, %s, %s) RETURNING id, created_at""",
            (str(memory.project_id) if memory.project_id else None,
             json.dumps(memory.scope_keys) if memory.scope_keys else None,
             memory.text, memory.source_ref)
        )
        
        result = cursor.fetchone()
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "id": result[0],
            "created_at": result[1],
            "message": "Memory added successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding memory: {e}")

@router.post("/search")
async def search_memories(search: MemorySearch):
    """Search memories (simple text search for now)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if search.project_id:
            cursor.execute(
                """SELECT id, project_id, scope_keys, text, source_ref, created_at
                   FROM memories 
                   WHERE project_id = %s AND text ILIKE %s
                   ORDER BY created_at DESC LIMIT %s""",
                (str(search.project_id), f"%{search.query}%", search.limit)
            )
        else:
            cursor.execute(
                """SELECT id, project_id, scope_keys, text, source_ref, created_at
                   FROM memories 
                   WHERE text ILIKE %s
                   ORDER BY created_at DESC LIMIT %s""",
                (f"%{search.query}%", search.limit)
            )
        
        memories = []
        for row in cursor.fetchall():
            memories.append({
                "id": row[0],
                "project_id": row[1],
                "scope_keys": json.loads(row[2]) if row[2] else None,
                "text": row[3],
                "source_ref": row[4],
                "created_at": row[5]
            })
        
        cursor.close()
        conn.close()
        
        return {
            "query": search.query,
            "results": memories,
            "count": len(memories)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching memories: {e}")

@router.get("/{memory_id}")
async def get_memory(memory_id: UUID):
    """Get a specific memory"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, project_id, scope_keys, text, source_ref, created_at
               FROM memories WHERE id = %s""",
            (str(memory_id),)
        )
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        memory = {
            "id": row[0],
            "project_id": row[1],
            "scope_keys": json.loads(row[2]) if row[2] else None,
            "text": row[3],
            "source_ref": row[4],
            "created_at": row[5]
        }
        
        cursor.close()
        conn.close()
        return memory
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching memory: {e}")