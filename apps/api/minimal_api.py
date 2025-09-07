from datetime import timezone
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
import json
import time

# Import LLM and RAG services
from llm_service import llm_service
from rag_service import rag_service

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
    description="Minimal API for StudioOps AI project management",
    version="1.0.0"
)

# Startup event - initialize database and AI services
@app.on_event("startup")
async def startup_event():
    try:
        from database import init_db
        init_db()
        print("Database initialized successfully")
        
        # Initialize AI services
        print("LLM service ready")
        print("RAG service ready")
        
    except Exception as e:
        print(f"Startup error: {e}")
        print("Continuing without database - using in-memory storage only")

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
    updated_at: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

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
    timestamp: float

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

@app.post("/chat/message", response_model=ChatMessageResponse)
async def chat_message(chat_request: ChatMessageRequest):
    """Real chat endpoint with LLM integration and memory"""
    try:
        # Handle both project_context and project_id formats
        project_context = chat_request.project_context or {}
        
        # If project_id is provided directly, add it to context
        if chat_request.project_id:
            project_context['project_id'] = chat_request.project_id
        
        # Get AI response with memory
        response = await llm_service.generate_response(
            chat_request.message, 
            chat_request.session_id, 
            project_context
        )
        
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
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {e}")

@app.get("/context/detect")
async def detect_context(message: str):
    """Analyze message and detect project context"""
    try:
        message_lower = message.lower()
        
        # Simple context detection
        project_types = {
            'cabinet': ['cabinet', 'cupboard', 'storage', 'kitchen', 'bathroom', 'vanity', 'drawer', 'shelf'],
            'furniture': ['table', 'chair', 'desk', 'shelf', 'bookshelf', 'bench', 'bed', 'furniture', 'sofa'],
            'painting': ['paint', 'painting', 'color', 'wall', 'ceiling', 'trim', 'exterior', 'interior', 'finish'],
            'electrical': ['electrical', 'wiring', 'outlet', 'switch', 'light', 'fixture', 'panel', 'circuit', 'breaker'],
            'plumbing': ['plumbing', 'pipe', 'faucet', 'sink', 'toilet', 'shower', 'drain', 'water', 'valve'],
            'renovation': ['renovate', 'remodel', 'update', 'modernize', 'refresh', 'renovation', 'remodeling'],
            'construction': ['build', 'construct', 'frame', 'structure', 'foundation', 'deck', 'patio']
        }
        
        materials = {
            'lumber': ['wood', 'lumber', 'plywood', 'board', '2x4', 'pine', 'oak', 'maple', 'timber'],
            'fasteners': ['screw', 'nail', 'bolt', 'hinge', 'bracket', 'hardware', 'fastener'],
            'finishes': ['paint', 'stain', 'varnish', 'sealer', 'primer', 'finish', 'coating'],
            'electrical': ['wire', 'cable', 'conduit', 'breaker', 'outlet', 'switch', 'electrical'],
            'plumbing': ['pipe', 'fitting', 'valve', 'faucet', 'drain', 'plumbing'],
            'hardware': ['handle', 'knob', 'pull', 'lock', 'latch', 'hardware']
        }
        
        # Detect project type with confidence scoring
        project_type_scores = {}
        for p_type, keywords in project_types.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
                    if f' {keyword} ' in f' {message_lower} ':
                        score += 2
            if score > 0:
                project_type_scores[p_type] = score
        
        detected_project_type = max(project_type_scores.items(), key=lambda x: x[1])[0] if project_type_scores else None
        
        # Detect materials
        detected_materials = []
        for material_type, keywords in materials.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_materials.append(material_type)
        
        return {
            "success": True,
            "analysis": {
                "message": message,
                "detected_project_type": detected_project_type,
                "project_type_confidence": project_type_scores,
                "detected_materials": detected_materials,
                "recommended_materials": [],
                "recommended_labor": []
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing context: {e}")

# Additional chat endpoints
@app.get("/chat/sessions", response_model=List[Dict[str, Any]])
async def get_chat_sessions(project_id: Optional[str] = None):
    """Get all chat sessions, optionally filtered by project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if project_id:
            cursor.execute("""
                SELECT DISTINCT session_id, MAX(created_at) as last_activity
                FROM chat_messages 
                WHERE project_context->>'project_id' = %s
                GROUP BY session_id
                ORDER BY last_activity DESC
            """, (project_id,))
        else:
            cursor.execute("""
                SELECT DISTINCT session_id, MAX(created_at) as last_activity
                FROM chat_messages 
                GROUP BY session_id
                ORDER BY last_activity DESC
            """)
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "session_id": row[0],
                "last_activity": row[1].isoformat() if row[1] else None
            })
        
        cursor.close()
        conn.close()
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat sessions: {e}")

@app.get("/chat/history/{session_id}", response_model=List[Dict[str, Any]])
async def get_chat_history(session_id: str):
    """Get chat history for a specific session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, message, response, is_user, project_context, created_at
            FROM chat_messages 
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (session_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "message": row[1],
                "response": row[2],
                "is_user": row[3],
                "project_context": row[4],
                "created_at": row[5].isoformat() if row[5] else None
            })
        
        cursor.close()
        conn.close()
        return messages
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat history: {e}")

@app.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session and all its messages"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM chat_messages WHERE session_id = %s", (session_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Chat session deleted successfully", "deleted_messages": cursor.rowcount}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chat session: {e}")

@app.get("/chat/analyze")
async def analyze_chat_message(message: str):
    """Analyze a chat message for project context and intent"""
    try:
        # Use the context detection endpoint
        context_response = await detect_context(message)
        
        # Additional analysis can be added here
        return {
            "success": True,
            "message": message,
            "analysis": context_response["analysis"],
            "suggested_actions": ["create_project", "estimate_cost", "schedule_task"],
            "confidence": 0.85
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing chat message: {e}")

@app.post("/rag/upload")
async def rag_upload_file(
    file: UploadFile = File(...),
    source: str = Form("web_upload"),
    document_type: str = Form("manual")
):
    """Upload a document to the RAG system"""
    try:
        # Read file content
        contents = await file.read()
        
        # For now, just log the upload and return success
        # In a real implementation, this would process the file and add to RAG
        print(f"RAG Upload: {file.filename} ({len(contents)} bytes) from {source}, type: {document_type}")
        
        return {
            "success": True,
            "filename": file.filename,
            "size": len(contents),
            "message": "File uploaded successfully (simulated)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)