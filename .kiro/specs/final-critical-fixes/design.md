# Design Document - Final Critical System Fixes

## Overview

This design document outlines the comprehensive solution for resolving critical issues in the StudioOps AI system. The fixes address database foreign key constraints, Trello MCP connectivity, document upload functionality, AI response systems, and overall system integration.

## Architecture

### Current System Issues Analysis

1. **Database Schema Issues**
   - Foreign key constraints lack proper ON DELETE actions
   - Mixed ID types between tables (UUID vs VARCHAR)
   - Inconsistent relationship handling

2. **Trello MCP Integration Issues**
   - Missing error handling for API credentials
   - Incomplete request/response validation
   - No graceful degradation when Trello API is unavailable

3. **Document Upload and Processing Issues**
   - MinIO integration not properly configured
   - Document ingestion pipeline has gaps
   - File storage and database record creation not atomic

4. **AI Response System Issues**
   - Mock responses instead of real AI integration
   - No fallback mechanism for AI service failures
   - Context retrieval not working properly

## Components and Interfaces

### 1. Database Schema Fixes

#### Foreign Key Relationship Updates
```sql
-- Update chat_sessions foreign key constraint
ALTER TABLE chat_sessions 
DROP CONSTRAINT IF EXISTS chat_sessions_project_id_fkey;

ALTER TABLE chat_sessions 
ADD CONSTRAINT chat_sessions_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) 
ON DELETE SET NULL;

-- Update documents foreign key constraint  
ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS documents_project_id_fkey;

ALTER TABLE documents 
ADD CONSTRAINT documents_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) 
ON DELETE SET NULL;

-- Update purchases foreign key constraint
ALTER TABLE purchases 
DROP CONSTRAINT IF EXISTS purchases_project_id_fkey;

ALTER TABLE purchases 
ADD CONSTRAINT purchases_project_id_fkey 
FOREIGN KEY (project_id) REFERENCES projects(id) 
ON DELETE SET NULL;
```

#### Project Deletion Service Enhancement
```python
class ProjectDeletionService:
    async def delete_project_safely(self, project_id: UUID, db: Session):
        """Safely delete a project with proper cascade handling"""
        try:
            # 1. Update chat_sessions to remove project reference
            db.execute(
                update(ChatSession)
                .where(ChatSession.project_id == project_id)
                .values(project_id=None)
            )
            
            # 2. Update documents to remove project reference
            db.execute(
                update(Document)
                .where(Document.project_id == project_id)
                .values(project_id=None)
            )
            
            # 3. Update purchases to remove project reference
            db.execute(
                update(Purchase)
                .where(Purchase.project_id == project_id)
                .values(project_id=None)
            )
            
            # 4. Delete plans (CASCADE will handle plan_items)
            db.execute(
                delete(Plan).where(Plan.project_id == project_id)
            )
            
            # 5. Finally delete the project
            db.execute(
                delete(Project).where(Project.id == project_id)
            )
            
            db.commit()
            return {"success": True, "message": "Project deleted successfully"}
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to delete project: {str(e)}"
            )
```

### 2. Trello MCP Server Enhancement

#### Enhanced Error Handling and Validation
```python
class EnhancedTrelloMCPServer:
    def __init__(self):
        self.server = Server("studioops-trello-mcp")
        self.api_key = os.getenv('TRELLO_API_KEY')
        self.token = os.getenv('TRELLO_TOKEN')
        self.base_url = "https://api.trello.com/1"
        
        # Enhanced credential validation
        self.credentials_valid = self._validate_credentials()
        
        if not self.credentials_valid:
            logger.warning(
                "Trello API credentials not configured or invalid. "
                "Trello integration will operate in mock mode."
            )
        
        self.setup_tools()
    
    def _validate_credentials(self) -> bool:
        """Validate Trello API credentials"""
        if not self.api_key or not self.token:
            return False
        
        try:
            # Test API connection
            response = requests.get(
                f"{self.base_url}/members/me",
                params={"key": self.api_key, "token": self.token},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Trello API validation failed: {e}")
            return False
    
    def _make_request_with_retry(self, method: str, endpoint: str, 
                                params: Dict = None, data: Dict = None, 
                                max_retries: int = 3) -> Dict:
        """Make API request with retry logic and enhanced error handling"""
        if not self.credentials_valid:
            return self._mock_response(method, endpoint, params, data)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        auth_params = {"key": self.api_key, "token": self.token}
        
        if params:
            auth_params.update(params)
        
        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    params=auth_params,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Trello API request failed after {max_retries} attempts: {e}")
                    return self._mock_response(method, endpoint, params, data)
                
                wait_time = 2 ** attempt
                time.sleep(wait_time)
        
        return self._mock_response(method, endpoint, params, data)
    
    def _mock_response(self, method: str, endpoint: str, 
                      params: Dict = None, data: Dict = None) -> Dict:
        """Provide mock responses when Trello API is unavailable"""
        if "boards" in endpoint and method.upper() == "POST":
            return {
                "id": f"mock_board_{uuid.uuid4().hex[:8]}",
                "name": params.get("name", "Mock Board"),
                "url": "https://trello.com/b/mock/mock-board",
                "desc": params.get("desc", ""),
                "mock": True
            }
        elif "cards" in endpoint and method.upper() == "POST":
            return {
                "id": f"mock_card_{uuid.uuid4().hex[:8]}",
                "name": params.get("name", "Mock Card"),
                "url": "https://trello.com/c/mock/mock-card",
                "desc": params.get("desc", ""),
                "mock": True
            }
        
        return {"mock": True, "message": "Trello API unavailable, using mock response"}
```

