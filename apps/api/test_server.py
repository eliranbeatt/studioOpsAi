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
    {"id": "1", "name": "Home Center", "contact": "03-1234567", "url": "https://homecenter.co.il", "rating": 4.5, "notes": "Good for basic materials"},
    {"id": "2", "name": "ACE Hardware", "contact": "03-7654321", "url": "https://ace.co.il", "rating": 4.2, "notes": "Professional tools"}
]

mock_materials = [
    {"id": "1", "name": "Plywood 4x8", "spec": "18mm", "unit": "sheet", "category": "wood", "typical_waste_pct": 10.0, "notes": "Standard plywood"},
    {"id": "2", "name": "2x4 Lumber", "spec": "2x4x8", "unit": "piece", "category": "wood", "typical_waste_pct": 5.0, "notes": "Construction lumber"}
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

@app.get("/api/vendors")
async def get_vendors():
    """Get all vendors"""
    return mock_vendors

@app.get("/api/materials")
async def get_materials():
    """Get all materials"""
    return mock_materials

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)