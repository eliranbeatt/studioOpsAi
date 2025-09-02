from fastapi import APIRouter, HTTPException
from typing import List, Optional
import psycopg2
import os
from uuid import UUID
import json
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer

router = APIRouter(prefix="/mem0", tags=["mem0"])

# Initialize embedding model
embedding_model = SentenceTransformer(os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'))

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
    """Add a memory to the vector store with embeddings"""
    try:
        # Generate embedding for the memory text
        embedding = embedding_model.encode(memory.text).tolist()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO memories (project_id, scope_keys, text, source_ref, embedding)
               VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at""",
            (str(memory.project_id) if memory.project_id else None,
             json.dumps(memory.scope_keys) if memory.scope_keys else None,
             memory.text, memory.source_ref, embedding)
        )
        
        result = cursor.fetchone()
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "id": result[0],
            "created_at": result[1],
            "message": "Memory added successfully with embedding"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding memory: {e}")

@router.post("/search")
async def search_memories(search: MemorySearch):
    """Search memories using semantic similarity with pgvector"""
    try:
        # Generate embedding for the search query
        query_embedding = embedding_model.encode(search.query).tolist()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if search.project_id:
            # Semantic search with project filter
            cursor.execute(
                """SELECT id, project_id, scope_keys, text, source_ref, created_at,
                      1 - (embedding <=> %s) as similarity
                   FROM memories 
                   WHERE project_id = %s
                   ORDER BY embedding <=> %s
                   LIMIT %s""",
                (query_embedding, str(search.project_id), query_embedding, search.limit)
            )
        else:
            # Semantic search across all memories
            cursor.execute(
                """SELECT id, project_id, scope_keys, text, source_ref, created_at,
                      1 - (embedding <=> %s) as similarity
                   FROM memories 
                   ORDER BY embedding <=> %s
                   LIMIT %s""",
                (query_embedding, query_embedding, search.limit)
            )
        
        memories = []
        for row in cursor.fetchall():
            memories.append({
                "id": row[0],
                "project_id": row[1],
                "scope_keys": json.loads(row[2]) if row[2] else None,
                "text": row[3],
                "source_ref": row[4],
                "created_at": row[5],
                "similarity": float(row[6])  # Convert to float for JSON serialization
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

@router.post("/batch/add")
async def batch_add_memories(memories: List[MemoryCreate]):
    """Add multiple memories to the vector store"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        results = []
        
        for memory in memories:
            # Generate embedding for each memory
            embedding = embedding_model.encode(memory.text).tolist()
            
            cursor.execute(
                """INSERT INTO memories (project_id, scope_keys, text, source_ref, embedding)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at""",
                (str(memory.project_id) if memory.project_id else None,
                 json.dumps(memory.scope_keys) if memory.scope_keys else None,
                 memory.text, memory.source_ref, embedding)
            )
            
            result = cursor.fetchone()
            results.append({
                "id": result[0],
                "created_at": result[1],
                "text": memory.text[:100] + "..." if len(memory.text) > 100 else memory.text
            })
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": f"Added {len(results)} memories successfully",
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding memories: {e}")

@router.get("/project/{project_id}/count")
async def get_project_memory_count(project_id: UUID):
    """Get count of memories for a project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT COUNT(*) FROM memories WHERE project_id = %s""",
            (str(project_id),)
        )
        
        count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return {
            "project_id": project_id,
            "memory_count": count
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting memories: {e}")