"""Context MCP Server for StudioOps AI Agent - Documentation and Context Retrieval"""

import asyncio
import json
from typing import Dict, List, Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    ListToolsResult,
    CallToolResult,
    CallToolRequest,
)

class ContextMCPServer:
    def __init__(self):
        self.server = Server("studioops-context-mcp")
        self.setup_tools()
        
        # Sample documentation and context data
        self.documentation = {
            "project_management": {
                "title": "Project Management API",
                "content": "API endpoints for managing projects:\n- GET /projects - List all projects\n- POST /projects - Create new project\n- GET /projects/{id} - Get project details\n- PUT /projects/{id} - Update project\n- DELETE /projects/{id} - Delete project"
            },
            "chat_system": {
                "title": "Chat System API", 
                "content": "Real-time chat with AI agent:\n- POST /chat/message - Send message to AI\n- GET /chat/sessions - List chat sessions\n- GET /chat/history/{session_id} - Get chat history\n- DELETE /chat/session/{session_id} - Delete session"
            },
            "rag_system": {
                "title": "RAG Document System",
                "content": "Document ingestion and retrieval:\n- POST /rag/upload - Upload documents\n- GET /rag/documents - List documents\n- POST /rag/query - Query knowledge base"
            },
            "mcp_servers": {
                "title": "MCP Server Integration",
                "content": "Available MCP servers:\n1. PostgreSQL Server - Database queries\n2. Playwright Server - Browser automation\n3. Context Server - Documentation access\n4. Filesystem Server - File access"
            }
        }
    
    def setup_tools(self):
        """Setup available tools for the MCP server"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available context and documentation tools"""
            tools = [
                Tool(
                    name="get_documentation",
                    description="Get documentation for specific topics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Documentation topic to retrieve"},
                            "search": {"type": "string", "description": "Search term within documentation"}
                        }
                    }
                ),
                Tool(
                    name="list_topics",
                    description="List all available documentation topics",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="search_documentation",
                    description="Search across all documentation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "description": "Maximum results to return", "default": 5}
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
                if request.name == "get_documentation":
                    result = await self.get_documentation(request.arguments)
                elif request.name == "list_topics":
                    result = await self.list_topics(request.arguments)
                elif request.name == "search_documentation":
                    result = await self.search_documentation(request.arguments)
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
    
    async def get_documentation(self, args: Dict[str, Any]) -> Dict:
        """Get documentation for a specific topic"""
        topic = args.get('topic', '').lower()
        search_term = args.get('search', '')
        
        if topic in self.documentation:
            doc = self.documentation[topic]
            if search_term:
                # Simple search within the content
                if search_term.lower() in doc['content'].lower():
                    return {
                        "topic": topic,
                        "title": doc['title'],
                        "content": doc['content'],
                        "found": True
                    }
                else:
                    return {
                        "topic": topic,
                        "found": False,
                        "message": f"Search term '{search_term}' not found in {topic} documentation"
                    }
            else:
                return {
                    "topic": topic,
                    "title": doc['title'],
                    "content": doc['content'],
                    "found": True
                }
        else:
            return {
                "topic": topic,
                "found": False,
                "available_topics": list(self.documentation.keys()),
                "message": f"Topic '{topic}' not found. Available topics: {list(self.documentation.keys())}"
            }
    
    async def list_topics(self, args: Dict[str, Any]) -> Dict:
        """List all available documentation topics"""
        return {
            "topics": [
                {
                    "id": topic_id,
                    "title": doc['title'],
                    "description": doc['content'][:100] + "..." if len(doc['content']) > 100 else doc['content']
                }
                for topic_id, doc in self.documentation.items()
            ],
            "total": len(self.documentation)
        }
    
    async def search_documentation(self, args: Dict[str, Any]) -> Dict:
        """Search across all documentation"""
        query = args.get('query', '').lower()
        limit = args.get('limit', 5)
        
        if not query:
            return {"results": [], "total": 0, "message": "No search query provided"}
        
        results = []
        for topic_id, doc in self.documentation.items():
            content_lower = doc['content'].lower()
            title_lower = doc['title'].lower()
            
            if query in content_lower or query in title_lower:
                # Simple relevance scoring
                score = 0
                if query in title_lower:
                    score += 3
                if query in content_lower:
                    score += 1
                
                results.append({
                    "topic": topic_id,
                    "title": doc['title'],
                    "content_snippet": self._extract_snippet(doc['content'], query),
                    "score": score
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            "results": results[:limit],
            "total": len(results),
            "query": query
        }
    
    def _extract_snippet(self, content: str, query: str, context_chars: int = 50) -> str:
        """Extract a snippet around the search query"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        pos = content_lower.find(query_lower)
        if pos == -1:
            return content[:100] + "..." if len(content) > 100 else content
        
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet

async def main():
    """Main function to run the MCP server"""
    server = ContextMCPServer()
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            server.server.create_initialization_options(),
        )

if __name__ == "__main__":
    asyncio.run(main())