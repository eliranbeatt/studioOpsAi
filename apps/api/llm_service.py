"""LLM service with OpenAI integration and memory"""

import os
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
try:
    from .database import get_db
    from .models import ChatMessage, ChatSession
except ImportError:
    # Fallback for direct import
    from database import get_db
    from models import ChatMessage, ChatSession
import uuid

class LLMService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-5"  # Using GPT-4 Turbo (latest available)
            self.use_openai = True
        else:
            self.client = None
            self.use_openai = False
            print("Warning: OpenAI API key not set. Using fallback responses.")
    
    async def generate_response(self, message: str, session_id: str = None, project_context: dict = None) -> dict:
        """Generate AI response with context and memory"""
        
        # Get conversation history
        conversation_history = await self._get_conversation_history(session_id)
        
        if self.use_openai:
            # Build system prompt with context
            system_prompt = self._build_system_prompt(project_context)
            
            # Prepare messages for OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in conversation_history:
                role = "user" if msg['is_user'] else "assistant"
                messages.append({"role": role, "content": msg['content']})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            try:
                # Call OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
                
                # Save conversation to database
                await self._save_conversation(session_id, message, ai_response, project_context)
                
                return {
                    "message": ai_response,
                    "suggest_plan": self._should_suggest_plan(message, ai_response),
                    "session_id": session_id or str(uuid.uuid4())
                }
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
                # Fallback to mock response if OpenAI fails
                return await self._fallback_response(message, project_context)
        else:
            # Use enhanced fallback response with context
            return await self._enhanced_fallback_response(message, conversation_history, project_context)
    
    async def _get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history from database"""
        if not session_id:
            return []
            
        db = next(get_db())
        try:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.asc()).all()
            
            return [{
                "content": msg.message if msg.is_user else msg.response,
                "is_user": msg.is_user,
                "timestamp": msg.created_at
            } for msg in messages]
            
        except Exception:
            return []
        finally:
            db.close()
    
    def _build_system_prompt(self, project_context: dict = None) -> str:
        """Build system prompt with project context"""
        base_prompt = """You are StudioOps AI, an expert project management assistant for creative studios. 
        You help with project planning, material estimation, pricing, and creative solutions.
        
        CRITICAL LANGUAGE INSTRUCTIONS:
        - DETECT user message language first
        - If user message contains ANY English characters/words, respond in ENGLISH
        - If user message is ONLY in Hebrew characters, respond in HEBREW
        - Default to Hebrew if language detection is unclear
        - NEVER mix languages in the same response
        
        Be helpful, professional, and provide accurate information.
        If you suggest creating a project plan, mention it clearly.
        """
        
        if project_context:
            context_str = json.dumps(project_context, indent=2)
            base_prompt += f"\n\nCurrent project context:\n{context_str}"
        
        return base_prompt
    
    async def _save_conversation(self, session_id: str, message: str, response: str, project_context: dict = None):
        """Save conversation to database"""
        db = next(get_db())
        try:
            # Save user message
            user_msg = ChatMessage(
                session_id=session_id,
                message=message,
                response="",  # No response for user messages
                is_user=True,
                project_context=project_context
            )
            db.add(user_msg)
            
            # Save AI response
            ai_msg = ChatMessage(
                session_id=session_id,
                message="",  # No message for AI responses
                response=response,
                is_user=False,
                project_context=project_context
            )
            db.add(ai_msg)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            print(f"Error saving conversation: {e}")
        finally:
            db.close()
    
    def _should_suggest_plan(self, user_message: str, ai_response: str) -> bool:
        """Determine if we should suggest creating a project plan"""
        plan_keywords = ['plan', 'תוכנית', 'project', 'פרויקט', 'build', 'בנייה', 'create', 'יצירה', 'estimate', 'הערכה']
        
        message_lower = user_message.lower() + " " + ai_response.lower()
        return any(keyword in message_lower for keyword in plan_keywords)
    
    async def _enhanced_fallback_response(self, message: str, conversation_history: List[Dict], project_context: dict = None) -> dict:
        """Enhanced fallback response with context awareness"""
        
        message_lower = message.lower()
        
        # Context-aware responses
        if any(word in message_lower for word in ['cabinet', 'kitchen', 'cupboard', 'storage']):
            response = "I'd be happy to help with your cabinet project! For standard kitchen cabinets, we typically use 3/4 inch plywood for boxes and 1/4 inch for backs. Would you like me to create a detailed plan with material estimates?"
        elif any(word in message_lower for word in ['table', 'desk', 'furniture']):
            response = "That sounds like a great furniture project! For tables and desks, we recommend solid wood or high-quality plywood. I can help you create a detailed plan with material requirements and cost estimates."
        elif any(word in message_lower for word in ['paint', 'painting', 'color']):
            response = "I can help with your painting project! For interior painting, we typically estimate 350-400 square feet per gallon. Would you like me to calculate the paint quantities needed?"
        elif any(word in message_lower for word in ['plan', 'estimate', 'budget', 'cost']):
            response = "I'd be happy to help you create a detailed project plan with cost estimates. Could you provide more details about what you're planning to build?"
        else:
            # Generic helpful response
            responses = [
                "I'd be happy to help you with that project! Could you provide more details about what you're planning to build?",
                "That sounds like an interesting project. Let me help you create a detailed plan and estimate.",
                "I can assist with project planning and material estimation. What specific aspects would you like help with?"
            ]
            import random
            response = random.choice(responses)
        
        # Save conversation to database
        session_id = str(uuid.uuid4())
        await self._save_conversation(session_id, message, response, project_context)
        
        return {
            "message": response,
            "suggest_plan": True,
            "session_id": session_id
        }
    
    async def _fallback_response(self, message: str, project_context: dict = None) -> dict:
        """Simple fallback response when OpenAI fails"""
        return await self._enhanced_fallback_response(message, [], project_context)

# Global instance
llm_service = LLMService()