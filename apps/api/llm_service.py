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
import time
from openai import RateLimitError, APIError, APIConnectionError

class LLMService:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('LITELLM_MODEL', 'gpt-3.5-turbo')
        
        if self.api_key and self.api_key.startswith('sk-'):
            try:
                self.client = OpenAI(api_key=self.api_key)
                # Test the connection with a simple API call
                self._test_api_connection()
                self.use_openai = True
                print(f"OpenAI integration enabled with model: {self.model}")
            except Exception as e:
                print(f"OpenAI client initialization failed: {e}")
                self.client = None
                self.use_openai = False
                print("Falling back to mock responses due to API connection issues")
        else:
            print("OpenAI API key not configured or invalid - using fallback responses")
            self.client = None
            self.use_openai = False
    
    def _test_api_connection(self):
        """Test OpenAI API connection and key validation"""
        try:
            # Make a minimal API call to test the connection
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            print("OpenAI API connection test successful")
        except Exception as e:
            print(f"OpenAI API connection test failed: {e}")
            raise e
    
    async def _call_openai_with_retry(self, messages: List[Dict], max_retries: int = 3) -> str:
        """Call OpenAI API with retry logic for rate limits"""
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content
                
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1  # Exponential backoff
                    print(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
            except (APIConnectionError, APIError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"API error, waiting {wait_time} seconds before retry {attempt + 1}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
    
    async def generate_response(self, message: str, session_id: str = None, project_context: dict = None) -> dict:
        """Generate AI response with context and memory"""
        
        print(f"DEBUG: generate_response called with session_id: {session_id}")
        
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
                # Call OpenAI API with retry logic for rate limits
                ai_response = await self._call_openai_with_retry(messages)
                
                # Generate proper UUID session ID if not provided
                if not session_id:
                    session_id = str(uuid.uuid4())
                    print(f"DEBUG: Generated new UUID session_id: {session_id}")
                elif session_id.startswith('session_'):
                    # Convert old format to UUID
                    old_session_id = session_id
                    session_id = str(uuid.uuid4())
                    print(f"DEBUG: Converted session_id from {old_session_id} to {session_id}")
                
                # Save conversation to database
                await self._save_conversation(session_id, message, ai_response, project_context)
                
                return {
                    "message": ai_response,
                    "suggest_plan": self._should_suggest_plan(message, ai_response),
                    "session_id": session_id
                }
                
            except RateLimitError as e:
                print(f"OpenAI rate limit exceeded: {e}")
                return await self._fallback_response(message, project_context, "Rate limit exceeded. Using fallback response.")
            except APIConnectionError as e:
                print(f"OpenAI connection error: {e}")
                return await self._fallback_response(message, project_context, "Connection error. Using fallback response.")
            except APIError as e:
                print(f"OpenAI API error: {e}")
                return await self._fallback_response(message, project_context, "API error. Using fallback response.")
            except Exception as e:
                print(f"Unexpected OpenAI error: {e}")
                return await self._fallback_response(message, project_context, "Unexpected error. Using fallback response.")
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
        """Save conversation to database with proper session and project linking"""
        db = next(get_db())
        try:
            import uuid as uuid_module
            
            # Convert session_id to UUID if it's a string
            if isinstance(session_id, str):
                session_uuid = uuid_module.UUID(session_id)
            else:
                session_uuid = session_id
            
            # Extract project_id from project_context if available
            project_id = None
            if project_context and isinstance(project_context, dict):
                project_id_str = project_context.get('project_id') or project_context.get('id')
                if project_id_str:
                    project_id = uuid_module.UUID(project_id_str) if isinstance(project_id_str, str) else project_id_str
            
            # Ensure chat session exists
            existing_session = db.query(ChatSession).filter(ChatSession.id == session_uuid).first()
            if not existing_session:
                # Create new chat session with project link
                new_session = ChatSession(
                    id=session_uuid,
                    project_id=project_id,
                    title=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    context=project_context,
                    is_active=True
                )
                db.add(new_session)
                db.flush()  # Ensure session is created before adding messages
            
            # Save user message
            user_msg = ChatMessage(
                session_id=session_uuid,
                message=message,
                response="",  # No response for user messages
                is_user=True,
                project_context=project_context
            )
            db.add(user_msg)
            
            # Save AI response
            ai_msg = ChatMessage(
                session_id=session_uuid,
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
        
        # Generate proper UUID session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"DEBUG: Generated new UUID session_id in fallback: {session_id}")
        elif session_id.startswith('session_'):
            # Convert old format to UUID
            old_session_id = session_id
            session_id = str(uuid.uuid4())
            print(f"DEBUG: Converted session_id in fallback from {old_session_id} to {session_id}")
        
        # Save conversation to database
        await self._save_conversation(session_id, message, response, project_context)
        
        return {
            "message": response,
            "suggest_plan": True,
            "session_id": session_id
        }
    
    async def _fallback_response(self, message: str, project_context: dict = None, error_msg: str = None) -> dict:
        """Simple fallback response when OpenAI fails"""
        response = await self._enhanced_fallback_response(message, [], project_context)
        if error_msg:
            response["error_info"] = error_msg
        return response

# Global instance
llm_service = LLMService()