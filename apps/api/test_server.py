#!/usr/bin/env python3
"""
Simple test server for StudioOps AI API
This runs without database dependencies for testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
import time
import uvicorn

app = FastAPI(
    title="StudioOps AI API",
    description="Core API for StudioOps AI project management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    project_id: Optional[str] = None

# Mock data for testing
mock_vendors = [
    {"id": "1", "name": "Home Center", "contact": "03-1234567", "url": "https://homecenter.co.il", "rating": 4.5, "notes": "Good for basic materials", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"},
    {"id": "2", "name": "ACE Hardware", "contact": "03-7654321", "url": "https://ace.co.il", "rating": 4.2, "notes": "Professional tools", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"}
]

mock_materials = [
    {"id": "1", "name": "Plywood 4x8", "spec": "18mm", "unit": "sheet", "category": "wood", "typical_waste_pct": 10.0, "notes": "Standard plywood", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"},
    {"id": "2", "name": "2x4 Lumber", "spec": "2x4x8", "unit": "piece", "category": "wood", "typical_waste_pct": 5.0, "notes": "Construction lumber", "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"}
]

mock_projects = [
    {"id": "1", "name": "Kitchen Renovation", "client_name": "John Doe", "status": "active", "start_date": "2024-01-15", "due_date": "2024-03-15", "budget_planned": 50000, "budget_actual": 0, "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"},
    {"id": "2", "name": "Bathroom Remodel", "client_name": "Jane Smith", "status": "draft", "start_date": "2024-02-01", "due_date": "2024-04-01", "budget_planned": 30000, "budget_actual": 0, "created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-01T00:00:00Z"}
]

async def simulate_ai_response(message: str):
    """Simulate AI response generation"""
    responses = {
        "hello": "שלום! איך אני יכול לעזור לך עם הפרויקט היום?",
        "project": "אשמח לעזור עם התכנון. תאר לי את הפרויקט ואתן לך המלצות.",
        "price": "אני יכול לעזור עם תמחור. איזה חומרים אתה צריך?",
        "plan": "בוא ניצור תוכנית עבודה מפורטת לפרויקט שלך.",
        "default": "מצוין! אני כאן כדי לעזור עם ניהול הפרויקט. אוכל לסייע בתכנון, תמחור, יצירת תוכנית עבודה או ייצוא ל-Trello."
    }
    
    message_lower = message.lower()
    
    if "hello" in message_lower or "hi" in message_lower or "שלום" in message_lower:
        return responses["hello"]
    elif "project" in message_lower or "פרויקט" in message_lower:
        return responses["project"]
    elif "price" in message_lower or "מחיר" in message_lower or "תמחור" in message_lower:
        return responses["price"]
    elif "plan" in message_lower or "תוכנית" in message_lower:
        return responses["plan"]
    else:
        return responses["default"]

@app.get("/")
async def root():
    return {"message": "StudioOps AI API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "mock_mode",
        "service": "studioops-api"
    }

@app.get("/api/health")
async def api_health():
    """API health endpoint"""
    return {"status": "ok", "service": "studioops-api"}

@app.post("/api/chat/message")
async def chat_message(chat_message: ChatMessage):
    """Simple chat endpoint (non-streaming)"""
    try:
        response = await simulate_ai_response(chat_message.message)
        
        # Check if the message suggests creating a plan
        should_suggest_plan = any(word in chat_message.message.lower() for word in [
            'plan', 'תוכנית', 'project', 'פרויקט', 'build', 'בנייה', 'create', 'יצירה'
        ])
        
        return {
            "message": response,
            "context": {
                "assumptions": ["הנחה 1", "הנחה 2"],
                "risks": ["סיכון 1", "סיכון 2"],
                "suggestions": ["הצעה 1", "הצעה 2"]
            },
            "suggest_plan": should_suggest_plan,
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {e}")

@app.post("/api/chat/generate_plan")
async def generate_plan_skeleton(plan_request: dict):
    """Generate a plan skeleton from chat context"""
    try:
        project_name = plan_request.get('project_name', 'New Project')
        project_description = plan_request.get('project_description', '')
        
        # Mock plan generation
        items = [
            {
                "category": "materials",
                "title": "Plywood 4x8",
                "description": "Standard plywood sheet",
                "quantity": 5.0,
                "unit": "sheet",
                "unit_price": 120.0,
                "subtotal": 600.0
            },
            {
                "category": "materials",
                "title": "2x4 Lumber",
                "description": "Construction lumber",
                "quantity": 20.0,
                "unit": "piece",
                "unit_price": 25.0,
                "subtotal": 500.0
            },
            {
                "category": "labor",
                "title": "Carpenter work",
                "description": "Professional carpentry services",
                "quantity": 16.0,
                "unit": "hour",
                "unit_price": 150.0,
                "subtotal": 2400.0
            }
        ]
        
        total = sum(item["subtotal"] for item in items)
        
        plan_skeleton = {
            "project_id": plan_request.get('project_id'),
            "project_name": project_name,
            "items": items,
            "total": total,
            "margin_target": 0.25,
            "currency": "NIS",
            "metadata": {
                "generated_at": time.time(),
                "items_count": len(items),
                "materials_count": len([i for i in items if i['category'] == 'materials']),
                "labor_count": len([i for i in items if i['category'] == 'labor'])
            }
        }
        
        return plan_skeleton
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan: {e}")

@app.get("/projects")
async def get_projects():
    """Get all projects"""
    return mock_projects

@app.post("/projects")
async def create_project(project: dict):
    """Create a new project"""
    new_project = {
        "id": str(len(mock_projects) + 1),
        "name": project.get("name", "New Project"),
        "client_name": project.get("client_name"),
        "status": project.get("status", "draft"),
        "start_date": project.get("start_date"),
        "due_date": project.get("due_date"),
        "budget_planned": project.get("budget_planned"),
        "budget_actual": 0,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    mock_projects.append(new_project)
    return new_project

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    global mock_projects
    mock_projects = [p for p in mock_projects if p["id"] != project_id]
    return {"message": "Project deleted successfully"}

@app.get("/vendors")
async def get_vendors():
    """Get all vendors"""
    return mock_vendors

@app.post("/vendors")
async def create_vendor(vendor: dict):
    """Create a new vendor"""
    new_vendor = {
        "id": str(len(mock_vendors) + 1),
        "name": vendor.get("name", "New Vendor"),
        "contact": vendor.get("contact"),
        "url": vendor.get("url"),
        "rating": vendor.get("rating"),
        "notes": vendor.get("notes"),
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    mock_vendors.append(new_vendor)
    return new_vendor

@app.delete("/vendors/{vendor_id}")
async def delete_vendor(vendor_id: str):
    """Delete a vendor"""
    global mock_vendors
    mock_vendors = [v for v in mock_vendors if v["id"] != vendor_id]
    return {"message": "Vendor deleted successfully"}

@app.get("/materials")
async def get_materials():
    """Get all materials"""
    return mock_materials

@app.post("/materials")
async def create_material(material: dict):
    """Create a new material"""
    new_material = {
        "id": str(len(mock_materials) + 1),
        "name": material.get("name", "New Material"),
        "spec": material.get("spec"),
        "unit": material.get("unit", "unit"),
        "category": material.get("category"),
        "typical_waste_pct": material.get("typical_waste_pct", 0),
        "notes": material.get("notes"),
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
    mock_materials.append(new_material)
    return new_material

@app.delete("/materials/{material_id}")
async def delete_material(material_id: str):
    """Delete a material"""
    global mock_materials
    mock_materials = [m for m in mock_materials if m["id"] != material_id]
    return {"message": "Material deleted successfully"}

@app.post("/chat")
async def chat_message_v2(chat_message: ChatMessage):
    """Direct chat endpoint without /api prefix"""
    try:
        response = await simulate_ai_response(chat_message.message)
        
        # Check if the message suggests creating a plan
        should_suggest_plan = any(word in chat_message.message.lower() for word in [
            'plan', 'תוכנית', 'project', 'פרויקט', 'build', 'בנייה', 'create', 'יצירה'
        ])
        
        return {
            "message": response,
            "response": response,  # Alternative field name
            "context": {
                "assumptions": ["הנחה 1", "הנחה 2"],
                "risks": ["סיכון 1", "סיכון 2"],
                "suggestions": ["הצעה 1", "הצעה 2"]
            },
            "suggests_plan": should_suggest_plan,
            "suggest_plan": should_suggest_plan,
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {e}")

@app.post("/plans/generate")
async def generate_plan_v2(plan_request: dict):
    """Direct plan generation endpoint without /api prefix"""
    try:
        project_name = plan_request.get('project_name', 'New Project')
        project_description = plan_request.get('project_description', '')
        
        # Mock plan generation
        items = [
            {
                "category": "materials",
                "title": "Plywood 4x8",
                "description": "Standard plywood sheet",
                "quantity": 5.0,
                "unit": "sheet",
                "unit_price": 120.0,
                "subtotal": 600.0
            },
            {
                "category": "materials",
                "title": "2x4 Lumber",
                "description": "Construction lumber",
                "quantity": 20.0,
                "unit": "piece",
                "unit_price": 25.0,
                "subtotal": 500.0
            },
            {
                "category": "labor",
                "title": "Carpenter work",
                "description": "Professional carpentry services",
                "quantity": 16.0,
                "unit": "hour",
                "unit_price": 150.0,
                "subtotal": 2400.0
            }
        ]
        
        total = sum(item["subtotal"] for item in items)
        
        plan_skeleton = {
            "project_id": plan_request.get('project_id'),
            "project_name": project_name,
            "items": items,
            "total": total,
            "margin_target": 0.25,
            "currency": "NIS",
            "metadata": {
                "generated_at": time.time(),
                "items_count": len(items),
                "materials_count": len([i for i in items if i['category'] == 'materials']),
                "labor_count": len([i for i in items if i['category'] == 'labor'])
            }
        }
        
        return plan_skeleton
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)