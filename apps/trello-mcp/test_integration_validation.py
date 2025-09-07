"""Integration validation test for Trello MCP Server"""

import asyncio
import os
import sys
from unittest.mock import patch, Mock
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from server import TrelloMCPServer

# Load environment variables
load_dotenv()

class MockResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.exceptions.HTTPError(f"{self.status_code} Client Error")

async def test_integration_with_mock_api():
    """Test complete integration flow with mocked API responses"""
    print("Testing complete integration flow with mocked API...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Use comprehensive mocking by patching the _make_request method
        def mock_make_request(method, endpoint, params=None, data=None):
            if endpoint == "/members/me/boards":
                return [
                    {
                        "id": "board1",
                        "name": "Existing Board 1",
                        "url": "https://trello.com/b/board1",
                        "desc": "Test board",
                        "closed": False
                    }
                ]
            elif endpoint == "/boards":
                return {
                    "id": "newboard123",
                    "name": params.get("name", "Test Board"),
                    "url": "https://trello.com/b/newboard123",
                    "desc": params.get("desc", ""),
                    "prefs": {"permissionLevel": "private"}
                }
            elif endpoint.endswith("/lists"):
                if method == "GET":
                    return []  # Empty lists initially
                else:  # POST - creating list
                    return {
                        "id": f"list_{params.get('name', 'default').replace(' ', '_').lower()}",
                        "name": params.get("name", "Default List")
                    }
            elif endpoint == "/cards":
                return {
                    "id": f"card_{params.get('name', 'default').replace(' ', '_').lower()}",
                    "name": params.get("name", "Default Card"),
                    "url": f"https://trello.com/c/card_{params.get('name', 'default').replace(' ', '_').lower()}",
                    "desc": params.get("desc", ""),
                    "idList": params.get("idList", "list123")
                }
            else:
                return {}
        
        with patch.object(server, '_make_request', side_effect=mock_make_request):
            # Step 1: Get existing boards
            boards_result = await server.get_boards({"filter": "open"})
            assert boards_result["success"] is True
            assert len(boards_result["boards"]) == 1
            print("✓ Successfully retrieved user boards")
            
            # Step 2: Create new board
            board_result = await server.create_board({
                "name": "Test Project Board",
                "description": "Created by integration test"
            })
            assert board_result["success"] is True
            board_id = board_result["board"]["id"]
            print(f"✓ Successfully created board: {board_id}")
            
            # Step 3: Export project with tasks
            project_data = {
                "plan": [
                    {"name": "Setup environment", "description": "Configure dev environment"},
                    {"name": "Write code", "description": "Implement features"}
                ]
            }
            
            export_result = await server.export_project_tasks({
                "project_id": "test_project",
                "board_name": "Test Project Board",
                "project_data": project_data
            })
            
            assert export_result["success"] is True
            assert export_result["cards_created"] == 2
            print("✓ Successfully exported project tasks")
            
            return True

async def test_error_handling():
    """Test error handling for various failure scenarios"""
    print("Testing error handling scenarios...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Test 401 Unauthorized
        mock_401_response = MockResponse({}, 401)
        
        with patch('requests.get', return_value=mock_401_response):
            try:
                await server.get_boards({})
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Trello API request failed" in str(e)
                print("✓ Handles 401 Unauthorized correctly")
        
        # Test network error
        import requests
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError("Network error")):
            try:
                await server.get_boards({})
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Trello API request failed" in str(e)
                print("✓ Handles network errors correctly")
        
        # Test invalid JSON response
        mock_invalid_response = Mock()
        mock_invalid_response.raise_for_status.return_value = None
        mock_invalid_response.json.side_effect = ValueError("Invalid JSON")
        
        with patch('requests.get', return_value=mock_invalid_response):
            try:
                await server.get_boards({})
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Trello API request failed" in str(e)
                print("✓ Handles invalid JSON responses correctly")

async def test_credentials_validation():
    """Test credentials validation"""
    print("Testing credentials validation...")
    
    # Test missing credentials
    with patch.dict(os.environ, {}, clear=True):
        server = TrelloMCPServer()
        
        try:
            await server.get_boards({})
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Trello API credentials not configured" in str(e)
            print("✓ Detects missing credentials correctly")
    
    # Test partial credentials
    with patch.dict(os.environ, {'TRELLO_API_KEY': 'test_key'}, clear=True):
        server = TrelloMCPServer()
        
        try:
            await server.get_boards({})
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Trello API credentials not configured" in str(e)
            print("✓ Detects partial credentials correctly")

async def test_real_credentials_detection():
    """Test detection of real credentials"""
    print("Testing real credentials detection...")
    
    api_key = os.getenv('TRELLO_API_KEY')
    token = os.getenv('TRELLO_TOKEN')
    
    if api_key and token:
        print(f"✓ Real API key detected: {api_key[:8]}...")
        print(f"✓ Real token detected: {token[:8]}...")
        print("✓ Credentials are configured for manual testing")
        
        # Test that server initializes with real credentials
        server = TrelloMCPServer()
        assert server.api_key == api_key
        assert server.token == token
        print("✓ Server correctly loads real credentials")
        
        return True
    else:
        print("ℹ️  No real credentials configured (this is fine for automated testing)")
        print("ℹ️  To test with real Trello API, set TRELLO_API_KEY and TRELLO_TOKEN")
        return False

async def test_mcp_tool_integration():
    """Test MCP tool call integration"""
    print("Testing MCP tool call integration...")
    
    with patch.dict(os.environ, {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_TOKEN': 'test_token'
    }):
        server = TrelloMCPServer()
        
        # Test that the server has the expected MCP structure
        assert hasattr(server.server, 'request_handlers')
        print("✓ MCP server structure is correct")
        
        # Test direct method calls (simulating what MCP would do)
        def mock_make_request(method, endpoint, params=None, data=None):
            if endpoint == "/members/me/boards":
                return [
                    {"id": "board1", "name": "Test Board", "url": "https://trello.com/b/board1", "desc": "", "closed": False}
                ]
            elif endpoint == "/boards":
                return {
                    "id": "newboard123",
                    "name": params.get("name", "New Board"),
                    "url": "https://trello.com/b/newboard123",
                    "desc": params.get("desc", ""),
                    "prefs": {"permissionLevel": "private"}
                }
            return {}
        
        with patch.object(server, '_make_request', side_effect=mock_make_request):
            # Test get_boards method directly
            result = await server.get_boards({"filter": "open"})
            assert result["success"] is True
            assert len(result["boards"]) == 1
            assert result["boards"][0]["name"] == "Test Board"
            print("✓ MCP tool methods work correctly")
            
            # Test create_board method
            result = await server.create_board({"name": "New Board"})
            assert result["success"] is True
            print("✓ MCP tool creation methods work correctly")

async def run_integration_validation():
    """Run complete integration validation"""
    print("Running Trello MCP Server Integration Validation")
    print("=" * 55)
    
    try:
        # Test 1: Integration flow with mocked API
        await test_integration_with_mock_api()
        print()
        
        # Test 2: Error handling
        await test_error_handling()
        print()
        
        # Test 3: Credentials validation
        await test_credentials_validation()
        print()
        
        # Test 4: Real credentials detection
        has_real_creds = await test_real_credentials_detection()
        print()
        
        # Test 5: MCP tool integration
        await test_mcp_tool_integration()
        
        print("\n" + "=" * 55)
        print("✅ Integration validation completed successfully!")
        print("✅ All Trello MCP Server components working correctly")
        print("✅ Error handling implemented properly")
        print("✅ MCP tool integration functional")
        
        if has_real_creds:
            print("✅ Real credentials detected - ready for live testing")
            print("💡 Run 'python test_end_to_end.py --validation-only' to test with real API")
        else:
            print("ℹ️  No real credentials - automated testing only")
            print("💡 Configure TRELLO_API_KEY and TRELLO_TOKEN for live testing")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_integration_validation())
    sys.exit(0 if success else 1)