from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import json
import asyncio
import time
from pydantic import BaseModel
from ..services.pricing_resolver import pricing_resolver

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    message: str
    project_id: Optional[str] = None

async def simulate_ai_response(message: str):
    """Simulate AI response generation"""
    # This is a mock implementation - in production, you would use:
    # 1. Retrieve relevant context from Mem0
    # 2. Use LangChain/LlamaIndex with your LLM
    # 3. Generate response with citations
    
    responses = {
        "hello": "שלום! איך אני יכול לעזור לך עם הפרויקט היום?",
        "project": "אשמח לעזור עם התכנון. תאר לי את הפרויקט ואתן לך המלצות.",
        "price": "אני יכול לעזור עם תמחור. איזה חומרים אתה צריך?",
        "plan": "בוא ניצור תוכנית עבודה מפורטת לפרויקט שלך.",
        "default": "מצוין! אני כאן כדי לעזור עם ניהול הפרויקט. אוכל לסייע בתכנון, תמחור, יצירת תוכנית עבודה או ייצוא ל-Trello."
    }
    
    message_lower = message.lower()
    
    if "hello" in message_lower or "hi" in message_lower:
        return responses["hello"]
    elif "project" in message_lower or "פרויקט" in message_lower:
        return responses["project"]
    elif "price" in message_lower or "מחיר" in message_lower or "תמחור" in message_lower:
        return responses["price"]
    elif "plan" in message_lower or "תוכנית" in message_lower:
        return responses["plan"]
    else:
        return responses["default"]

async def generate_streaming_response(message: str):
    """Generate streaming response for SSE"""
    response = await simulate_ai_response(message)
    
    # Simulate streaming by sending words one by one
    words = response.split()
    for i, word in enumerate(words):
        yield f"data: {json.dumps({'token': word + ' ', 'finished': i == len(words) - 1})}\n\n"
        await asyncio.sleep(0.1)

@router.post("/stream")
async def chat_stream(chat_message: ChatMessage):
    """Streaming chat endpoint with SSE"""
    return StreamingResponse(
        generate_streaming_response(chat_message.message),
        media_type="text/event-stream"
    )

@router.post("/message")
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

class PlanSkeleton(BaseModel):
    project_id: Optional[str] = None
    project_name: str
    items: List[dict]

@router.post("/generate_plan")
async def generate_plan_skeleton(plan_request: dict):
    """Generate a plan skeleton from chat context"""
    try:
        project_name = plan_request.get('project_name', 'New Project')
        project_description = plan_request.get('project_description', '')
        
        # Extract materials from chat context or use defaults
        materials_to_include = []
        
        if 'cabinet' in project_description.lower() or 'furniture' in project_description.lower():
            materials_to_include = ['Plywood 4x8', '2x4 Lumber', 'Screws']
        elif 'painting' in project_description.lower():
            materials_to_include = ['Paint']
        else:
            # Default materials for general projects
            materials_to_include = ['Plywood 4x8', '2x4 Lumber', 'Screws', 'Nails']
        
        # Generate plan items with real pricing
        items = []
        total = 0.0
        
        # Add materials
        for material_name in materials_to_include:
            price_data = pricing_resolver.get_material_price(material_name)
            if price_data:
                # Estimate quantity based on project type
                quantity = _estimate_material_quantity(material_name, project_description)
                subtotal = quantity * price_data['price']
                
                items.append({
                    "category": "materials",
                    "title": price_data['material_name'],
                    "description": f"{material_name} from {price_data['vendor_name']}",
                    "quantity": quantity,
                    "unit": price_data['unit'],
                    "unit_price": price_data['price'],
                    "unit_price_source": {
                        "vendor": price_data['vendor_name'],
                        "confidence": price_data['confidence'],
                        "fetched_at": price_data['fetched_at'].isoformat() if price_data['fetched_at'] else None
                    },
                    "subtotal": round(subtotal, 2)
                })
                total += subtotal
        
        # Add labor
        labor_roles = ['Carpenter']
        if 'painting' in project_description.lower():
            labor_roles.append('Painter')
        if 'electrical' in project_description.lower():
            labor_roles.append('Electrician')
        
        for role in labor_roles:
            labor_data = pricing_resolver.get_labor_rate(role)
            if labor_data:
                # Estimate hours based on project complexity
                hours = _estimate_labor_hours(role, project_description, len(materials_to_include))
                subtotal = hours * labor_data['hourly_rate']
                
                items.append({
                    "category": "labor",
                    "title": f"{role} work",
                    "description": f"{role} services for {project_name}",
                    "quantity": hours,
                    "unit": "hour",
                    "unit_price": labor_data['hourly_rate'],
                    "labor_role": role,
                    "labor_hours": hours,
                    "subtotal": round(subtotal, 2)
                })
                total += subtotal
        
        # Add shipping/logistics
        shipping_data = pricing_resolver.estimate_shipping_cost(100, 50)  # Example: 100kg, 50km
        items.append({
            "category": "logistics",
            "title": "Shipping & Delivery",
            "description": "Material delivery and logistics",
            "quantity": 1,
            "unit": "delivery",
            "unit_price": shipping_data['estimated_cost'],
            "subtotal": round(shipping_data['estimated_cost'], 2)
        })
        total += shipping_data['estimated_cost']
        
        plan_skeleton = {
            "project_id": plan_request.get('project_id'),
            "project_name": project_name,
            "items": items,
            "total": round(total, 2),
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

def _estimate_material_quantity(material_name: str, project_description: str) -> float:
    """Estimate material quantity based on project type"""
    estimates = {
        'Plywood 4x8': 8.0,  # sheets for average project
        '2x4 Lumber': 20.0,  # pieces
        'Screws': 2.0,       # boxes
        'Nails': 1.0,        # lbs
        'Paint': 3.0,        # gallons
        'Drywall': 15.0,     # sheets
    }
    
    # Adjust based on project size keywords
    if 'large' in project_description.lower() or 'big' in project_description.lower():
        return estimates.get(material_name, 1.0) * 1.5
    elif 'small' in project_description.lower() or 'simple' in project_description.lower():
        return estimates.get(material_name, 1.0) * 0.7
    
    return estimates.get(material_name, 1.0)

def _estimate_labor_hours(role: str, project_description: str, materials_count: int) -> float:
    """Estimate labor hours based on role and project complexity"""
    base_hours = {
        'Carpenter': 16.0,
        'Painter': 8.0,
        'Electrician': 6.0,
        'Laborer': 12.0
    }
    
    hours = base_hours.get(role, 8.0)
    
    # Adjust based on project complexity
    if 'complex' in project_description.lower() or 'detailed' in project_description.lower():
        hours *= 1.5
    elif 'simple' in project_description.lower() or 'basic' in project_description.lower():
        hours *= 0.8
    
    # Adjust based on number of materials (proxy for project size)
    if materials_count > 5:
        hours *= 1.3
    elif materials_count < 2:
        hours *= 0.7
    
    return round(hours, 1)