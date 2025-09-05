#!/usr/bin/env python3
"""Test MCP server connection"""

import asyncio
import json
import os
import sys
from mcp.server.stdio import stdio_server
from mcp import ClientSession

async def test_mcp_server():
    """Test the PostgreSQL MCP server"""
    print("Testing PostgreSQL MCP server connection...")
    
    # Start the server as a subprocess
    server_params = {
        "command": "python",
        "args": ["apps/api/mcp_server.py"],
        "env": {
            "DATABASE_URL": os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        }
    }
    
    try:
        # This would normally be done through stdio transport
        # For testing, we'll just import and test the server directly
        from apps.api.mcp_server import PostgresMCPServer
        
        server = PostgresMCPServer()
        
        # Test a simple query
        result = await server.query_projects({"limit": 1})
        print(f"MCP server test successful! Found {len(result)} projects")
        
        if result:
            print(f"Sample project: {result[0]['name']} ({result[0]['status']})")
        
        return True
        
    except Exception as e:
        print(f"MCP server test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1)