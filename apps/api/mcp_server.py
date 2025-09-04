"""PostgreSQL MCP Server for StudioOps AI Agent"""

import asyncio
import json
import os
import psycopg2
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    ImageContent,
    Tool,
    ListToolsResult,
    CallToolResult,
    CallToolRequest,
)

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')

class PostgresMCPServer:
    def __init__(self):
        self.server = Server("studioops-postgres-mcp")
        self.setup_tools()
    
    def setup_tools(self):
        """Setup available tools for the MCP server"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available database query tools"""
            tools = [
                Tool(
                    name="query_projects",
                    description="Query projects from the database with optional filters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string", "description": "Specific project ID to query"},
                            "status": {"type": "string", "description": "Filter by project status"},
                            "client_name": {"type": "string", "description": "Filter by client name"},
                            "limit": {"type": "integer", "description": "Maximum number of results"}
                        }
                    }
                ),
                Tool(
                    name="query_chat_messages",
                    description="Query chat messages for a specific session or project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session ID to filter messages"},
                            "project_id": {"type": "string", "description": "Project ID to filter messages"},
                            "limit": {"type": "integer", "description": "Maximum number of results"},
                            "is_user": {"type": "boolean", "description": "Filter by user messages only"}
                        }
                    }
                ),
                Tool(
                    name="query_rag_documents",
                    description="Query RAG documents from the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_type": {"type": "string", "description": "Filter by document type"},
                            "source": {"type": "string", "description": "Filter by document source"},
                            "search_term": {"type": "string", "description": "Search term in title or content"},
                            "limit": {"type": "integer", "description": "Maximum number of results"}
                        }
                    }
                ),
                Tool(
                    name="query_project_knowledge",
                    description="Query project-specific knowledge base entries",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string", "description": "Project ID to filter knowledge"},
                            "category": {"type": "string", "description": "Filter by knowledge category"},
                            "key": {"type": "string", "description": "Filter by specific key"},
                            "search_term": {"type": "string", "description": "Search term in key or value"},
                            "limit": {"type": "integer", "description": "Maximum number of results"}
                        }
                    }
                ),
                Tool(
                    name="execute_custom_query",
                    description="Execute a custom SQL query against the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "SQL query to execute"},
                            "parameters": {"type": "object", "description": "Query parameters"}
                        },
                        "required": ["query"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool execution requests"""
            try:
                if request.name == "query_projects":
                    result = await self.query_projects(request.arguments)
                elif request.name == "query_chat_messages":
                    result = await self.query_chat_messages(request.arguments)
                elif request.name == "query_rag_documents":
                    result = await self.query_rag_documents(request.arguments)
                elif request.name == "query_project_knowledge":
                    result = await self.query_project_knowledge(request.arguments)
                elif request.name == "execute_custom_query":
                    result = await self.execute_custom_query(request.arguments)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))],
                    isError=False
                )
            
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
    
    async def get_db_connection(self):
        """Get a database connection"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")
    
    async def query_projects(self, args: Dict[str, Any]) -> List[Dict]:
        """Query projects from database"""
        conn = await self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id, name, client_name, status, start_date, due_date, budget_planned, 
                       created_at, updated_at
                FROM projects
                WHERE 1=1
            """
            
            params = []
            
            if args.get('project_id'):
                query += " AND id = %s"
                params.append(args['project_id'])
            
            if args.get('status'):
                query += " AND status = %s"
                params.append(args['status'])
            
            if args.get('client_name'):
                query += " AND client_name ILIKE %s"
                params.append(f"%{args['client_name']}%")
            
            query += " ORDER BY created_at DESC"
            
            if args.get('limit'):
                query += " LIMIT %s"
                params.append(args['limit'])
            
            cursor.execute(query, params)
            
            projects = []
            for row in cursor.fetchall():
                projects.append({
                    "id": row[0],
                    "name": row[1],
                    "client_name": row[2],
                    "status": row[3],
                    "start_date": row[4].isoformat() if row[4] else None,
                    "due_date": row[5].isoformat() if row[5] else None,
                    "budget_planned": float(row[6]) if row[6] else None,
                    "created_at": row[7].isoformat(),
                    "updated_at": row[8].isoformat()
                })
            
            return projects
            
        finally:
            cursor.close()
            conn.close()
    
    async def query_chat_messages(self, args: Dict[str, Any]) -> List[Dict]:
        """Query chat messages from database"""
        conn = await self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id, session_id, message, response, is_user, project_context, 
                       created_at
                FROM chat_messages
                WHERE 1=1
            """
            
            params = []
            
            if args.get('session_id'):
                query += " AND session_id = %s"
                params.append(args['session_id'])
            
            if args.get('project_id'):
                query += " AND project_context->>'project_id' = %s"
                params.append(args['project_id'])
            
            if 'is_user' in args:
                query += " AND is_user = %s"
                params.append(args['is_user'])
            
            query += " ORDER BY created_at ASC"
            
            if args.get('limit'):
                query += " LIMIT %s"
                params.append(args['limit'])
            
            cursor.execute(query, params)
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    "id": row[0],
                    "session_id": row[1],
                    "message": row[2],
                    "response": row[3],
                    "is_user": row[4],
                    "project_context": row[5],
                    "created_at": row[6].isoformat()
                })
            
            return messages
            
        finally:
            cursor.close()
            conn.close()
    
    async def query_rag_documents(self, args: Dict[str, Any]) -> List[Dict]:
        """Query RAG documents from database"""
        conn = await self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id, title, content, source, document_type, meta_data, 
                       created_at, updated_at
                FROM rag_documents
                WHERE is_active = true
            """
            
            params = []
            
            if args.get('document_type'):
                query += " AND document_type = %s"
                params.append(args['document_type'])
            
            if args.get('source'):
                query += " AND source = %s"
                params.append(args['source'])
            
            if args.get('search_term'):
                query += " AND (title ILIKE %s OR content ILIKE %s)"
                search_term = f"%{args['search_term']}%"
                params.extend([search_term, search_term])
            
            query += " ORDER BY created_at DESC"
            
            if args.get('limit'):
                query += " LIMIT %s"
                params.append(args['limit'])
            
            cursor.execute(query, params)
            
            documents = []
            for row in cursor.fetchall():
                documents.append({
                    "id": row[0],
                    "title": row[1],
                    "content": row[2][:500] + "..." if len(row[2]) > 500 else row[2],  # Truncate long content
                    "source": row[3],
                    "document_type": row[4],
                    "meta_data": row[5],
                    "created_at": row[6].isoformat(),
                    "updated_at": row[7].isoformat()
                })
            
            return documents
            
        finally:
            cursor.close()
            conn.close()
    
    async def query_project_knowledge(self, args: Dict[str, Any]) -> List[Dict]:
        """Query project knowledge base"""
        conn = await self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id, project_id, category, key, value, confidence, source, 
                       meta_data, created_at, updated_at
                FROM project_knowledge
                WHERE 1=1
            """
            
            params = []
            
            if args.get('project_id'):
                query += " AND project_id = %s"
                params.append(args['project_id'])
            
            if args.get('category'):
                query += " AND category = %s"
                params.append(args['category'])
            
            if args.get('key'):
                query += " AND key = %s"
                params.append(args['key'])
            
            if args.get('search_term'):
                query += " AND (key ILIKE %s OR value ILIKE %s)"
                search_term = f"%{args['search_term']}%"
                params.extend([search_term, search_term])
            
            query += " ORDER BY confidence DESC, updated_at DESC"
            
            if args.get('limit'):
                query += " LIMIT %s"
                params.append(args['limit'])
            
            cursor.execute(query, params)
            
            knowledge = []
            for row in cursor.fetchall():
                knowledge.append({
                    "id": row[0],
                    "project_id": row[1],
                    "category": row[2],
                    "key": row[3],
                    "value": row[4],
                    "confidence": float(row[5]),
                    "source": row[6],
                    "meta_data": row[7],
                    "created_at": row[8].isoformat(),
                    "updated_at": row[9].isoformat()
                })
            
            return knowledge
            
        finally:
            cursor.close()
            conn.close()
    
    async def execute_custom_query(self, args: Dict[str, Any]) -> List[Dict]:
        """Execute custom SQL query"""
        conn = await self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            query = args['query']
            parameters = args.get('parameters', {})
            
            # Convert parameters to list for psycopg2
            params_list = list(parameters.values()) if isinstance(parameters, dict) else []
            
            cursor.execute(query, params_list)
            
            # Get column names
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            
            results = []
            for row in cursor.fetchall():
                result = {}
                for i, value in enumerate(row):
                    col_name = col_names[i] if i < len(col_names) else f"column_{i}"
                    # Convert non-serializable types
                    if hasattr(value, 'isoformat'):
                        result[col_name] = value.isoformat()
                    else:
                        result[col_name] = value
                results.append(result)
            
            return results
            
        finally:
            cursor.close()
            conn.close()

async def main():
    """Main function to run the MCP server"""
    server = PostgresMCPServer()
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            server.server.create_initialization_options(),
        )

if __name__ == "__main__":
    asyncio.run(main())