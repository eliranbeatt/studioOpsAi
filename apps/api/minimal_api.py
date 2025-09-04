from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel
import uuid

# Load environment variables
load_dotenv()

app = FastAPI(
    title="StudioOps AI API",
    description="Minimal API for StudioOps AI project management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3008"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ProjectBase(BaseModel):
    name: str
    client_name: Optional[str] = None
    status: Optional[str] = "draft"
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    budget_planned: Optional[float] = None

class Project(ProjectBase):
    id: str
    created_at: str
    updated_at: str

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@app.get("/")
async def root():
    return {"message": "StudioOps AI API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0] == 1:
            return {
                "status": "healthy",
                "database": "connected",
                "service": "studioops-api"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")
    
    return {"status": "unhealthy"}

@app.get("/projects", response_model=List[Project])
async def get_projects():
    """Get all projects"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, client_name, status, start_date, due_date, budget_planned, created_at, updated_at
            FROM projects ORDER BY created_at DESC
        """)
        
        projects = []
        for row in cursor.fetchall():
            projects.append({
                "id": str(row[0]),
                "name": row[1],
                "client_name": row[2],
                "status": row[3],
                "start_date": row[4].isoformat() if row[4] else None,
                "due_date": row[5].isoformat() if row[5] else None,
                "budget_planned": float(row[6]) if row[6] else None,
                "created_at": row[7].isoformat(),
                "updated_at": row[8].isoformat()
            })
        
        cursor.close()
        conn.close()
        return projects
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {e}")

@app.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    """Create a new project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        project_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO projects (id, name, client_name, status, start_date, due_date, budget_planned)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, name, client_name, status, start_date, due_date, budget_planned, created_at, updated_at
        """, (
            project_id,
            project.name,
            project.client_name,
            project.status,
            project.start_date,
            project.due_date,
            project.budget_planned
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "id": str(result[0]),
            "name": result[1],
            "client_name": result[2],
            "status": result[3],
            "start_date": result[4].isoformat() if result[4] else None,
            "due_date": result[5].isoformat() if result[5] else None,
            "budget_planned": float(result[6]) if result[6] else None,
            "created_at": result[7].isoformat(),
            "updated_at": result[8].isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {e}")

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Project deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)