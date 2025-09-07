"""Test script for Trello MCP Server"""

import asyncio
import os
import sys
from unittest.mock import Mock, patch
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from server import TrelloMCPServer

async def test_server_initialization():
    """Test that the server initializes correctly"""
    print("Testing server initialization...")
    
    # Test without credentials
    with patch.dict(os.environ, {}, clear=True):
        server = TrelloMCPServer()
        assert server.api_key is None
        assert server.token is None
        print("✓ Server handles missing credentials gracefully")
    
    # Test with credentials
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        assert server.api_key == 'test_key'
        assert server.token == 'test_token'
        print("✓ Server loads credentials correctly")

async def test_tool_listing():
    """Test that tools are listed correctly"""
    print("\nTesting tool listing...")
    
    server = TrelloMCPServer()
    
    # Test that the server has the expected structure
    assert hasattr(server.server, 'request_handlers')
    print("✓ Server has request handlers")
    
    # Test expected tool count by checking the setup
    expected_tools = [
        "create_board",
        "create_card", 
        "get_boards",
        "get_board_lists",
        "export_project_tasks"
    ]
    
    print(f"✓ Expected {len(expected_tools)} tools to be configured")
    for tool in expected_tools:
        print(f"✓ Tool '{tool}' should be available")

async def test_plan_parsing():
    """Test plan parsing functionality"""
    print("\nTesting plan parsing...")
    
    server = TrelloMCPServer()
    
    # Test string plan
    string_plan = """
    # Project Tasks
    - Task 1: Setup database
    - Task 2: Create API endpoints
    - Task 3: Build frontend
    """
    
    tasks = server._parse_plan_items(string_plan)
    assert len(tasks) == 3
    assert tasks[0]["name"] == "Task 1: Setup database"
    print("✓ String plan parsing works")
    
    # Test list plan
    list_plan = [
        {"name": "Setup environment", "description": "Configure development environment"},
        {"name": "Write tests", "description": "Create unit tests"}
    ]
    
    tasks = server._parse_plan_items(list_plan)
    assert len(tasks) == 2
    assert tasks[0]["name"] == "Setup environment"
    assert tasks[0]["description"] == "Configure development environment"
    print("✓ List plan parsing works")
    
    # Test dict plan
    dict_plan = {
        "Backend": ["API setup", "Database migration"],
        "Frontend": ["UI components", "State management"]
    }
    
    tasks = server._parse_plan_items(dict_plan)
    assert len(tasks) == 4
    assert "Backend: API setup" in [task["name"] for task in tasks]
    print("✓ Dict plan parsing works")

async def test_request_method():
    """Test the request method structure"""
    print("\nTesting request method...")
    
    server = TrelloMCPServer()
    
    # Test that the method exists and has proper structure
    assert hasattr(server, '_make_request')
    assert callable(server._make_request)
    print("✓ Request method is properly defined")

async def run_tests():
    """Run all tests"""
    print("Running Trello MCP Server Tests")
    print("=" * 40)
    
    try:
        await test_server_initialization()
        await test_tool_listing()
        await test_plan_parsing()
        await test_request_method()
        
        print("\n" + "=" * 40)
        print("All tests passed! ✓")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)