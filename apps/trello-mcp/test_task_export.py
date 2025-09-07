"""Test task export functionality"""

import asyncio
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from server import TrelloMCPServer

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

async def test_export_project_tasks_basic():
    """Test basic project task export"""
    print("Testing basic project task export...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock board creation
        board_response = MockResponse({
            "id": "board123",
            "name": "Project Test Project",
            "url": "https://trello.com/b/board123",
            "desc": "Tasks for project test_project"
        })
        
        # Mock list creation (default lists)
        list_response = MockResponse({
            "id": "list1",
            "name": "To Do"
        })
        
        # Mock getting existing lists (empty initially)
        empty_lists_response = MockResponse([])
        
        with patch('requests.post', side_effect=[board_response, list_response, list_response, list_response]), \
             patch('requests.get', return_value=empty_lists_response):
            
            result = await server.export_project_tasks({
                "project_id": "test_project",
                "board_name": "Project Test Project"
            })
            
            assert result["success"] is True
            assert result["board"]["id"] == "board123"
            assert result["cards_created"] == 0  # No project data provided
            print("✓ Basic project export works correctly")

async def test_export_project_tasks_with_string_plan():
    """Test project task export with string plan"""
    print("Testing project task export with string plan...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock board creation
        board_response = MockResponse({
            "id": "board123",
            "name": "Project Test Project",
            "url": "https://trello.com/b/board123",
            "desc": "Tasks for project test_project"
        })
        
        # Mock list responses
        list_response = MockResponse({
            "id": "list1",
            "name": "To Do"
        })
        
        # Mock getting existing lists (return To Do list)
        lists_response = MockResponse([
            {"id": "list1", "name": "To Do", "closed": False}
        ])
        
        # Mock card creation responses
        def create_card_response(card_id, name):
            return MockResponse({
                "id": card_id,
                "name": name,
                "url": f"https://trello.com/c/{card_id}",
                "desc": "",
                "idList": "list1"
            })
        
        card_responses = [
            create_card_response("card1", "Setup database"),
            create_card_response("card2", "Create API endpoints"), 
            create_card_response("card3", "Build frontend components")
        ]
        
        project_data = {
            "plan": """
            # Project Tasks
            - Setup database
            - Create API endpoints
            - Build frontend components
            """
        }
        
        with patch('requests.post', side_effect=[board_response, list_response, list_response, list_response] + card_responses), \
             patch('requests.get', return_value=lists_response):
            
            result = await server.export_project_tasks({
                "project_id": "test_project",
                "board_name": "Project Test Project",
                "project_data": project_data
            })
            
            assert result["success"] is True
            assert result["board"]["id"] == "board123"
            assert result["cards_created"] == 3
            assert len(result["cards"]) == 3
            print("✓ Project export with string plan works correctly")

async def test_export_project_tasks_with_list_plan():
    """Test project task export with list plan"""
    print("Testing project task export with list plan...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock board creation
        board_response = MockResponse({
            "id": "board123",
            "name": "Project Test Project",
            "url": "https://trello.com/b/board123",
            "desc": "Tasks for project test_project"
        })
        
        # Mock list responses
        list_response = MockResponse({
            "id": "list1",
            "name": "To Do"
        })
        
        # Mock getting existing lists
        lists_response = MockResponse([
            {"id": "list1", "name": "To Do", "closed": False}
        ])
        
        # Mock card creation responses
        def create_card_response(card_id, name, desc=""):
            return MockResponse({
                "id": card_id,
                "name": name,
                "url": f"https://trello.com/c/{card_id}",
                "desc": desc,
                "idList": "list1"
            })
        
        card_responses = [
            create_card_response("card1", "Setup environment", "Configure development environment"),
            create_card_response("card2", "Write tests", "Create unit tests")
        ]
        
        project_data = {
            "plan": [
                {
                    "name": "Setup environment",
                    "description": "Configure development environment",
                    "labels": ["setup", "task"]
                },
                {
                    "name": "Write tests",
                    "description": "Create unit tests",
                    "labels": ["testing", "task"]
                }
            ]
        }
        
        with patch('requests.post', side_effect=[board_response, list_response, list_response, list_response] + card_responses), \
             patch('requests.get', return_value=lists_response):
            
            result = await server.export_project_tasks({
                "project_id": "test_project",
                "board_name": "Project Test Project",
                "project_data": project_data
            })
            
            assert result["success"] is True
            assert result["board"]["id"] == "board123"
            assert result["cards_created"] == 2
            assert len(result["cards"]) == 2
            print("✓ Project export with list plan works correctly")

async def test_export_project_tasks_with_dict_plan():
    """Test project task export with dictionary plan"""
    print("Testing project task export with dictionary plan...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock board creation
        board_response = MockResponse({
            "id": "board123",
            "name": "Project Test Project",
            "url": "https://trello.com/b/board123",
            "desc": "Tasks for project test_project"
        })
        
        # Mock list responses
        list_response = MockResponse({
            "id": "list1",
            "name": "To Do"
        })
        
        # Mock getting existing lists
        lists_response = MockResponse([
            {"id": "list1", "name": "To Do", "closed": False}
        ])
        
        # Mock card creation responses
        def create_card_response(card_id, name):
            return MockResponse({
                "id": card_id,
                "name": name,
                "url": f"https://trello.com/c/{card_id}",
                "desc": "",
                "idList": "list1"
            })
        
        card_responses = [
            create_card_response("card1", "Backend: API setup"),
            create_card_response("card2", "Backend: Database migration"),
            create_card_response("card3", "Frontend: UI components"),
            create_card_response("card4", "Frontend: State management")
        ]
        
        project_data = {
            "plan": {
                "Backend": ["API setup", "Database migration"],
                "Frontend": ["UI components", "State management"]
            }
        }
        
        with patch('requests.post', side_effect=[board_response, list_response, list_response, list_response] + card_responses), \
             patch('requests.get', return_value=lists_response):
            
            result = await server.export_project_tasks({
                "project_id": "test_project",
                "board_name": "Project Test Project",
                "project_data": project_data
            })
            
            assert result["success"] is True
            assert result["board"]["id"] == "board123"
            assert result["cards_created"] == 4
            assert len(result["cards"]) == 4
            print("✓ Project export with dictionary plan works correctly")

async def test_plan_parsing_edge_cases():
    """Test plan parsing with edge cases"""
    print("Testing plan parsing edge cases...")
    
    server = TrelloMCPServer()
    
    # Test empty plan
    tasks = server._parse_plan_items("")
    assert len(tasks) == 0
    print("✓ Empty plan parsing works")
    
    # Test plan with comments and formatting
    formatted_plan = """
    # Main Tasks
    - Task 1: Important task
    * Task 2: Another format
    
    ## Subtasks
    - Subtask A
    """
    
    tasks = server._parse_plan_items(formatted_plan)
    assert len(tasks) == 3
    assert "Task 1: Important task" in [task["name"] for task in tasks]
    assert "Task 2: Another format" in [task["name"] for task in tasks]
    assert "Subtask A" in [task["name"] for task in tasks]
    print("✓ Formatted plan parsing works")
    
    # Test mixed data types
    mixed_plan = [
        "Simple string task",
        {"name": "Complex task", "description": "With description"},
        {"title": "Task with title field"}  # Different field name
    ]
    
    tasks = server._parse_plan_items(mixed_plan)
    assert len(tasks) == 3
    assert tasks[0]["name"] == "Simple string task"
    assert tasks[1]["name"] == "Complex task"
    assert tasks[2]["name"] == "Task with title field"
    print("✓ Mixed plan parsing works")

async def test_default_board_name():
    """Test default board name generation"""
    print("Testing default board name generation...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock board creation with default name
        board_response = MockResponse({
            "id": "board123",
            "name": "Project test_project_123",
            "url": "https://trello.com/b/board123",
            "desc": "Tasks for project test_project_123"
        })
        
        # Mock list creation
        list_response = MockResponse({
            "id": "list1",
            "name": "To Do"
        })
        
        # Mock getting existing lists (empty)
        empty_lists_response = MockResponse([])
        
        with patch('requests.post', side_effect=[board_response, list_response, list_response, list_response]), \
             patch('requests.get', return_value=empty_lists_response):
            
            result = await server.export_project_tasks({
                "project_id": "test_project_123"
                # No board_name provided - should use default
            })
            
            assert result["success"] is True
            assert result["board"]["name"] == "Project test_project_123"
            print("✓ Default board name generation works correctly")

async def run_task_export_tests():
    """Run all task export tests"""
    print("Running Trello Task Export Tests")
    print("=" * 40)
    
    try:
        await test_export_project_tasks_basic()
        await test_export_project_tasks_with_string_plan()
        await test_export_project_tasks_with_list_plan()
        await test_export_project_tasks_with_dict_plan()
        await test_plan_parsing_edge_cases()
        await test_default_board_name()
        
        print("\n" + "=" * 40)
        print("All task export tests passed! ✓")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_task_export_tests())
    sys.exit(0 if success else 1)