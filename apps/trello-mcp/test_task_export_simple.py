"""Simple test for task export functionality"""

import asyncio
import os
import sys
from unittest.mock import Mock, patch
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from server import TrelloMCPServer

async def test_plan_parsing():
    """Test plan parsing functionality without API calls"""
    print("Testing plan parsing functionality...")
    
    server = TrelloMCPServer()
    
    # Test string plan
    string_plan = """
    # Project Tasks
    - Setup database
    - Create API endpoints
    - Build frontend components
    """
    
    tasks = server._parse_plan_items(string_plan)
    assert len(tasks) == 3
    assert tasks[0]["name"] == "Setup database"
    assert tasks[1]["name"] == "Create API endpoints"
    assert tasks[2]["name"] == "Build frontend components"
    print("✓ String plan parsing works correctly")
    
    # Test list plan
    list_plan = [
        {"name": "Setup environment", "description": "Configure development environment"},
        {"name": "Write tests", "description": "Create unit tests"},
        "Simple task"
    ]
    
    tasks = server._parse_plan_items(list_plan)
    assert len(tasks) == 3
    assert tasks[0]["name"] == "Setup environment"
    assert tasks[0]["description"] == "Configure development environment"
    assert tasks[1]["name"] == "Write tests"
    assert tasks[2]["name"] == "Simple task"
    print("✓ List plan parsing works correctly")
    
    # Test dict plan
    dict_plan = {
        "Backend": ["API setup", "Database migration"],
        "Frontend": ["UI components", "State management"]
    }
    
    tasks = server._parse_plan_items(dict_plan)
    assert len(tasks) == 4
    task_names = [task["name"] for task in tasks]
    assert "Backend: API setup" in task_names
    assert "Backend: Database migration" in task_names
    assert "Frontend: UI components" in task_names
    assert "Frontend: State management" in task_names
    print("✓ Dict plan parsing works correctly")

async def test_export_project_tasks_structure():
    """Test the export_project_tasks method structure without API calls"""
    print("Testing export_project_tasks method structure...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock all the API calls to return success
        with patch.object(server, 'create_board') as mock_create_board, \
             patch.object(server, '_get_or_create_list') as mock_get_list, \
             patch.object(server, 'create_card') as mock_create_card:
            
            # Setup mocks
            mock_create_board.return_value = {
                "board": {
                    "id": "board123",
                    "name": "Test Project",
                    "url": "https://trello.com/b/board123"
                }
            }
            
            mock_get_list.return_value = "list123"
            
            mock_create_card.return_value = {
                "card": {
                    "id": "card123",
                    "name": "Test Task",
                    "url": "https://trello.com/c/card123"
                }
            }
            
            # Test with project data
            project_data = {
                "plan": [
                    {"name": "Task 1", "description": "First task"},
                    {"name": "Task 2", "description": "Second task"}
                ]
            }
            
            result = await server.export_project_tasks({
                "project_id": "test_project",
                "board_name": "Test Project",
                "project_data": project_data
            })
            
            # Verify the method was called correctly
            assert result["success"] is True
            assert result["board"]["id"] == "board123"
            assert result["cards_created"] == 2
            
            # Verify board creation was called
            mock_create_board.assert_called_once()
            
            # Verify list creation was called for default lists
            assert mock_get_list.call_count == 3  # To Do, In Progress, Done
            
            # Verify card creation was called for each task
            assert mock_create_card.call_count == 2
            
            print("✓ Export project tasks structure works correctly")

async def test_default_lists_creation():
    """Test that default lists are created"""
    print("Testing default lists creation...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        with patch.object(server, 'create_board') as mock_create_board, \
             patch.object(server, '_get_or_create_list') as mock_get_list:
            
            mock_create_board.return_value = {
                "board": {
                    "id": "board123",
                    "name": "Test Project",
                    "url": "https://trello.com/b/board123"
                }
            }
            
            mock_get_list.return_value = "list123"
            
            await server.export_project_tasks({
                "project_id": "test_project"
            })
            
            # Verify default lists were created
            expected_calls = [
                (("board123", "To Do"),),
                (("board123", "In Progress"),),
                (("board123", "Done"),)
            ]
            
            actual_calls = mock_get_list.call_args_list
            assert len(actual_calls) == 3
            
            for expected_call in expected_calls:
                assert expected_call in actual_calls
            
            print("✓ Default lists creation works correctly")

async def test_credentials_check():
    """Test that credentials are checked before API calls"""
    print("Testing credentials check...")
    
    with patch.dict(os.environ, {}, clear=True):
        server = TrelloMCPServer()
        
        try:
            await server.export_project_tasks({
                "project_id": "test_project"
            })
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Trello API credentials not configured" in str(e)
            print("✓ Credentials check works correctly")

async def run_simple_tests():
    """Run all simple tests"""
    print("Running Simple Trello Task Export Tests")
    print("=" * 45)
    
    try:
        await test_plan_parsing()
        await test_export_project_tasks_structure()
        await test_default_lists_creation()
        await test_credentials_check()
        
        print("\n" + "=" * 45)
        print("All simple task export tests passed! ✓")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_simple_tests())
    sys.exit(0 if success else 1)