### 3. Document Upload and Processing System

#### Enhanced Document Upload Service
```python
class DocumentUploadService:
    def __init__(self):
        self.minio_client = self._init_minio_client()
        self.bucket_name = "studioops-documents"
        self._ensure_bucket_exists()
    
    def _init_minio_client(self):
        """Initialize MinIO client with proper error handling"""
        try:
            client = Minio(
                endpoint=os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
                access_key=os.getenv('MINIO_ACCESS_KEY', 'studioops'),
                secret_key=os.getenv('MINIO_SECRET_KEY', 'studioops123'),
                secure=os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            )
            
            # Test connection
            client.list_buckets()
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise HTTPException(
                status_code=500,
                detail="Document storage service unavailable"
            )
    
    async def upload_document(self, file: UploadFile, project_id: Optional[UUID] = None,
                            db: Session = None) -> Dict:
        """Upload document with atomic database and storage operations"""
        document_id = str(uuid.uuid4())
        storage_path = f"documents/{document_id}/{file.filename}"
        
        try:
            # 1. Calculate file hash for deduplication
            file_content = await file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # 2. Check for existing document with same hash
            existing_doc = db.query(Document).filter(
                Document.content_sha256 == file_hash
            ).first()
            
            if existing_doc:
                return {
                    "document_id": existing_doc.id,
                    "message": "Document already exists",
                    "duplicate": True
                }
            
            # 3. Upload to MinIO
            file_stream = io.BytesIO(file_content)
            self.minio_client.put_object(
                bucket_name=self.bucket_name,
                object_name=storage_path,
                data=file_stream,
                length=len(file_content),
                content_type=file.content_type or 'application/octet-stream'
            )
            
            # 4. Create database record
            document = Document(
                id=document_id,
                filename=file.filename,
                mime_type=file.content_type,
                size_bytes=len(file_content),
                project_id=project_id,
                storage_path=storage_path,
                content_sha256=file_hash,
                type=self._detect_document_type(file.filename, file_content)
            )
            
            db.add(document)
            db.commit()
            
            # 5. Queue for processing
            await self._queue_document_processing(document_id)
            
            return {
                "document_id": document_id,
                "filename": file.filename,
                "size_bytes": len(file_content),
                "storage_path": storage_path,
                "message": "Document uploaded successfully"
            }
            
        except Exception as e:
            # Cleanup on failure
            try:
                self.minio_client.remove_object(self.bucket_name, storage_path)
            except:
                pass
            
            if db:
                db.rollback()
            
            logger.error(f"Document upload failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Document upload failed: {str(e)}"
            )
```

### 4. AI Response System Enhancement

