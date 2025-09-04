from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import json
import asyncio
import time
from pydantic import BaseModel
from services.pricing_resolver import pricing_resolver
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    message: str
    project_id: Optional[str] = None
    session_id: Optional[str] = None

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

async def get_project_context(project_id: str) -> Dict[str, Any]:
    """Get project context from database"""
    if not project_id:
        return {}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, name, client_name, status, start_date, due_date, budget_planned
            FROM projects WHERE id = %s
        """, (project_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                "project_id": row[0],
                "project_name": row[1],
                "client_name": row[2],
                "status": row[3],
                "start_date": row[4].isoformat() if row[4] else None,
                "due_date": row[5].isoformat() if row[5] else None,
                "budget_planned": float(row[6]) if row[6] else None
            }
        return {}
        
    finally:
        cursor.close()
        conn.close()

async def get_chat_history(session_id: str, limit: int = 10) -> List[Dict]:
    """Get chat history for context"""
    if not session_id:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT message, response, is_user, created_at
            FROM chat_messages 
            WHERE session_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (session_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "message": row[0],
                "response": row[1],
                "is_user": row[2],
                "timestamp": row[3].isoformat()
            })
        
        return history
        
    finally:
        cursor.close()
        conn.close()

async def search_rag_documents(search_term: str, limit: int = 5) -> List[Dict]:
    """Search RAG documents for relevant information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT title, content, document_type
            FROM rag_documents 
            WHERE is_active = true 
            AND (title ILIKE %s OR content ILIKE %s)
            ORDER BY created_at DESC 
            LIMIT %s
        """, (f"%{search_term}%", f"%{search_term}%", limit))
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                "title": row[0],
                "content": row[1][:200] + "..." if len(row[1]) > 200 else row[1],
                "type": row[2]
            })
        
        return documents
        
    finally:
        cursor.close()
        conn.close()

async def simulate_ai_response(message: str, project_id: str = None, session_id: str = None):
    """Enhanced AI response generation with database context"""
    
    message_lower = message.lower()
    
    # Get context from database
    project_context = await get_project_context(project_id) if project_id else {}
    chat_history = await get_chat_history(session_id) if session_id else []
    
    # Extract keywords for RAG search
    keywords = extract_keywords(message)
    rag_context = []
    if keywords:
        for keyword in keywords[:3]:  # Search top 3 keywords
            docs = await search_rag_documents(keyword, limit=2)
            rag_context.extend(docs)
    
    # Build context-aware response
    context_info = ""
    if project_context:
        context_info += f"\nProject: {project_context.get('project_name', 'Unknown')}"
        if project_context.get('client_name'):
            context_info += f" for {project_context['client_name']}"
    
    if rag_context:
        context_info += "\nRelevant knowledge:"
        for doc in rag_context:
            context_info += f"\n- {doc['title']}: {doc['content']}"
    
    # Context-aware responses
    if "hello" in message_lower or "hi" in message_lower or "hey" in message_lower:
        greeting = "שלום!" if any(char in message for char in "אבגדהוזחטיכלמנסעפצקרשת") else "Hello!"
        return f"{greeting} איך אני יכול לעזור לך עם הפרויקט היום?{context_info}"
    
    elif "project" in message_lower or "פרויקט" in message_lower:
        if project_context:
            return f"אשמח לעזור עם הפרויקט '{project_context.get('project_name')}'.{context_info} תאר לי מה אתה צריך לעשות ואתן לך המלצות מפורטות."
        else:
            return "אשמח לעזור עם התכנון. תאר לי את הפרויקט ואתן לך המלצות כולל חומרים, עבודה, ותמחור.{context_info}"
    
    elif "price" in message_lower or "מחיר" in message_lower or "תמחור" in message_lower:
        return f"אני יכול לעזור עם תמחור מדויק.{context_info} איזה חומרים או עבודה אתה צריך לתמחר?"
    
    elif "plan" in message_lower or "תוכנית" in message_lower or "schedule" in message_lower:
        return f"בוא ניצור תוכנית עבודה מפורטת.{context_info} אכלול חומרים, עבודה, לוח זמנים, ותמחור מדויק."
    
    elif "status" in message_lower or "stat" in message_lower or "status" in message_lower:
        if project_context:
            status = project_context.get('status', 'unknown')
            return f"סטטוס הפרויקט '{project_context.get('project_name')}' הוא: {status}.{context_info}"
        else:
            return "אשמח לבדוק סטטוס פרויקט. אנא ציין את מזהה הפרויקט.{context_info}"
    
    elif "material" in message_lower or "חומר" in message_lower or "wood" in message_lower:
        return f"אני יכול לעזור עם בחירת חומרים.{context_info} איזה סוג עבודה אתה מתכנן?"
    
    else:
        return f"מצוין! אני כאן כדי לעזור עם ניהול הפרויקט.{context_info} אוכל לסייע בתכנון, תמחור, יצירת תוכנית עבודה, או מעקב אחר התקדמות."

def extract_keywords(message: str) -> List[str]:
    """Extract relevant keywords from message for RAG search"""
    message_lower = message.lower()
    
    # Common project-related keywords
    keywords = []
    
    # Project types
    project_types = [
        'cabinet', 'kitchen', 'furniture', 'table', 'chair', 'desk', 'shelf',
        'painting', 'paint', 'wall', 'ceiling', 'electrical', 'wiring', 'light',
        'plumbing', 'pipe', 'sink', 'toilet', 'renovation', 'remodel', 'build',
        'construction', 'deck', 'patio', 'door', 'window', 'floor', 'tile'
    ]
    
    # Materials
    materials = [
        'wood', 'plywood', 'lumber', '2x4', 'pine', 'oak', 'maple', 'screw',
        'nail', 'hinge', 'paint', 'stain', 'varnish', 'wire', 'pipe', 'drywall',
        'tile', 'glass', 'metal', 'steel', 'aluminum', 'plastic', 'laminate'
    ]
    
    # Hebrew keywords
    hebrew_keywords = [
        'עץ', 'פlywood', 'קרש', 'בורג', 'מסמר', 'צבע', 'לכה', 'חוט', 'צינור',
        'גבס', 'אריח', 'זכוכית', 'מתכת', 'פלדה', 'אלומיניום', 'פלסטיק', 'למינציה'
    ]
    
    # Check for keywords in message
    all_keywords = project_types + materials + hebrew_keywords
    for keyword in all_keywords:
        if keyword in message_lower:
            keywords.append(keyword)
    
    return keywords

async def generate_streaming_response(message: str, project_id: str = None, session_id: str = None):
    """Generate streaming response for SSE with context"""
    response = await simulate_ai_response(message, project_id, session_id)
    
    # Simulate streaming by sending words one by one
    words = response.split()
    for i, word in enumerate(words):
        yield f"data: {json.dumps({'token': word + ' ', 'finished': i == len(words) - 1})}\n\n"
        await asyncio.sleep(0.1)

@router.post("/stream")
async def chat_stream(chat_message: ChatMessage):
    """Streaming chat endpoint with SSE"""
    return StreamingResponse(
        generate_streaming_response(
            chat_message.message, 
            chat_message.project_id, 
            chat_message.session_id
        ),
        media_type="text/event-stream"
    )

@router.post("/message")
async def chat_message(chat_message: ChatMessage):
    """Simple chat endpoint (non-streaming) with context"""
    try:
        response = await simulate_ai_response(
            chat_message.message, 
            chat_message.project_id, 
            chat_message.session_id
        )
        
        # Check if the message suggests creating a plan
        should_suggest_plan = any(word in chat_message.message.lower() for word in [
            'plan', 'תוכנית', 'project', 'פרויקט', 'build', 'בנייה', 'create', 'יצירה'
        ])
        
        # Get actual context from database
        project_context = await get_project_context(chat_message.project_id) if chat_message.project_id else {}
        rag_context = []
        if chat_message.message:
            keywords = extract_keywords(chat_message.message)
            if keywords:
                for keyword in keywords[:2]:
                    docs = await search_rag_documents(keyword, limit=1)
                    rag_context.extend(docs)
        
        return {
            "message": response,
            "context": {
                "project": project_context,
                "rag_documents": rag_context,
                "assumptions": ["מחירים מעודכנים לפי ספקים נוכחיים", "זמני עבודה לפי ניסיון קודם"],
                "risks": ["זמינות חומרים עשויה להשתנות", "שינויים בלוח הזמנים אפשריים"],
                "suggestions": ["מומלץ לקבל הצעות מחיר מכמה ספקים", "לתכנן מרווח ביטחון של 15% בעלויות"]
            },
            "suggest_plan": should_suggest_plan,
            "session_id": chat_message.session_id or f"session_{int(time.time())}",
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