"""Trello MCP Server for StudioOps AI Agent"""

import asyncio
import json
import os
import uuid
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    ListToolsResult,
    CallToolResult,
    CallToolRequest,
)

# Load environment variables
load_dotenv()

class TrelloMCPServer:
    def __init__(self):
        self.server = Server("studioops-trello-mcp")
        self.api_key = os.getenv('TRELLO_API_KEY')
        self.token = os.getenv('TRELLO_TOKEN')
        self.base_url = "https://api.trello.com/1"
        
        if not self.api_key or not self.token:
            print("Warning: Trello API credentials not configured. Set TRELLO_API_KEY and TRELLO_TOKEN environment variables.")
        
        self.setup_tools()
    
    def setup_tools(self):
        """Setup available tools for the MCP server"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available Trello management tools"""
            tools = [
                Tool(
                    name="create_board",
                    description="Create a new Trello board",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Board name"},
                            "description": {"type": "string", "description": "Board description (optional)"},
                            "visibility": {"type": "string", "enum": ["private", "public", "org"], "default": "private"}
                        },
                        "required": ["name"]
                    }
                ),
                Tool(
                    name="create_card",
                    description="Create a card in a Trello board",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "board_id": {"type": "string", "description": "Board ID where to create the card"},
                            "list_name": {"type": "string", "description": "List name (will be created if doesn't exist)"},
                            "name": {"type": "string", "description": "Card name"},
                            "description": {"type": "string", "description": "Card description (optional)"},
                            "due_date": {"type": "string", "description": "Due date in ISO format (optional)"},
                            "labels": {"type": "array", "items": {"type": "string"}, "description": "Label names (optional)"}
                        },
                        "required": ["board_id", "list_name", "name"]
                    }
                ),
                Tool(
                    name="get_boards",
                    description="Get user's Trello boards",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {"type": "string", "enum": ["all", "open", "closed"], "default": "open"}
                        }
                    }
                ),
                Tool(
                    name="get_board_lists",
                    description="Get lists from a Trello board",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "board_id": {"type": "string", "description": "Board ID"}
                        },
                        "required": ["board_id"]
                    }
                ),
                Tool(
                    name="export_project_tasks",
                    description="Export project tasks to a Trello board",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string", "description": "Project ID from database"},
                            "board_name": {"type": "string", "description": "Name for the new Trello board (optional)"},
                            "project_data": {"type": "object", "description": "Project data including plan items"}
                        },
                        "required": ["project_id"]
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool execution requests"""
            try:
                if not self.api_key or not self.token:
                    raise ValueError("Trello API credentials not configured")
                
                if request.name == "create_board":
                    result = await self.create_board(request.arguments)
                elif request.name == "create_card":
                    result = await self.create_card(request.arguments)
                elif request.name == "get_boards":
                    result = await self.get_boards(request.arguments)
                elif request.name == "get_board_lists":
                    result = await self.get_board_lists(request.arguments)
                elif request.name == "export_project_tasks":
                    result = await self.export_project_tasks(request.arguments)
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
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make authenticated request to Trello API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Add authentication parameters
        auth_params = {
            "key": self.api_key,
            "token": self.token
        }
        
        if params:
            auth_params.update(params)
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=auth_params)
            elif method.upper() == "POST":
                response = requests.post(url, params=auth_params, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, params=auth_params, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, params=auth_params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Trello API request failed: {e}")
        except Exception as e:
            raise Exception(f"Trello API request failed: {e}")
    
    async def create_board(self, args: Dict[str, Any]) -> Dict:
        """Create a new Trello board"""
        if not self.api_key or not self.token:
            raise ValueError("Trello API credentials not configured")
            
        params = {
            "name": args["name"],
            "desc": args.get("description", ""),
            "prefs_permissionLevel": args.get("visibility", "private")
        }
        
        result = self._make_request("POST", "/boards", params=params)
        
        return {
            "success": True,
            "board": {
                "id": result["id"],
                "name": result["name"],
                "url": result["url"],
                "description": result.get("desc", ""),
                "visibility": result.get("prefs", {}).get("permissionLevel", "private")
            }
        }
    
    async def create_card(self, args: Dict[str, Any]) -> Dict:
        """Create a card in a Trello board"""
        if not self.api_key or not self.token:
            raise ValueError("Trello API credentials not configured")
            
        board_id = args["board_id"]
        list_name = args["list_name"]
        
        # Get or create the list
        list_id = await self._get_or_create_list(board_id, list_name)
        
        params = {
            "name": args["name"],
            "desc": args.get("description", ""),
            "idList": list_id
        }
        
        if args.get("due_date"):
            params["due"] = args["due_date"]
        
        result = self._make_request("POST", "/cards", params=params)
        
        # Add labels if specified
        if args.get("labels"):
            await self._add_labels_to_card(result["id"], args["labels"])
        
        return {
            "success": True,
            "card": {
                "id": result["id"],
                "name": result["name"],
                "url": result["url"],
                "description": result.get("desc", ""),
                "list_id": result["idList"],
                "due_date": result.get("due")
            }
        }
    
    async def get_boards(self, args: Dict[str, Any]) -> Dict:
        """Get user's Trello boards"""
        if not self.api_key or not self.token:
            raise ValueError("Trello API credentials not configured")
            
        filter_type = args.get("filter", "open")
        
        result = self._make_request("GET", "/members/me/boards", params={"filter": filter_type})
        
        boards = []
        for board in result:
            boards.append({
                "id": board["id"],
                "name": board["name"],
                "url": board["url"],
                "description": board.get("desc", ""),
                "closed": board.get("closed", False)
            })
        
        return {
            "success": True,
            "boards": boards
        }
    
    async def get_board_lists(self, args: Dict[str, Any]) -> Dict:
        """Get lists from a Trello board"""
        if not self.api_key or not self.token:
            raise ValueError("Trello API credentials not configured")
            
        board_id = args["board_id"]
        
        result = self._make_request("GET", f"/boards/{board_id}/lists")
        
        lists = []
        for list_item in result:
            lists.append({
                "id": list_item["id"],
                "name": list_item["name"],
                "closed": list_item.get("closed", False),
                "position": list_item.get("pos")
            })
        
        return {
            "success": True,
            "lists": lists
        }
    
    async def _get_or_create_list(self, board_id: str, list_name: str) -> str:
        """Get existing list or create new one"""
        # Get existing lists
        lists = self._make_request("GET", f"/boards/{board_id}/lists")
        
        # Check if list already exists
        for list_item in lists:
            if list_item["name"] == list_name:
                return list_item["id"]
        
        # Create new list
        params = {
            "name": list_name,
            "idBoard": board_id
        }
        
        result = self._make_request("POST", "/lists", params=params)
        return result["id"]
    
    async def _add_labels_to_card(self, card_id: str, label_names: List[str]) -> None:
        """Add labels to a card"""
        # Get board labels first
        card_info = self._make_request("GET", f"/cards/{card_id}")
        board_id = card_info["idBoard"]
        
        board_labels = self._make_request("GET", f"/boards/{board_id}/labels")
        
        for label_name in label_names:
            # Find existing label or create new one
            label_id = None
            for label in board_labels:
                if label["name"] == label_name:
                    label_id = label["id"]
                    break
            
            if not label_id:
                # Create new label
                label_result = self._make_request("POST", "/labels", params={
                    "name": label_name,
                    "color": "blue",  # Default color
                    "idBoard": board_id
                })
                label_id = label_result["id"]
            
            # Add label to card
            self._make_request("POST", f"/cards/{card_id}/idLabels", params={"value": label_id})
    
    async def export_project_tasks(self, args: Dict[str, Any]) -> Dict:
        """Export project tasks to Trello board"""
        if not self.api_key or not self.token:
            raise ValueError("Trello API credentials not configured")
            
        project_id = args["project_id"]
        project_data = args.get("project_data", {})
        board_name = args.get("board_name", f"Project {project_id}")
        
        # Create board for the project
        board_result = await self.create_board({
            "name": board_name,
            "description": f"Tasks for project {project_id}"
        })
        
        board_id = board_result["board"]["id"]
        
        # Default lists to create
        default_lists = ["To Do", "In Progress", "Done"]
        
        # Create default lists
        for list_name in default_lists:
            await self._get_or_create_list(board_id, list_name)
        
        # Export tasks if project data is provided
        cards_created = []
        if project_data and "plan" in project_data:
            plan = project_data["plan"]
            
            # Parse plan items (assuming it's a structured format)
            tasks = self._parse_plan_items(plan)
            
            for task in tasks:
                card_result = await self.create_card({
                    "board_id": board_id,
                    "list_name": "To Do",
                    "name": task["name"],
                    "description": task.get("description", ""),
                    "labels": task.get("labels", [])
                })
                cards_created.append(card_result["card"])
        
        return {
            "success": True,
            "board": board_result["board"],
            "cards_created": len(cards_created),
            "cards": cards_created
        }
    
    def _parse_plan_items(self, plan: Any) -> List[Dict]:
        """Parse plan items into task format"""
        tasks = []
        
        if isinstance(plan, str):
            # Simple text plan - split by lines
            lines = plan.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove markdown formatting
                    task_name = line.lstrip('- *').strip()
                    if task_name:
                        tasks.append({
                            "name": task_name,
                            "description": "",
                            "labels": []
                        })
        
        elif isinstance(plan, list):
            # Structured plan items
            for item in plan:
                if isinstance(item, dict):
                    tasks.append({
                        "name": item.get("title", item.get("name", "Untitled Task")),
                        "description": item.get("description", ""),
                        "labels": item.get("labels", [])
                    })
                elif isinstance(item, str):
                    tasks.append({
                        "name": item,
                        "description": "",
                        "labels": []
                    })
        
        elif isinstance(plan, dict):
            # Plan with sections
            for section_name, section_items in plan.items():
                if isinstance(section_items, list):
                    for item in section_items:
                        task_name = item if isinstance(item, str) else item.get("name", "Untitled Task")
                        tasks.append({
                            "name": f"{section_name}: {task_name}",
                            "description": item.get("description", "") if isinstance(item, dict) else "",
                            "labels": [section_name.lower()]
                        })
        
        return tasks

async def main():
    """Main function to run the MCP server"""
    server = TrelloMCPServer()
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            server.server.create_initialization_options(),
        )

if __name__ == "__main__":
    asyncio.run(main())