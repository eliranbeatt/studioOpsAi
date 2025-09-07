"""Test Trello API integration functionality"""

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

async def test_create_board():
    """Test board creation functionality"""
    print("Testing create_board...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock the API response
        mock_response = MockResponse({
            "id": "board123",
            "name": "Test Board",
            "url": "https://trello.com/b/board123",
            "desc": "Test Description",
            "prefs": {"permissionLevel": "private"}
        })
        
        with patch('requests.post', return_value=mock_response):
            result = await server.create_board({
                "name": "Test Board",
                "description": "Test Description"
            })
            
            assert result["success"] is True
            assert result["board"]["id"] == "board123"
            assert result["board"]["name"] == "Test Board"
            print("✓ Board creation works correctly")

async def test_get_boards():
    """Test getting user boards"""
    print("Testing get_boards...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock the API response
        mock_response = MockResponse([
            {
                "id": "board1",
                "name": "Board 1",
                "url": "https://trello.com/b/board1",
                "desc": "Description 1",
                "closed": False
            },
            {
                "id": "board2", 
                "name": "Board 2",
                "url": "https://trello.com/b/board2",
                "desc": "Description 2",
                "closed": False
            }
        ])
        
        with patch('requests.get', return_value=mock_response):
            result = await server.get_boards({"filter": "open"})
            
            assert result["success"] is True
            assert len(result["boards"]) == 2
            assert result["boards"][0]["name"] == "Board 1"
            print("✓ Get boards works correctly")

async def test_get_board_lists():
    """Test getting board lists"""
    print("Testing get_board_lists...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock the API response
        mock_response = MockResponse([
            {
                "id": "list1",
                "name": "To Do",
                "closed": False,
                "pos": 1
            },
            {
                "id": "list2",
                "name": "In Progress", 
                "closed": False,
                "pos": 2
            }
        ])
        
        with patch('requests.get', return_value=mock_response):
            result = await server.get_board_lists({"board_id": "board123"})
            
            assert result["success"] is True
            assert len(result["lists"]) == 2
            assert result["lists"][0]["name"] == "To Do"
            print("✓ Get board lists works correctly")

async def test_create_card():
    """Test card creation functionality"""
    print("Testing create_card...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock getting existing lists
        lists_response = MockResponse([
            {"id": "list1", "name": "To Do", "closed": False}
        ])
        
        # Mock card creation
        card_response = MockResponse({
            "id": "card123",
            "name": "Test Card",
            "url": "https://trello.com/c/card123",
            "desc": "Test Description",
            "idList": "list1"
        })
        
        with patch('requests.get', return_value=lists_response), \
             patch('requests.post', return_value=card_response):
            
            result = await server.create_card({
                "board_id": "board123",
                "list_name": "To Do",
                "name": "Test Card",
                "description": "Test Description"
            })
            
            assert result["success"] is True
            assert result["card"]["id"] == "card123"
            assert result["card"]["name"] == "Test Card"
            print("✓ Card creation works correctly")

async def test_create_card_with_new_list():
    """Test card creation with new list creation"""
    print("Testing create_card with new list...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock getting existing lists (empty)
        lists_response = MockResponse([])
        
        # Mock list creation
        list_response = MockResponse({
            "id": "newlist1",
            "name": "New List"
        })
        
        # Mock card creation
        card_response = MockResponse({
            "id": "card123",
            "name": "Test Card",
            "url": "https://trello.com/c/card123",
            "desc": "Test Description",
            "idList": "newlist1"
        })
        
        with patch('requests.get', return_value=lists_response), \
             patch('requests.post', side_effect=[list_response, card_response]):
            
            result = await server.create_card({
                "board_id": "board123",
                "list_name": "New List",
                "name": "Test Card",
                "description": "Test Description"
            })
            
            assert result["success"] is True
            assert result["card"]["id"] == "card123"
            print("✓ Card creation with new list works correctly")

async def test_error_handling():
    """Test error handling for API failures"""
    print("Testing error handling...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Mock API failure
        with patch('requests.post', side_effect=Exception("API Error")):
            try:
                await server.create_board({"name": "Test Board"})
                assert False, "Should have raised an exception"
            except Exception as e:
                assert "Trello API request failed" in str(e)
                print("✓ Error handling works correctly")

async def test_missing_credentials():
    """Test handling of missing credentials"""
    print("Testing missing credentials...")
    
    with patch.dict(os.environ, {}, clear=True):
        server = TrelloMCPServer()
        
        try:
            await server.create_board({"name": "Test Board"})
            assert False, "Should have raised an exception"
        except ValueError as e:
            assert "Trello API credentials not configured" in str(e)
            print("✓ Missing credentials handling works correctly")

async def run_api_tests():
    """Run all API integration tests"""
    print("Running Trello API Integration Tests")
    print("=" * 45)
    
    try:
        await test_create_board()
        await test_get_boards()
        await test_get_board_lists()
        await test_create_card()
        await test_create_card_with_new_list()
        await test_error_handling()
        await test_missing_credentials()
        
        print("\n" + "=" * 45)
        print("All API integration tests passed! ✓")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_api_tests())
    sys.exit(0 if success else 1)