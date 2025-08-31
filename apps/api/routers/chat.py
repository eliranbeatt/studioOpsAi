from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import asyncio
import time
from pydantic import BaseModel

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
        
        return {
            "message": response,
            "context": {
                "assumptions": ["הנחה 1", "הנחה 2"],
                "risks": ["סיכון 1", "סיכון 2"],
                "suggestions": ["הצעה 1", "הצעה 2"]
            },
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {e}")