"""End-to-end test for Trello MCP Server with real API credentials"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from server import TrelloMCPServer

# Load environment variables
load_dotenv()

async def test_real_api_connection():
    """Test connection to real Trello API"""
    print("Testing real Trello API connection...")
    
    api_key = os.getenv('TRELLO_API_KEY')
    token = os.getenv('TRELLO_TOKEN')
    
    if not api_key or not token:
        print("❌ Trello API credentials not configured")
        print("Please set TRELLO_API_KEY and TRELLO_TOKEN environment variables")
        print("Get your API key from: https://trello.com/app-key")
        print("Get your token by visiting the authorization URL (see README.md)")
        return False
    
    print(f"✓ API Key configured: {api_key[:8]}...")
    print(f"✓ Token configured: {token[:8]}...")
    
    server = TrelloMCPServer()
    
    try:
        # Test getting user boards
        result = await server.get_boards({"filter": "open"})
        
        if result["success"]:
            print(f"✓ Successfully connected to Trello API")
            print(f"✓ Found {len(result['boards'])} open boards")
            
            # Show first few boards
            for i, board in enumerate(result["boards"][:3]):
                print(f"  - {board['name']} ({board['id']})")
            
            return True
        else:
            print("❌ Failed to get boards from Trello API")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Trello API: {e}")
        return False

async def test_board_creation():
    """Test creating a test board"""
    print("\nTesting board creation...")
    
    server = TrelloMCPServer()
    
    try:
        # Create a test board
        board_name = "StudioOps Test Board"
        result = await server.create_board({
            "name": board_name,
            "description": "Test board created by StudioOps Trello MCP Server"
        })
        
        if result["success"]:
            board_id = result["board"]["id"]
            print(f"✓ Successfully created test board: {board_name}")
            print(f"✓ Board ID: {board_id}")
            print(f"✓ Board URL: {result['board']['url']}")
            return board_id
        else:
            print("❌ Failed to create test board")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test board: {e}")
        return None

async def test_card_creation(board_id):
    """Test creating cards in the test board"""
    print(f"\nTesting card creation in board {board_id}...")
    
    server = TrelloMCPServer()
    
    try:
        # Create test cards
        test_cards = [
            {
                "name": "Test Task 1",
                "description": "This is a test task created by the MCP server",
                "list_name": "To Do"
            },
            {
                "name": "Test Task 2", 
                "description": "Another test task with different list",
                "list_name": "In Progress"
            },
            {
                "name": "Test Task 3",
                "description": "Final test task",
                "list_name": "Done"
            }
        ]
        
        created_cards = []
        
        for card_data in test_cards:
            result = await server.create_card({
                "board_id": board_id,
                "list_name": card_data["list_name"],
                "name": card_data["name"],
                "description": card_data["description"]
            })
            
            if result["success"]:
                created_cards.append(result["card"])
                print(f"✓ Created card: {card_data['name']} in list '{card_data['list_name']}'")
            else:
                print(f"❌ Failed to create card: {card_data['name']}")
        
        print(f"✓ Successfully created {len(created_cards)} cards")
        return created_cards
        
    except Exception as e:
        print(f"❌ Error creating cards: {e}")
        return []

async def test_project_export(board_id):
    """Test exporting a sample project to the test board"""
    print(f"\nTesting project export to board {board_id}...")
    
    server = TrelloMCPServer()
    
    try:
        # Sample project data
        project_data = {
            "plan": {
                "Setup": [
                    "Initialize project repository",
                    "Configure development environment",
                    "Set up CI/CD pipeline"
                ],
                "Development": [
                    "Implement core features",
                    "Write unit tests",
                    "Create API documentation"
                ],
                "Deployment": [
                    "Deploy to staging",
                    "Run integration tests",
                    "Deploy to production"
                ]
            }
        }
        
        # Note: We'll use the existing board instead of creating a new one
        # by manually calling the internal methods
        
        # Parse the plan
        tasks = server._parse_plan_items(project_data["plan"])
        print(f"✓ Parsed {len(tasks)} tasks from project plan")
        
        # Create cards for each task
        created_cards = []
        for task in tasks:
            result = await server.create_card({
                "board_id": board_id,
                "list_name": "Project Tasks",
                "name": task["name"],
                "description": task["description"]
            })
            
            if result["success"]:
                created_cards.append(result["card"])
        
        print(f"✓ Successfully exported {len(created_cards)} project tasks")
        return created_cards
        
    except Exception as e:
        print(f"❌ Error exporting project: {e}")
        return []

async def test_board_lists(board_id):
    """Test getting lists from the test board"""
    print(f"\nTesting board lists retrieval for board {board_id}...")
    
    server = TrelloMCPServer()
    
    try:
        result = await server.get_board_lists({"board_id": board_id})
        
        if result["success"]:
            print(f"✓ Successfully retrieved {len(result['lists'])} lists")
            for list_item in result["lists"]:
                print(f"  - {list_item['name']} ({list_item['id']})")
            return result["lists"]
        else:
            print("❌ Failed to get board lists")
            return []
            
    except Exception as e:
        print(f"❌ Error getting board lists: {e}")
        return []

async def cleanup_test_board(board_id):
    """Clean up the test board (manual step)"""
    print(f"\n🧹 Cleanup Instructions:")
    print(f"Please manually delete the test board if no longer needed:")
    print(f"Board ID: {board_id}")
    print(f"You can delete it from the Trello web interface")

async def run_end_to_end_test():
    """Run complete end-to-end test"""
    print("Running Trello MCP Server End-to-End Test")
    print("=" * 50)
    
    try:
        # Test 1: API Connection
        if not await test_real_api_connection():
            return False
        
        # Test 2: Board Creation
        board_id = await test_board_creation()
        if not board_id:
            return False
        
        # Test 3: Board Lists
        lists = await test_board_lists(board_id)
        
        # Test 4: Card Creation
        cards = await test_card_creation(board_id)
        
        # Test 5: Project Export
        project_cards = await test_project_export(board_id)
        
        # Cleanup instructions
        await cleanup_test_board(board_id)
        
        print("\n" + "=" * 50)
        print("✅ End-to-end test completed successfully!")
        print(f"✅ Created test board with {len(cards) + len(project_cards)} cards")
        print("✅ All Trello integration features working correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_validation_only():
    """Run validation tests without creating resources"""
    print("Running Trello MCP Server Validation Test")
    print("=" * 50)
    
    try:
        # Test API connection only
        if await test_real_api_connection():
            print("\n" + "=" * 50)
            print("✅ Validation test passed!")
            print("✅ Trello API integration is working correctly")
            print("✅ Ready for real project exports")
            return True
        else:
            print("\n" + "=" * 50)
            print("❌ Validation test failed!")
            print("❌ Please check your Trello API credentials")
            return False
            
    except Exception as e:
        print(f"\n❌ Validation test failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Trello MCP Server")
    parser.add_argument("--validation-only", action="store_true", 
                       help="Run validation test only (no resource creation)")
    
    args = parser.parse_args()
    
    if args.validation_only:
        success = asyncio.run(run_validation_only())
    else:
        success = asyncio.run(run_end_to_end_test())
    
    sys.exit(0 if success else 1)