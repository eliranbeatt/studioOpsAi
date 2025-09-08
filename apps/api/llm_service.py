"""Enhanced LLM service with OpenAI integration, fallback mechanisms, and health monitoring"""

import os
import asyncio
import hashlib
import logging
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta
try:
    from .database import get_db
    from .models import ChatMessage, ChatSession, Project, Document, RAGDocument
except ImportError:
    # Fallback for direct import
    from database import get_db
    from models import ChatMessage, ChatSession, Project, Document, RAGDocument
import uuid
import time
from openai import RateLimitError, APIError, APIConnectionError
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedLLMService:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        
        # Health monitoring
        self.health_status = {
            'api_available': False,
            'last_check': None,
            'consecutive_failures': 0,
            'last_error': None,
            'response_times': []
        }
        
        # Initialize OpenAI client
        self.client = None
        self.use_openai = False
        self._initialize_openai_client()
        
        # Context cache for performance
        self._context_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        logger.info(f"Enhanced LLM Service initialized - OpenAI: {self.use_openai}, Model: {self.model}")
    
    def _initialize_openai_client(self):
        """Initialize OpenAI client with validation"""
        if not self.api_key or not self.api_key.startswith('sk-'):
            logger.warning("OpenAI API key not configured or invalid - using enhanced fallback responses")
            self.use_openai = False
            return
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            # Test the connection
            self._test_api_connection()
            self.use_openai = True
            self.health_status['api_available'] = True
            self.health_status['consecutive_failures'] = 0
            logger.info(f"OpenAI integration enabled with model: {self.model}")
        except Exception as e:
            logger.error(f"OpenAI client initialization failed: {e}")
            self.client = None
            self.use_openai = False
            self.health_status['api_available'] = False
            self.health_status['last_error'] = str(e)
            logger.warning("Falling back to enhanced mock responses due to API connection issues")
    
    def _test_api_connection(self):
        """Test OpenAI API connection and key validation"""
        start_time = time.time()
        try:
            # Make a minimal API call to test the connection
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            
            response_time = time.time() - start_time
            self.health_status['response_times'].append(response_time)
            # Keep only last 10 response times
            if len(self.health_status['response_times']) > 10:
                self.health_status['response_times'] = self.health_status['response_times'][-10:]
            
            self.health_status['last_check'] = datetime.now()
            logger.info(f"OpenAI API connection test successful (response time: {response_time:.2f}s)")
            
        except Exception as e:
            self.health_status['consecutive_failures'] += 1
            self.health_status['last_error'] = str(e)
            self.health_status['last_check'] = datetime.now()
            logger.error(f"OpenAI API connection test failed: {e}")
            raise e
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of the AI service"""
        avg_response_time = None
        if self.health_status['response_times']:
            avg_response_time = sum(self.health_status['response_times']) / len(self.health_status['response_times'])
        
        return {
            'service_name': 'Enhanced LLM Service',
            'api_available': self.health_status['api_available'],
            'use_openai': self.use_openai,
            'model': self.model,
            'last_check': self.health_status['last_check'].isoformat() if self.health_status['last_check'] else None,
            'consecutive_failures': self.health_status['consecutive_failures'],
            'last_error': self.health_status['last_error'],
            'avg_response_time': round(avg_response_time, 3) if avg_response_time else None,
            'cache_size': len(self._context_cache)
        }
    
    async def _call_openai_with_retry(self, messages: List[Dict], max_retries: int = 3) -> str:
        """Call OpenAI API with enhanced retry logic and health monitoring"""
        start_time = time.time()
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                # Update health status on success
                response_time = time.time() - start_time
                self.health_status['response_times'].append(response_time)
                if len(self.health_status['response_times']) > 10:
                    self.health_status['response_times'] = self.health_status['response_times'][-10:]
                
                self.health_status['consecutive_failures'] = 0
                self.health_status['api_available'] = True
                self.health_status['last_check'] = datetime.now()
                
                return response.choices[0].message.content
                
            except RateLimitError as e:
                self.health_status['consecutive_failures'] += 1
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1  # Exponential backoff
                    logger.warning(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.health_status['last_error'] = f"Rate limit exceeded after {max_retries} attempts"
                    raise e
                    
            except (APIConnectionError, APIError) as e:
                self.health_status['consecutive_failures'] += 1
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"API error, waiting {wait_time} seconds before retry {attempt + 1}: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    self.health_status['api_available'] = False
                    self.health_status['last_error'] = str(e)
                    self.health_status['last_check'] = datetime.now()
                    raise e
            
            except Exception as e:
                self.health_status['consecutive_failures'] += 1
                self.health_status['api_available'] = False
                self.health_status['last_error'] = str(e)
                self.health_status['last_check'] = datetime.now()
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.error(f"Unexpected error, waiting {wait_time} seconds before retry {attempt + 1}: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise e
    
    async def generate_response(self, message: str, session_id: str = None, project_context: dict = None) -> dict:
        """Generate AI response with enhanced context retrieval and fallback mechanisms"""
        
        logger.info(f"Generating response for session: {session_id}")
        
        # Generate proper UUID session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new UUID session_id: {session_id}")
        elif session_id.startswith('session_'):
            # Convert old format to UUID
            old_session_id = session_id
            session_id = str(uuid.uuid4())
            logger.info(f"Converted session_id from {old_session_id} to {session_id}")
        
        # Get enhanced context
        enhanced_context = await self._build_enhanced_context(message, session_id, project_context)
        
        if self.use_openai and self.health_status['api_available']:
            try:
                # Attempt real AI response
                ai_response = await self._generate_real_ai_response(message, session_id, enhanced_context)
                
                # Save conversation to database
                await self._save_conversation(session_id, message, ai_response, project_context)
                
                return {
                    "message": ai_response,
                    "suggest_plan": self._should_suggest_plan(message, ai_response),
                    "session_id": session_id,
                    "ai_enabled": True,
                    "context_used": enhanced_context.get('context_summary', {}),
                    "health_status": "healthy"
                }
                
            except Exception as e:
                logger.error(f"Real AI response failed: {e}")
                # Fall back to enhanced mock response
                return await self._generate_enhanced_fallback_response(message, session_id, enhanced_context, error_info=str(e))
        else:
            # Use enhanced fallback response
            return await self._generate_enhanced_fallback_response(message, session_id, enhanced_context)
    
    async def _build_enhanced_context(self, message: str, session_id: str, project_context: dict = None) -> Dict[str, Any]:
        """Build enhanced context from multiple sources"""
        
        # Check cache first
        cache_key = hashlib.md5(f"{session_id}:{message}".encode()).hexdigest()
        if cache_key in self._context_cache:
            cache_entry = self._context_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self._cache_ttl):
                return cache_entry['context']
        
        context = {
            'conversation_history': [],
            'project_data': {},
            'relevant_documents': [],
            'context_summary': {}
        }
        
        try:
            # Get conversation history
            context['conversation_history'] = await self._get_conversation_history(session_id)
            
            # Get project context if available
            if project_context and project_context.get('project_id'):
                context['project_data'] = await self._get_enhanced_project_context(project_context['project_id'])
            
            # Search for relevant documents
            context['relevant_documents'] = await self._search_relevant_documents(message, project_context)
            
            # Build context summary
            context['context_summary'] = {
                'conversation_length': len(context['conversation_history']),
                'has_project_context': bool(context['project_data']),
                'relevant_docs_count': len(context['relevant_documents']),
                'project_name': context['project_data'].get('name', 'Unknown')
            }
            
            # Cache the context
            self._context_cache[cache_key] = {
                'context': context,
                'timestamp': datetime.now()
            }
            
            # Clean old cache entries
            self._clean_context_cache()
            
        except Exception as e:
            logger.error(f"Error building enhanced context: {e}")
        
        return context
    
    async def _generate_real_ai_response(self, message: str, session_id: str, enhanced_context: Dict[str, Any]) -> str:
        """Generate response using real AI service with enhanced context"""
        
        # Build comprehensive system prompt
        system_prompt = self._build_enhanced_system_prompt(enhanced_context)
        
        # Prepare messages for OpenAI
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limit to last 10 exchanges to manage token usage)
        conversation_history = enhanced_context.get('conversation_history', [])
        recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
        
        for msg in recent_history:
            role = "user" if msg['is_user'] else "assistant"
            content = msg['content']
            if content and content.strip():
                messages.append({"role": role, "content": content})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI API with retry logic
        return await self._call_openai_with_retry(messages)
    
    async def _generate_enhanced_fallback_response(self, message: str, session_id: str, 
                                                 enhanced_context: Dict[str, Any], 
                                                 error_info: str = None) -> Dict[str, Any]:
        """Generate enhanced fallback response with context awareness"""
        
        message_lower = message.lower()
        project_data = enhanced_context.get('project_data', {})
        conversation_history = enhanced_context.get('conversation_history', [])
        relevant_docs = enhanced_context.get('relevant_documents', [])
        
        # Context-aware response generation
        response = await self._generate_contextual_mock_response(
            message, message_lower, project_data, conversation_history, relevant_docs
        )
        
        # Save conversation to database
        await self._save_conversation(session_id, message, response, project_data)
        
        return {
            "message": response,
            "suggest_plan": self._should_suggest_plan(message, response),
            "session_id": session_id,
            "ai_enabled": False,
            "mock_mode": True,
            "context_used": enhanced_context.get('context_summary', {}),
            "health_status": "fallback",
            "error_info": error_info
        }
    
    async def _get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history from database with enhanced error handling"""
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
                "timestamp": msg.created_at.isoformat() if msg.created_at else None
            } for msg in messages if (msg.message and msg.is_user) or (msg.response and not msg.is_user)]
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
        finally:
            db.close()
    
    async def _get_enhanced_project_context(self, project_id: str) -> Dict[str, Any]:
        """Get enhanced project context from database"""
        if not project_id:
            return {}
        
        db = next(get_db())
        try:
            # Get project details
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {}
            
            # Get project documents count
            doc_count = db.query(Document).filter(Document.project_id == project_id).count()
            
            # Get recent chat sessions for this project
            recent_sessions = db.query(ChatSession).filter(
                and_(ChatSession.project_id == project_id, ChatSession.is_active == True)
            ).order_by(desc(ChatSession.updated_at)).limit(3).all()
            
            return {
                'id': str(project.id),
                'name': project.name,
                'client_name': project.client_name,
                'status': project.status,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'due_date': project.due_date.isoformat() if project.due_date else None,
                'budget_planned': float(project.budget_planned) if project.budget_planned else None,
                'budget_actual': float(project.budget_actual) if project.budget_actual else None,
                'document_count': doc_count,
                'recent_sessions_count': len(recent_sessions),
                'board_id': project.board_id
            }
            
        except Exception as e:
            logger.error(f"Error retrieving project context: {e}")
            return {}
        finally:
            db.close()
    
    async def _search_relevant_documents(self, message: str, project_context: dict = None) -> List[Dict[str, Any]]:
        """Search for relevant documents based on message content"""
        db = next(get_db())
        try:
            # Extract keywords from message
            keywords = self._extract_keywords_from_message(message)
            if not keywords:
                return []
            
            # Search in RAG documents
            rag_docs = []
            for keyword in keywords[:3]:  # Limit to top 3 keywords
                docs = db.query(RAGDocument).filter(
                    and_(
                        RAGDocument.is_active == True,
                        RAGDocument.content.ilike(f'%{keyword}%')
                    )
                ).limit(2).all()
                
                for doc in docs:
                    rag_docs.append({
                        'id': doc.id,
                        'title': doc.title,
                        'content': doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                        'type': doc.document_type,
                        'source': 'rag'
                    })
            
            # Search in project documents if project context available
            project_docs = []
            if project_context and project_context.get('project_id'):
                docs = db.query(Document).filter(
                    Document.project_id == project_context['project_id']
                ).limit(3).all()
                
                for doc in docs:
                    project_docs.append({
                        'id': doc.id,
                        'filename': doc.filename,
                        'type': doc.type,
                        'size_bytes': doc.size_bytes,
                        'source': 'project'
                    })
            
            return rag_docs + project_docs
            
        except Exception as e:
            logger.error(f"Error searching relevant documents: {e}")
            return []
        finally:
            db.close()
    
    def _extract_keywords_from_message(self, message: str) -> List[str]:
        """Extract relevant keywords from message for document search"""
        message_lower = message.lower()
        
        # Common project-related keywords
        keywords = []
        
        # Project types and materials
        project_keywords = [
            'cabinet', 'kitchen', 'furniture', 'table', 'chair', 'desk', 'shelf',
            'painting', 'paint', 'wall', 'ceiling', 'electrical', 'wiring', 'light',
            'plumbing', 'pipe', 'sink', 'toilet', 'renovation', 'remodel', 'build',
            'construction', 'deck', 'patio', 'door', 'window', 'floor', 'tile',
            'wood', 'plywood', 'lumber', 'screw', 'nail', 'hinge', 'stain', 'varnish'
        ]
        
        # Hebrew keywords
        hebrew_keywords = [
            'ארון', 'מטבח', 'רהיט', 'שולחן', 'כיסא', 'שולחן עבודה', 'מדף',
            'צביעה', 'צבע', 'קיר', 'תקרה', 'חשמל', 'תאורה',
            'אינסטלציה', 'צינור', 'כיור', 'שירותים', 'שיפוץ', 'בנייה',
            'דק', 'פטיו', 'דלת', 'חלון', 'רצפה', 'אריח',
            'עץ', 'פלייווד', 'קרש', 'בורג', 'מסמר', 'ציר', 'מורדן', 'לכה'
        ]
        
        # Check for keywords in message
        all_keywords = project_keywords + hebrew_keywords
        for keyword in all_keywords:
            if keyword in message_lower:
                keywords.append(keyword)
        
        return keywords[:5]  # Return top 5 keywords
    
    def _clean_context_cache(self):
        """Clean expired entries from context cache"""
        current_time = datetime.now()
        expired_keys = [
            key for key, value in self._context_cache.items()
            if current_time - value['timestamp'] > timedelta(seconds=self._cache_ttl)
        ]
        
        for key in expired_keys:
            del self._context_cache[key]
    
    def _build_enhanced_system_prompt(self, enhanced_context: Dict[str, Any]) -> str:
        """Build enhanced system prompt with comprehensive context"""
        
        base_prompt = """You are StudioOps AI, an expert project management assistant for creative studios in Israel. 
        You help with project planning, material estimation, pricing, and creative solutions.
        
        CRITICAL LANGUAGE INSTRUCTIONS:
        - DETECT user message language first
        - If user message contains ANY English characters/words, respond in ENGLISH
        - If user message is ONLY in Hebrew characters, respond in HEBREW
        - Default to Hebrew if language detection is unclear
        - NEVER mix languages in the same response
        
        CONTEXT AWARENESS:
        - Use conversation history to maintain context and avoid repetition
        - Reference project details when relevant
        - Incorporate information from relevant documents when available
        - Provide specific, actionable advice based on the project type and requirements
        
        Be helpful, professional, and provide accurate information.
        If you suggest creating a project plan, mention it clearly.
        """
        
        # Add project context
        project_data = enhanced_context.get('project_data', {})
        if project_data:
            base_prompt += f"\n\nCURRENT PROJECT CONTEXT:"
            base_prompt += f"\n- Project: {project_data.get('name', 'Unknown')}"
            if project_data.get('client_name'):
                base_prompt += f"\n- Client: {project_data['client_name']}"
            base_prompt += f"\n- Status: {project_data.get('status', 'Unknown')}"
            if project_data.get('budget_planned'):
                base_prompt += f"\n- Planned Budget: ₪{project_data['budget_planned']:,.2f}"
            if project_data.get('document_count', 0) > 0:
                base_prompt += f"\n- Documents Available: {project_data['document_count']}"
        
        # Add conversation context
        conversation_history = enhanced_context.get('conversation_history', [])
        if conversation_history:
            base_prompt += f"\n\nCONVERSATION CONTEXT:"
            base_prompt += f"\n- Previous messages in this conversation: {len(conversation_history)}"
            
            # Add summary of recent conversation topics
            recent_topics = self._extract_conversation_topics(conversation_history[-6:])
            if recent_topics:
                base_prompt += f"\n- Recent topics discussed: {', '.join(recent_topics)}"
        
        # Add relevant documents context
        relevant_docs = enhanced_context.get('relevant_documents', [])
        if relevant_docs:
            base_prompt += f"\n\nRELEVANT KNOWLEDGE:"
            for doc in relevant_docs[:3]:  # Limit to top 3 documents
                if doc.get('source') == 'rag':
                    base_prompt += f"\n- {doc.get('title', 'Document')}: {doc.get('content', '')[:100]}..."
                elif doc.get('source') == 'project':
                    base_prompt += f"\n- Project Document: {doc.get('filename', 'Unknown')} ({doc.get('type', 'unknown type')})"
        
        return base_prompt
    
    def _extract_conversation_topics(self, recent_messages: List[Dict]) -> List[str]:
        """Extract main topics from recent conversation"""
        topics = set()
        
        for msg in recent_messages:
            content = msg.get('content', '').lower()
            
            # Common project topics
            if any(word in content for word in ['cabinet', 'ארון', 'kitchen', 'מטבח']):
                topics.add('kitchen/cabinets')
            if any(word in content for word in ['paint', 'צבע', 'painting', 'צביעה']):
                topics.add('painting')
            if any(word in content for word in ['plan', 'תוכנית', 'planning', 'תכנון']):
                topics.add('planning')
            if any(word in content for word in ['price', 'מחיר', 'cost', 'עלות', 'budget', 'תקציב']):
                topics.add('pricing')
            if any(word in content for word in ['material', 'חומר', 'wood', 'עץ']):
                topics.add('materials')
        
        return list(topics)
    
    async def _generate_contextual_mock_response(self, message: str, message_lower: str, 
                                               project_data: Dict, conversation_history: List[Dict], 
                                               relevant_docs: List[Dict]) -> str:
        """Generate contextually aware mock responses"""
        
        # Detect language
        is_hebrew = any(char in message for char in "אבגדהוזחטיכלמנסעפצקרשת")
        
        # Project-specific responses
        project_name = project_data.get('name', 'הפרויקט' if is_hebrew else 'the project')
        
        # Context-aware response generation
        if any(word in message_lower for word in ['hello', 'hi', 'שלום', 'היי']):
            if is_hebrew:
                response = f"שלום! אני כאן לעזור לך עם {project_name}. איך אוכל לסייע היום?"
            else:
                response = f"Hello! I'm here to help you with {project_name}. How can I assist you today?"
                
        elif any(word in message_lower for word in ['plan', 'תוכנית', 'planning', 'תכנון']):
            if is_hebrew:
                response = f"אשמח ליצור תוכנית מפורטת עבור {project_name}. "
                if project_data.get('budget_planned'):
                    response += f"התקציב המתוכנן הוא ₪{project_data['budget_planned']:,.2f}. "
                response += "האם תרצה שאתחיל ביצירת תוכנית עבודה עם הערכת עלויות?"
            else:
                response = f"I'd be happy to create a detailed plan for {project_name}. "
                if project_data.get('budget_planned'):
                    response += f"The planned budget is ₪{project_data['budget_planned']:,.2f}. "
                response += "Would you like me to start creating a work plan with cost estimates?"
                
        elif any(word in message_lower for word in ['price', 'מחיר', 'cost', 'עלות', 'budget', 'תקציב']):
            if is_hebrew:
                response = f"אני יכול לעזור עם הערכת עלויות עבור {project_name}. "
                if relevant_docs:
                    response += f"יש לי גישה ל-{len(relevant_docs)} מסמכים רלוונטיים. "
                response += "תאר לי את הפרטים הספציפיים ואתן הערכה מדויקת."
            else:
                response = f"I can help with cost estimation for {project_name}. "
                if relevant_docs:
                    response += f"I have access to {len(relevant_docs)} relevant documents. "
                response += "Please describe the specific details and I'll provide an accurate estimate."
                
        elif any(word in message_lower for word in ['material', 'חומר', 'materials', 'חומרים']):
            if is_hebrew:
                response = f"אשמח לעזור עם בחירת חומרים עבור {project_name}. "
                if project_data.get('document_count', 0) > 0:
                    response += f"יש {project_data['document_count']} מסמכים בפרויקט שיכולים לעזור. "
                response += "איזה סוג חומרים אתה מחפש?"
            else:
                response = f"I'd be happy to help with material selection for {project_name}. "
                if project_data.get('document_count', 0) > 0:
                    response += f"There are {project_data['document_count']} documents in the project that can help. "
                response += "What type of materials are you looking for?"
                
        elif any(word in message_lower for word in ['status', 'סטטוס', 'progress', 'התקדמות']):
            if is_hebrew:
                status = project_data.get('status', 'לא ידוע')
                response = f"סטטוס {project_name} הוא: {status}. "
                if len(conversation_history) > 0:
                    response += f"דיברנו על הפרויקט {len(conversation_history)} פעמים. "
                response += "האם תרצה עדכון מפורט על ההתקדמות?"
            else:
                status = project_data.get('status', 'unknown')
                response = f"The status of {project_name} is: {status}. "
                if len(conversation_history) > 0:
                    response += f"We've discussed this project {len(conversation_history)} times. "
                response += "Would you like a detailed progress update?"
                
        else:
            # Generic helpful response
            if is_hebrew:
                response = f"אני כאן לעזור עם {project_name}. "
                if project_data.get('client_name'):
                    response += f"הפרויקט עבור {project_data['client_name']}. "
                response += "אוכל לסייע בתכנון, תמחור, בחירת חומרים, או כל שאלה אחרת."
            else:
                response = f"I'm here to help with {project_name}. "
                if project_data.get('client_name'):
                    response += f"This project is for {project_data['client_name']}. "
                response += "I can assist with planning, pricing, material selection, or any other questions."
        
        return response
    
    async def _save_conversation(self, session_id: str, message: str, response: str, project_context: dict = None):
        """Save conversation to database with enhanced error handling"""
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
                    try:
                        project_id = uuid_module.UUID(project_id_str) if isinstance(project_id_str, str) else project_id_str
                    except ValueError:
                        logger.warning(f"Invalid project_id format: {project_id_str}")
                        project_id = None
            
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
            logger.info(f"Conversation saved successfully for session: {session_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving conversation: {e}")
        finally:
            db.close()
    
    def _should_suggest_plan(self, user_message: str, ai_response: str) -> bool:
        """Determine if we should suggest creating a project plan"""
        plan_keywords = [
            'plan', 'תוכנית', 'project', 'פרויקט', 'build', 'בנייה', 'create', 'יצירה', 
            'estimate', 'הערכה', 'budget', 'תקציב', 'cost', 'עלות', 'material', 'חומר'
        ]
        
        combined_text = (user_message + " " + ai_response).lower()
        return any(keyword in combined_text for keyword in plan_keywords)
    
    async def check_api_health(self) -> Dict[str, Any]:
        """Perform health check on the AI API"""
        if not self.use_openai or not self.client:
            return {
                'status': 'unavailable',
                'message': 'OpenAI API not configured',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            start_time = time.time()
            
            # Simple health check call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "health check"}],
                max_tokens=1
            )
            
            response_time = time.time() - start_time
            
            # Update health status
            self.health_status['api_available'] = True
            self.health_status['consecutive_failures'] = 0
            self.health_status['last_check'] = datetime.now()
            self.health_status['response_times'].append(response_time)
            
            if len(self.health_status['response_times']) > 10:
                self.health_status['response_times'] = self.health_status['response_times'][-10:]
            
            return {
                'status': 'healthy',
                'response_time': round(response_time, 3),
                'model': self.model,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.health_status['api_available'] = False
            self.health_status['consecutive_failures'] += 1
            self.health_status['last_error'] = str(e)
            self.health_status['last_check'] = datetime.now()
            
            return {
                'status': 'unhealthy',
                'error': str(e),
                'consecutive_failures': self.health_status['consecutive_failures'],
                'timestamp': datetime.now().isoformat()
            }

# Global instance
llm_service = EnhancedLLMService()

# Backward compatibility alias
LLMService = EnhancedLLMService