#### Real AI Integration with Fallback
```python
class EnhancedAIService:
    def __init__(self):
        self.openai_client = self._init_openai_client()
        self.use_real_ai = bool(os.getenv('OPENAI_API_KEY'))
        
        if not self.use_real_ai:
            logger.warning("OpenAI API key not configured, using enhanced mock responses")
    
    async def generate_response(self, message: str, session_id: str = None,
                              project_context: Dict = None) -> Dict:
        """Generate AI response with real AI or enhanced fallback"""
        
        if self.use_real_ai:
            try:
                return await self._generate_real_ai_response(
                    message, session_id, project_context
                )
            except Exception as e:
                logger.error(f"Real AI response failed: {e}")
                # Fall back to enhanced mock
                return await self._generate_enhanced_mock_response(
                    message, session_id, project_context
                )
        else:
            return await self._generate_enhanced_mock_response(
                message, session_id, project_context
            )
    
    async def _generate_real_ai_response(self, message: str, session_id: str,
                                       project_context: Dict) -> Dict:
        """Generate response using real AI service"""
        
        # Build context from project data and chat history
        context = await self._build_ai_context(session_id, project_context)
        
        system_prompt = """
        You are an AI assistant for StudioOps, a project management system for creative studios.
        You help with project planning, cost estimation, and workflow optimization.
        
        Respond in Hebrew when appropriate, and provide practical, actionable advice.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nUser message: {message}"}
        ]
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        
        ai_message = response.choices[0].message.content
        
        # Save conversation to database
        await self._save_conversation(session_id, message, ai_message, project_context)
        
        return {
            "message": ai_message,
            "session_id": session_id,
            "suggest_plan": self._should_suggest_plan(ai_message),
            "ai_enabled": True
        }
    
    async def _generate_enhanced_mock_response(self, message: str, session_id: str,
                                             project_context: Dict) -> Dict:
        """Generate contextually relevant mock responses"""
        
        message_lower = message.lower()
        
        # Context-aware responses based on project data
        if project_context:
            project_name = project_context.get('project_name', 'הפרויקט')
            
            if any(word in message_lower for word in ['plan', 'תוכנית', 'planning']):
                response = f"""
                אני יכול לעזור לך ליצור תוכנית עבודה מפורטת עבור {project_name}.
                
                על בסיס הפרויקט שלך, אני ממליץ על:
                • תכנון שלבי עבודה לפי סדר עדיפויות
                • הערכת זמנים ועלויות מדויקת
                • זיהוי חומרים ונותני שירותים נדרשים
                • יצירת לוח זמנים מפורט
                
                האם תרצה שאיצור תוכנית עבודה אוטומטית?
                """
                return {
                    "message": response,
                    "session_id": session_id,
                    "suggest_plan": True,
                    "ai_enabled": False,
                    "mock_mode": True
                }
        
        # Default enhanced responses
        responses = {
            'hello': "שלום! אני כאן לעזור לך עם ניהול הפרויקט. איך אוכל לסייע?",
            'cost': "אני יכול לעזור בהערכת עלויות מדויקת. תאר לי את הפרויקט ואתן הערכה מפורטת.",
            'materials': "אשמח לעזור בבחירת חומרים מתאימים. איזה סוג פרויקט אתה מתכנן?",
            'timeline': "בוא ניצור לוח זמנים מפורט. מה היקף הפרויקט ומתי אתה צריך לסיים?"
        }
        
        for key, response in responses.items():
            if key in message_lower:
                return {
                    "message": response,
                    "session_id": session_id,
                    "suggest_plan": False,
                    "ai_enabled": False,
                    "mock_mode": True
                }
        
        # Default response
        return {
            "message": "אני כאן לעזור עם ניהול הפרויקט שלך. תאר לי מה אתה צריך ואתן המלצות מפורטות.",
            "session_id": session_id,
            "suggest_plan": False,
            "ai_enabled": False,
            "mock_mode": True
        }
```

## Data Models

### Updated Database Schema
```sql
-- Migration to fix foreign key constraints
CREATE OR REPLACE FUNCTION fix_foreign_key_constraints()
RETURNS void AS $$
BEGIN
    -- Fix chat_sessions foreign key
    ALTER TABLE chat_sessions 
    DROP CONSTRAINT IF EXISTS chat_sessions_project_id_fkey;
    
    ALTER TABLE chat_sessions 
    ADD CONSTRAINT chat_sessions_project_id_fkey 
    FOREIGN KEY (project_id) REFERENCES projects(id) 
    ON DELETE SET NULL;
    
    -- Fix documents foreign key
    ALTER TABLE documents 
    DROP CONSTRAINT IF EXISTS documents_project_id_fkey;
    
    ALTER TABLE documents 
    ADD CONSTRAINT documents_project_id_fkey 
    FOREIGN KEY (project_id) REFERENCES projects(id) 
    ON DELETE SET NULL;
    
    -- Fix purchases foreign key
    ALTER TABLE purchases 
    DROP CONSTRAINT IF EXISTS purchases_project_id_fkey;
    
    ALTER TABLE purchases 
    ADD CONSTRAINT purchases_project_id_fkey 
    FOREIGN KEY (project_id) REFERENCES projects(id) 
    ON DELETE SET NULL;
    
    -- Plans already have CASCADE, which is correct
    
END;
$$ LANGUAGE plpgsql;

SELECT fix_foreign_key_constraints();
```

## Error Handling

### Comprehensive Error Handling Strategy

1. **Database Operations**
   - Transaction rollback on failures
   - Detailed error logging
   - User-friendly error messages

2. **External Service Integration**
   - Graceful degradation when services unavailable
   - Retry logic with exponential backoff
   - Mock responses for development/testing

3. **File Operations**
   - Atomic upload operations
   - Cleanup on failure
   - Validation and security checks

4. **API Error Responses**
   - Consistent error format
   - Appropriate HTTP status codes
   - Detailed error information for debugging

## Testing Strategy

### Unit Tests
- Database operation tests with rollback scenarios
- Trello MCP server tests with mock API responses
- Document upload tests with MinIO integration
- AI service tests with both real and mock responses

### Integration Tests
- End-to-end project deletion workflow
- Complete document upload and processing pipeline
- Trello integration with real API (when credentials available)
- AI conversation flow with context retrieval

### Error Scenario Tests
- Foreign key constraint violation handling
- External service unavailability scenarios
- File upload failure recovery
- Database connection loss handling

This design provides a comprehensive solution to all identified critical issues while maintaining system reliability and user experience.