#!/usr/bin/env python3
"""
Minimal API for testing without heavy dependencies
"""

from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
import json
import time

# Import only LLM service
from llm_service import llm_service

# Load environment variables
load_dotenv()

def fix_datetime_tz(dt):
    """Ensure datetime has timezone info for consistent API responses"""
    if dt is None:
        return None
    if hasattr(dt, 'tzinfo'):
        if dt.tzinfo is None:
            # Add UTC timezone if missing
            return dt.replace(tzinfo=timezone.utc).isoformat()
        else:
            # Ensure consistent format with +00:00 instead of Z
            iso_str = dt.isoformat()
            if iso_str.endswith('Z'):
                return iso_str[:-1] + '+00:00'
            return iso_str
    return str(dt)

app = FastAPI(
    title="StudioOps AI API",
    description="Core API for StudioOps AI project management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'studioops'),
            user=os.getenv('DB_USER', 'studioops'),
            password=os.getenv('DB_PASSWORD', 'studioops123'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# Pydantic models
class ProjectBase(BaseModel):
    name: str
    client_name: Optional[str] = None
    status: Optional[str] = "draft"
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    budget_planned: Optional[float] = None
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: str
    budget_actual: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    board_id: Optional[str] = None

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    project_context: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    message: str
    session_id: str
    suggest_plan: bool
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None

@app.get("/")
async def root():
    return {"message": "StudioOps AI API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "studioops-api"}

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
                "created_at": fix_datetime_tz(row[7]),
                "updated_at": fix_datetime_tz(row[8])
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
            "created_at": fix_datetime_tz(result[7]),
            "updated_at": fix_datetime_tz(result[8])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {e}")

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a specific project by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, client_name, status, start_date, due_date, budget_planned, budget_actual, board_id, created_at, updated_at
            FROM projects WHERE id = %s
        """, (project_id,))
        
        result = cursor.fetchone()
        
        if not result:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Project not found")
        
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
            "budget_actual": float(result[7]) if result[7] else None,
            "board_id": result[8],
            "created_at": fix_datetime_tz(result[9]),
            "updated_at": fix_datetime_tz(result[10])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch project: {e}")

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First clean up related chat sessions
        cursor.execute("DELETE FROM chat_messages WHERE session_id IN (SELECT id FROM chat_sessions WHERE project_id = %s)", (project_id,))
        cursor.execute("DELETE FROM chat_sessions WHERE project_id = %s", (project_id,))
        
        # Then delete the project
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

@app.post("/chat/message", response_model=ChatMessageResponse)
async def chat_message(chat_request: ChatMessageRequest):
    """Real chat endpoint with LLM integration and memory"""
    try:
        # Handle both project_context and project_id formats
        project_context = chat_request.project_context or {}
        
        # If project_id is provided directly, add it to context
        if chat_request.project_id:
            project_context['project_id'] = chat_request.project_id
        
        print(f"DEBUG: Chat request - session_id: {chat_request.session_id}, project_context: {project_context}")
        
        # Get AI response with memory
        response = await llm_service.generate_response(
            chat_request.message, 
            chat_request.session_id, 
            project_context
        )
        
        print(f"DEBUG: LLM response - session_id: {response.get('session_id')}")
        
        return {
            "message": response["message"],
            "session_id": response["session_id"],
            "suggest_plan": response["suggest_plan"],
            "context": {
                "assumptions": ["Using current material prices", "Standard labor rates applied"],
                "risks": ["Material availability may vary", "Labor rates subject to change"],
                "suggestions": ["Consider getting multiple quotes", "Allow for 15% contingency"]
            },
            "timestamp": time.time()
        }
    
    except Exception as e:
        print(f"DEBUG: Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {e}")

@app.post("/chat/generate_plan")
async def generate_plan(request: dict):
    """Generate a project plan"""
    try:
        project_id = request.get('project_id')
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id required")
        
        # Verify project exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM projects WHERE id = %s", (project_id,))
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Generate a basic plan structure
        plan_items = [
            {
                "id": str(uuid.uuid4()),
                "category": "materials",
                "title": "Basic Construction Materials",
                "description": f"Essential materials for {project[0]}",
                "quantity": 1,
                "unit": "lot",
                "unit_price": 1000.0,
                "subtotal": 1000.0,
                "project_relevant": True
            },
            {
                "id": str(uuid.uuid4()),
                "category": "labor",
                "title": "Construction Labor",
                "description": "Professional construction work",
                "quantity": 40,
                "unit": "hours",
                "unit_price": 150.0,
                "subtotal": 6000.0,
                "project_relevant": True
            },
            {
                "id": str(uuid.uuid4()),
                "category": "equipment",
                "title": "Equipment Rental",
                "description": "Construction equipment",
                "quantity": 1,
                "unit": "week",
                "unit_price": 500.0,
                "subtotal": 500.0,
                "project_relevant": True
            },
            {
                "id": str(uuid.uuid4()),
                "category": "permits",
                "title": "Building Permits",
                "description": "Required permits and inspections",
                "quantity": 1,
                "unit": "set",
                "unit_price": 800.0,
                "subtotal": 800.0,
                "project_relevant": False
            },
            {
                "id": str(uuid.uuid4()),
                "category": "contingency",
                "title": "Contingency Buffer",
                "description": "15% contingency for unexpected costs",
                "quantity": 1,
                "unit": "percentage",
                "unit_price": 1245.0,
                "subtotal": 1245.0,
                "project_relevant": True
            }
        ]
        
        total_cost = sum(item["subtotal"] for item in plan_items)
        relevant_items = [item for item in plan_items if item.get("project_relevant", True)]
        
        return {
            "plan_id": str(uuid.uuid4()),
            "project_id": project_id,
            "items": plan_items,
            "total": total_cost,
            "currency": "NIS",
            "relevant_items_count": len(relevant_items),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "generated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)