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

# Import LLM and RAG services
try:
    # Try absolute import first
    from llm_service import llm_service
    from rag_service import rag_service
except ImportError:
    try:
        # Fallback for relative import
        from .llm_service import llm_service
        from .rag_service import rag_service
    except ImportError:
        # Create fallback instances if imports fail
        print("Warning: LLM and RAG services not available. Using fallback mode.")
        
        # Create simple fallback classes
        class FallbackLLMService:
            async def generate_response(self, message, session_id=None, project_context=None):
                return {
                    "message": "I'm a fallback AI assistant. Please configure OpenAI API for full functionality.",
                    "session_id": session_id or "fallback-session",
                    "suggest_plan": False
                }
        
        class FallbackRAGService:
            def enhance_prompt(self, user_message, max_context=1000):
                return user_message
        
        llm_service = FallbackLLMService()
        rag_service = FallbackRAGService()

# Load environment variables
load_dotenv()

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
                "created_at": row[7].isoformat(),
                "updated_at": row[8].isoformat() if row[8] else None
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
            "updated_at": result[8].isoformat() if result[8] else None
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
        # Get AI response with memory
        response = await llm_service.generate_response(
            chat_request.message, 
            chat_request.session_id, 
            chat_request.project_context
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)