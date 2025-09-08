"""Enhanced Trello MCP Server for StudioOps AI Agent"""

import asyncio
import json
import os
import uuid
import time
import logging
from datetime import datetime
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrelloMCPServer:
    def __init__(self):
        self.server = Server("studioops-trello-mcp")
        self.api_key = os.getenv('TRELLO_API_KEY')
        self.token = os.getenv('TRELLO_TOKEN')
        self.base_url = "https://api.trello.com/1"
        
        # Enhanced credential validation
        self.credentials_valid = self._validate_credentials()
        self.connection_healthy = False
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutes
        
        if not self.credentials_valid:
            logger.warning(
                "Trello API credentials not configured or invalid. "
                "Trello integration will operate in mock mode. "
                "Set TRELLO_API_KEY and TRELLO_TOKEN environment variables."
            )
        else:
            logger.info("Trello API credentials validated successfully")
        
        self.setup_tools()
    
    def _validate_credentials(self) -> bool:
        """Validate Trello API credentials with connection test"""
        if not self.api_key or not self.token:
            logger.error("Missing Trello API credentials")
            return False
        
        try:
            # Test API connection with timeout
            response = requests.get(
                f"{self.base_url}/members/me",
                params={"key": self.api_key, "token": self.token},
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Trello API validation successful for user: {user_data.get('username', 'unknown')}")
                self.connection_healthy = True
                self.last_health_check = time.time()
                return True
            else:
                logger.error(f"Trello API validation failed with status: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Trello API validation timed out")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Trello API connection failed - network error")
            return False
        except Exception as e:
            logger.error(f"Trello API validation failed: {e}")
            return False
    
    def _check_health(self, force_check: bool = False) -> Dict[str, Any]:
        """Perform comprehensive health check and return detailed status"""
        current_time = time.time()
        
        # Only check if enough time has passed or forced
        if force_check or current_time - self.last_health_check > self.health_check_interval:
            connection_details = {
                "api_reachable": False,
                "user_info": None,
                "response_time": None,
                "error": None
            }
            
            if self.credentials_valid:
                try:
                    start_time = time.time()
                    response = requests.get(
                        f"{self.base_url}/members/me",
                        params={"key": self.api_key, "token": self.token},
                        timeout=10
                    )
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        self.connection_healthy = True
                        connection_details.update({
                            "api_reachable": True,
                            "user_info": response.json(),
                            "response_time": round(response_time, 3)
                        })
                    else:
                        self.connection_healthy = False
                        connection_details["error"] = f"HTTP {response.status_code}: {response.text}"
                        
                except requests.exceptions.Timeout:
                    self.connection_healthy = False
                    connection_details["error"] = "Request timeout (>10s)"
                except requests.exceptions.ConnectionError:
                    self.connection_healthy = False
                    connection_details["error"] = "Network connection failed"
                except Exception as e:
                    self.connection_healthy = False
                    connection_details["error"] = str(e)
            else:
                connection_details["error"] = "Invalid or missing API credentials"
            
            self.last_health_check = current_time
        
        # Determine overall status
        if self.credentials_valid and self.connection_healthy:
            status = "healthy"
            status_message = "All systems operational"
        elif self.credentials_valid and not self.connection_healthy:
            status = "degraded"
            status_message = "API credentials valid but connection failed - using mock responses"
        else:
            status = "mock_mode"
            status_message = "Invalid/missing credentials - operating in mock mode"
        
        return {
            "status": status,
            "status_message": status_message,
            "credentials_valid": self.credentials_valid,
            "connection_healthy": self.connection_healthy,
            "mock_mode": not (self.credentials_valid and self.connection_healthy),
            "last_check": self.last_health_check,
            "last_check_human": datetime.fromtimestamp(self.last_health_check).isoformat(),
            "connection_details": connection_details,
            "server_info": {
                "name": "StudioOps Trello MCP Server",
                "version": "1.0.0",
                "api_base_url": self.base_url,
                "health_check_interval": self.health_check_interval
            }
        }
    
    def setup_tools(self):
        """Setup available tools for the MCP server"""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available Trello management tools"""
            tools = [
                Tool(
                    name="health_check",
                    description="Check Trello MCP server health and connection status with detailed diagnostics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "force_check": {
                                "type": "boolean", 
                                "description": "Force a fresh health check instead of using cached results",
                                "default": False
                            },
                            "include_diagnostics": {
                                "type": "boolean",
                                "description": "Include detailed diagnostic information",
                                "default": True
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="create_board",
                    description="Create a new Trello board (with fallback to mock when API unavailable)",
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
                    description="Create a card in a Trello board (with fallback to mock when API unavailable)",
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
                    description="Get user's Trello boards (with fallback to mock when API unavailable)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {"type": "string", "enum": ["all", "open", "closed"], "default": "open"}
                        }
                    }
                ),
                Tool(
                    name="get_board_lists",
                    description="Get lists from a Trello board (with fallback to mock when API unavailable)",
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
                    description="Export project tasks to a Trello board (with fallback to mock when API unavailable)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string", "description": "Project ID from database"},
                            "board_name": {"type": "string", "description": "Name for the new Trello board (optional)"},
                            "project_data": {"type": "object", "description": "Project data including plan items"}
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="test_connection",
                    description="Test Trello API connection with comprehensive diagnostics and validation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "test_operations": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["auth", "boards", "create_test_board", "cleanup"]},
                                "description": "Specific operations to test (default: all)",
                                "default": ["auth", "boards"]
                            },
                            "cleanup_test_data": {
                                "type": "boolean",
                                "description": "Whether to clean up any test data created during testing",
                                "default": True
                            }
                        },
                        "additionalProperties": False
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool execution requests with comprehensive error handling"""
            try:
                logger.info(f"Executing tool: {request.name}")
                
                if request.name == "health_check":
                    force_check = request.arguments.get("force_check", False)
                    include_diagnostics = request.arguments.get("include_diagnostics", True)
                    result = self._check_health(force_check=force_check)
                    
                    if not include_diagnostics:
                        # Return simplified status for basic checks
                        result = {
                            "status": result["status"],
                            "status_message": result["status_message"],
                            "mock_mode": result["mock_mode"],
                            "connection_healthy": result["connection_healthy"]
                        }
                elif request.name == "create_board":
                    result = await self.create_board(request.arguments)
                elif request.name == "create_card":
                    result = await self.create_card(request.arguments)
                elif request.name == "get_boards":
                    result = await self.get_boards(request.arguments)
                elif request.name == "get_board_lists":
                    result = await self.get_board_lists(request.arguments)
                elif request.name == "export_project_tasks":
                    result = await self.export_project_tasks(request.arguments)
                elif request.name == "test_connection":
                    result = await self.test_connection(request.arguments)
                else:
                    raise ValueError(f"Unknown tool: {request.name}")
                
                logger.info(f"Tool {request.name} executed successfully")
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))],
                    isError=False
                )
            
            except Exception as e:
                error_msg = f"Tool {request.name} failed: {str(e)}"
                logger.error(error_msg)
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )
    
    def _make_request_with_retry(self, method: str, endpoint: str, 
                                params: Dict = None, data: Dict = None, 
                                max_retries: int = 3, base_delay: float = 1.0) -> Dict:
        """Make API request with enhanced retry logic and comprehensive error handling"""
        if not self.credentials_valid:
            logger.info(f"Using mock response for {method} {endpoint} (credentials invalid)")
            mock_response = self._mock_response(method, endpoint, params, data)
            mock_response["_error_details"] = {
                "last_error": "Invalid or missing API credentials",
                "attempts": 0,
                "endpoint": endpoint,
                "method": method
            }
            return mock_response
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        auth_params = {"key": self.api_key, "token": self.token}
        
        if params:
            auth_params.update(params)
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1}/{max_retries} for {method} {endpoint}")
                
                # Calculate exponential backoff with jitter
                if attempt > 0:
                    jitter = 0.1 * (2 ** attempt) * (0.5 + 0.5 * time.time() % 1)
                    wait_time = base_delay * (2 ** (attempt - 1)) + jitter
                    logger.debug(f"Waiting {wait_time:.2f}s before retry")
                    time.sleep(wait_time)
                
                start_time = time.time()
                response = requests.request(
                    method=method.upper(),
                    url=url,
                    params=auth_params,
                    json=data,
                    timeout=30
                )
                response_time = time.time() - start_time
                
                logger.debug(f"API response: {response.status_code} in {response_time:.3f}s")
                
                # Handle rate limiting with proper backoff
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
                    logger.warning(f"Rate limited (429), waiting {retry_after}s before retry")
                    time.sleep(retry_after)
                    continue
                
                # Handle server errors with exponential backoff
                if response.status_code >= 500:
                    if attempt < max_retries - 1:
                        logger.warning(f"Server error {response.status_code}, will retry")
                        continue
                    else:
                        last_error = f"Server error {response.status_code}: {response.text}"
                        break
                
                # Handle client errors (don't retry)
                if 400 <= response.status_code < 500:
                    last_error = f"Client error {response.status_code}: {response.text}"
                    logger.error(f"Client error for {method} {endpoint}: {last_error}")
                    break
                
                response.raise_for_status()
                
                # Update connection health on success
                self.connection_healthy = True
                self.last_health_check = time.time()
                
                logger.debug(f"Successful API call to {endpoint}")
                return response.json()
                
            except requests.exceptions.Timeout as e:
                last_error = f"Request timeout after 30s"
                logger.warning(f"Request timeout on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Trello API request timed out after {max_retries} attempts")
                    self.connection_healthy = False
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Trello API connection failed after {max_retries} attempts")
                    self.connection_healthy = False
                
            except requests.exceptions.RequestException as e:
                last_error = f"Request exception: {str(e)}"
                logger.warning(f"Request exception on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Trello API request failed after {max_retries} attempts: {e}")
                    self.connection_healthy = False
        
        # All retries failed, use mock response
        logger.warning(f"All retry attempts failed for {method} {endpoint}, using mock response. Last error: {last_error}")
        mock_response = self._mock_response(method, endpoint, params, data)
        mock_response["_error_details"] = {
            "last_error": last_error,
            "attempts": max_retries,
            "endpoint": endpoint,
            "method": method
        }
        return mock_response
    
    def _mock_response(self, method: str, endpoint: str, 
                      params: Dict = None, data: Dict = None) -> Dict:
        """Provide mock responses when Trello API is unavailable"""
        logger.info(f"Generating mock response for {method} {endpoint}")
        
        if "members/me" in endpoint:
            return {
                "id": "mock_user_id",
                "username": "mock_user",
                "fullName": "Mock User",
                "email": "mock@example.com",
                "mock": True
            }
        
        elif "boards" in endpoint and method.upper() == "POST":
            board_id = f"mock_board_{uuid.uuid4().hex[:8]}"
            return {
                "id": board_id,
                "name": params.get("name", "Mock Board"),
                "url": f"https://trello.com/b/{board_id}/mock-board",
                "desc": params.get("desc", ""),
                "prefs": {"permissionLevel": params.get("prefs_permissionLevel", "private")},
                "mock": True,
                "message": "Mock board created - Trello API unavailable"
            }
        
        elif "boards" in endpoint and method.upper() == "GET":
            mock_boards = [
                {
                    "id": "mock_board_1",
                    "name": "Mock Project Board",
                    "url": "https://trello.com/b/mock1/mock-project-board",
                    "desc": "Mock board for testing",
                    "closed": False,
                    "mock": True
                },
                {
                    "id": "mock_board_2", 
                    "name": "Mock Development Board",
                    "url": "https://trello.com/b/mock2/mock-development-board",
                    "desc": "Another mock board",
                    "closed": False,
                    "mock": True
                }
            ]
            # Ensure the list itself is marked as mock
            for board in mock_boards:
                board["mock"] = True
            return mock_boards
        
        elif "lists" in endpoint and method.upper() == "POST":
            list_id = f"mock_list_{uuid.uuid4().hex[:8]}"
            return {
                "id": list_id,
                "name": params.get("name", "Mock List"),
                "closed": False,
                "pos": 16384,
                "idBoard": params.get("idBoard", "mock_board"),
                "mock": True
            }
        
        elif "/lists" in endpoint and method.upper() == "GET":
            mock_lists = [
                {
                    "id": "mock_list_todo",
                    "name": "To Do",
                    "closed": False,
                    "pos": 16384,
                    "mock": True
                },
                {
                    "id": "mock_list_progress",
                    "name": "In Progress", 
                    "closed": False,
                    "pos": 32768,
                    "mock": True
                },
                {
                    "id": "mock_list_done",
                    "name": "Done",
                    "closed": False,
                    "pos": 49152,
                    "mock": True
                }
            ]
            # Ensure all lists are marked as mock
            for list_item in mock_lists:
                list_item["mock"] = True
            return mock_lists
        
        elif "cards" in endpoint and method.upper() == "POST":
            card_id = f"mock_card_{uuid.uuid4().hex[:8]}"
            return {
                "id": card_id,
                "name": params.get("name", "Mock Card"),
                "url": f"https://trello.com/c/{card_id}/mock-card",
                "desc": params.get("desc", ""),
                "idList": params.get("idList", "mock_list"),
                "idBoard": "mock_board",
                "due": params.get("due"),
                "mock": True,
                "message": "Mock card created - Trello API unavailable"
            }
        
        elif "cards" in endpoint and method.upper() == "GET":
            return {
                "id": "mock_card_info",
                "name": "Mock Card",
                "idBoard": "mock_board",
                "idList": "mock_list",
                "mock": True
            }
        
        elif "labels" in endpoint:
            if method.upper() == "POST":
                return {
                    "id": f"mock_label_{uuid.uuid4().hex[:8]}",
                    "name": params.get("name", "Mock Label"),
                    "color": params.get("color", "blue"),
                    "idBoard": params.get("idBoard", "mock_board"),
                    "mock": True
                }
            else:
                return [
                    {
                        "id": "mock_label_1",
                        "name": "High Priority",
                        "color": "red",
                        "mock": True
                    },
                    {
                        "id": "mock_label_2", 
                        "name": "In Review",
                        "color": "yellow",
                        "mock": True
                    }
                ]
        
        # Default mock response
        return {
            "mock": True,
            "message": f"Mock response for {method} {endpoint} - Trello API unavailable",
            "endpoint": endpoint,
            "method": method,
            "params": params,
            "data": data
        }
    
    async def test_connection(self, args: Dict[str, Any]) -> Dict:
        """Comprehensive connection testing with detailed diagnostics"""
        test_operations = args.get("test_operations", ["auth", "boards"])
        cleanup_test_data = args.get("cleanup_test_data", True)
        
        results = {
            "overall_status": "unknown",
            "test_results": [],
            "summary": {},
            "recommendations": [],
            "timestamp": datetime.now().isoformat()
        }
        
        test_board_id = None
        
        try:
            # Test 1: Authentication and basic API access
            if "auth" in test_operations:
                auth_result = await self._test_authentication()
                results["test_results"].append(auth_result)
            
            # Test 2: List boards access
            if "boards" in test_operations:
                boards_result = await self._test_boards_access()
                results["test_results"].append(boards_result)
            
            # Test 3: Create test board (if requested)
            if "create_test_board" in test_operations:
                create_result = await self._test_board_creation()
                results["test_results"].append(create_result)
                if create_result["success"] and not create_result.get("mock_mode", False):
                    test_board_id = create_result.get("board_id")
            
            # Test 4: Cleanup test data (if requested and created)
            if "cleanup" in test_operations and test_board_id and cleanup_test_data:
                cleanup_result = await self._test_cleanup(test_board_id)
                results["test_results"].append(cleanup_result)
            
            # Generate summary
            total_tests = len(results["test_results"])
            passed_tests = sum(1 for test in results["test_results"] if test["success"])
            failed_tests = total_tests - passed_tests
            
            results["summary"] = {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
            }
            
            # Determine overall status
            if failed_tests == 0:
                results["overall_status"] = "healthy"
            elif passed_tests > 0:
                results["overall_status"] = "degraded"
            else:
                results["overall_status"] = "failed"
            
            # Generate recommendations
            results["recommendations"] = self._generate_recommendations(results["test_results"])
            
            return results
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            results["overall_status"] = "error"
            results["error"] = str(e)
            return results
    
    async def _test_authentication(self) -> Dict:
        """Test API authentication"""
        test_result = {
            "test_name": "Authentication",
            "success": False,
            "message": "",
            "details": {},
            "mock_mode": False
        }
        
        try:
            if not self.credentials_valid:
                test_result.update({
                    "success": False,
                    "message": "API credentials not configured or invalid",
                    "mock_mode": True,
                    "details": {
                        "has_api_key": bool(self.api_key),
                        "has_token": bool(self.token),
                        "credentials_validated": False
                    }
                })
                return test_result
            
            start_time = time.time()
            response = self._make_request_with_retry("GET", "/members/me", max_retries=2)
            response_time = time.time() - start_time
            
            if response.get("mock", False):
                test_result.update({
                    "success": False,
                    "message": "API call failed, using mock response",
                    "mock_mode": True,
                    "details": {
                        "error": response.get("_error_details", {}).get("last_error", "Unknown error"),
                        "response_time": response_time
                    }
                })
            else:
                test_result.update({
                    "success": True,
                    "message": f"Successfully authenticated as {response.get('username', 'unknown')}",
                    "details": {
                        "username": response.get("username"),
                        "full_name": response.get("fullName"),
                        "email": response.get("email"),
                        "response_time": response_time
                    }
                })
            
        except Exception as e:
            test_result.update({
                "success": False,
                "message": f"Authentication test failed: {str(e)}",
                "details": {"error": str(e)}
            })
        
        return test_result
    
    async def _test_boards_access(self) -> Dict:
        """Test boards listing access"""
        test_result = {
            "test_name": "Boards Access",
            "success": False,
            "message": "",
            "details": {},
            "mock_mode": False
        }
        
        try:
            start_time = time.time()
            response = self._make_request_with_retry("GET", "/members/me/boards", max_retries=2)
            response_time = time.time() - start_time
            
            if isinstance(response, list) and not any(board.get("mock", False) for board in response):
                test_result.update({
                    "success": True,
                    "message": f"Successfully retrieved {len(response)} boards",
                    "details": {
                        "board_count": len(response),
                        "response_time": response_time,
                        "boards": [{"id": b["id"], "name": b["name"]} for b in response[:5]]  # First 5 boards
                    }
                })
            elif isinstance(response, list):
                test_result.update({
                    "success": False,
                    "message": "API call failed, using mock boards",
                    "mock_mode": True,
                    "details": {
                        "mock_board_count": len(response),
                        "response_time": response_time
                    }
                })
            else:
                test_result.update({
                    "success": False,
                    "message": "Unexpected response format from boards API",
                    "details": {"response_type": type(response).__name__}
                })
                
        except Exception as e:
            test_result.update({
                "success": False,
                "message": f"Boards access test failed: {str(e)}",
                "details": {"error": str(e)}
            })
        
        return test_result
    
    async def _test_board_creation(self) -> Dict:
        """Test board creation"""
        test_result = {
            "test_name": "Board Creation",
            "success": False,
            "message": "",
            "details": {},
            "mock_mode": False,
            "board_id": None
        }
        
        try:
            test_board_name = f"StudioOps Test Board {int(time.time())}"
            
            board_result = await self.create_board({
                "name": test_board_name,
                "description": "Test board created by StudioOps MCP server connection test"
            })
            
            if board_result["success"]:
                test_result.update({
                    "success": True,
                    "message": f"Successfully created test board: {test_board_name}",
                    "mock_mode": board_result.get("mock_mode", False),
                    "board_id": board_result["board"]["id"],
                    "details": {
                        "board_name": test_board_name,
                        "board_url": board_result["board"].get("url"),
                        "mock_mode": board_result.get("mock_mode", False)
                    }
                })
            else:
                test_result.update({
                    "success": False,
                    "message": "Board creation failed",
                    "details": {"error": "Board creation returned success=False"}
                })
                
        except Exception as e:
            test_result.update({
                "success": False,
                "message": f"Board creation test failed: {str(e)}",
                "details": {"error": str(e)}
            })
        
        return test_result
    
    async def _test_cleanup(self, board_id: str) -> Dict:
        """Test cleanup of test data"""
        test_result = {
            "test_name": "Cleanup",
            "success": False,
            "message": "",
            "details": {}
        }
        
        try:
            # Only attempt cleanup for real boards (not mock)
            if board_id.startswith("mock_"):
                test_result.update({
                    "success": True,
                    "message": "Mock board cleanup not required",
                    "details": {"board_id": board_id, "mock": True}
                })
                return test_result
            
            # Delete the test board
            response = self._make_request_with_retry("DELETE", f"/boards/{board_id}", max_retries=2)
            
            if not response.get("mock", False):
                test_result.update({
                    "success": True,
                    "message": "Successfully cleaned up test board",
                    "details": {"board_id": board_id}
                })
            else:
                test_result.update({
                    "success": False,
                    "message": "Cleanup failed - API unavailable",
                    "details": {"board_id": board_id, "mock": True}
                })
                
        except Exception as e:
            test_result.update({
                "success": False,
                "message": f"Cleanup test failed: {str(e)}",
                "details": {"error": str(e), "board_id": board_id}
            })
        
        return test_result
    
    def _generate_recommendations(self, test_results: List[Dict]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        auth_test = next((t for t in test_results if t["test_name"] == "Authentication"), None)
        boards_test = next((t for t in test_results if t["test_name"] == "Boards Access"), None)
        
        if auth_test and not auth_test["success"]:
            if not auth_test["details"].get("has_api_key"):
                recommendations.append("Set TRELLO_API_KEY environment variable with your Trello API key")
            if not auth_test["details"].get("has_token"):
                recommendations.append("Set TRELLO_TOKEN environment variable with your Trello token")
            if auth_test["details"].get("has_api_key") and auth_test["details"].get("has_token"):
                recommendations.append("Verify that your Trello API credentials are valid and have not expired")
        
        if boards_test and not boards_test["success"] and auth_test and auth_test["success"]:
            recommendations.append("Check if your Trello token has the required permissions to read boards")
        
        if any(t.get("mock_mode", False) for t in test_results):
            recommendations.append("Server is operating in mock mode - configure valid Trello API credentials for full functionality")
        
        if not recommendations:
            recommendations.append("All tests passed - Trello integration is working correctly")
        
        return recommendations

    async def create_board(self, args: Dict[str, Any]) -> Dict:
        """Create a new Trello board with enhanced error handling"""
        try:
            params = {
                "name": args["name"],
                "desc": args.get("description", ""),
                "prefs_permissionLevel": args.get("visibility", "private")
            }
            
            result = self._make_request_with_retry("POST", "/boards", params=params)
            
            return {
                "success": True,
                "mock_mode": result.get("mock", False),
                "board": {
                    "id": result["id"],
                    "name": result["name"],
                    "url": result["url"],
                    "description": result.get("desc", ""),
                    "visibility": result.get("prefs", {}).get("permissionLevel", "private"),
                    "mock": result.get("mock", False)
                },
                "message": result.get("message", "Board created successfully")
            }
        except Exception as e:
            logger.error(f"Failed to create board: {e}")
            raise Exception(f"Failed to create board '{args['name']}': {str(e)}")
    
    async def create_card(self, args: Dict[str, Any]) -> Dict:
        """Create a card in a Trello board with enhanced error handling"""
        try:
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
            
            result = self._make_request_with_retry("POST", "/cards", params=params)
            
            # Add labels if specified (only if not in mock mode)
            labels_added = []
            if args.get("labels") and not result.get("mock", False):
                try:
                    labels_added = await self._add_labels_to_card(result["id"], args["labels"])
                except Exception as e:
                    logger.warning(f"Failed to add labels to card: {e}")
            
            return {
                "success": True,
                "mock_mode": result.get("mock", False),
                "card": {
                    "id": result["id"],
                    "name": result["name"],
                    "url": result["url"],
                    "description": result.get("desc", ""),
                    "list_id": result["idList"],
                    "due_date": result.get("due"),
                    "labels": labels_added,
                    "mock": result.get("mock", False)
                },
                "message": result.get("message", "Card created successfully")
            }
        except Exception as e:
            logger.error(f"Failed to create card: {e}")
            raise Exception(f"Failed to create card '{args['name']}': {str(e)}")
    
    async def get_boards(self, args: Dict[str, Any]) -> Dict:
        """Get user's Trello boards with enhanced error handling"""
        try:
            filter_type = args.get("filter", "open")
            
            result = self._make_request_with_retry("GET", "/members/me/boards", params={"filter": filter_type})
            
            # Handle both mock and real responses
            if isinstance(result, list):
                boards = []
                for board in result:
                    boards.append({
                        "id": board["id"],
                        "name": board["name"],
                        "url": board["url"],
                        "description": board.get("desc", ""),
                        "closed": board.get("closed", False),
                        "mock": board.get("mock", False)
                    })
            else:
                # Handle mock response format
                boards = [{
                    "id": "mock_board",
                    "name": "Mock Board",
                    "url": "https://trello.com/mock",
                    "description": "Mock board - API unavailable",
                    "closed": False,
                    "mock": True
                }]
            
            return {
                "success": True,
                "mock_mode": any(board.get("mock", False) for board in boards),
                "boards": boards,
                "count": len(boards)
            }
        except Exception as e:
            logger.error(f"Failed to get boards: {e}")
            raise Exception(f"Failed to retrieve boards: {str(e)}")
    
    async def get_board_lists(self, args: Dict[str, Any]) -> Dict:
        """Get lists from a Trello board with enhanced error handling"""
        try:
            board_id = args["board_id"]
            
            result = self._make_request_with_retry("GET", f"/boards/{board_id}/lists")
            
            # Handle both mock and real responses
            if isinstance(result, list):
                lists = []
                for list_item in result:
                    lists.append({
                        "id": list_item["id"],
                        "name": list_item["name"],
                        "closed": list_item.get("closed", False),
                        "position": list_item.get("pos"),
                        "mock": list_item.get("mock", False)
                    })
            else:
                # Handle unexpected response format
                lists = []
            
            return {
                "success": True,
                "mock_mode": any(lst.get("mock", False) for lst in lists),
                "board_id": board_id,
                "lists": lists,
                "count": len(lists)
            }
        except Exception as e:
            logger.error(f"Failed to get board lists: {e}")
            raise Exception(f"Failed to retrieve lists for board {args['board_id']}: {str(e)}")
    
    async def _get_or_create_list(self, board_id: str, list_name: str) -> str:
        """Get existing list or create new one with enhanced error handling"""
        try:
            # Get existing lists
            lists = self._make_request_with_retry("GET", f"/boards/{board_id}/lists")
            
            # Handle both mock and real responses
            if isinstance(lists, list):
                # Check if list already exists
                for list_item in lists:
                    if isinstance(list_item, dict) and list_item.get("name") == list_name:
                        return list_item["id"]
            elif isinstance(lists, dict) and lists.get("mock", False):
                # Handle case where mock response is a dict instead of list
                logger.info(f"Mock response received for lists, creating mock list for '{list_name}'")
                return f"mock_list_{uuid.uuid4().hex[:8]}"
            
            # Create new list
            params = {
                "name": list_name,
                "idBoard": board_id
            }
            
            result = self._make_request_with_retry("POST", "/lists", params=params)
            if isinstance(result, dict) and "id" in result:
                return result["id"]
            else:
                # Fallback to mock ID if result is unexpected
                logger.warning(f"Unexpected result format when creating list: {result}")
                return f"mock_list_{uuid.uuid4().hex[:8]}"
            
        except Exception as e:
            logger.error(f"Failed to get or create list '{list_name}': {e}")
            # Return a mock list ID if everything fails
            return f"mock_list_{uuid.uuid4().hex[:8]}"
    
    async def _add_labels_to_card(self, card_id: str, label_names: List[str]) -> List[str]:
        """Add labels to a card with enhanced error handling"""
        added_labels = []
        
        try:
            # Get board labels first
            card_info = self._make_request_with_retry("GET", f"/cards/{card_id}")
            
            # Skip if mock response
            if card_info.get("mock", False):
                logger.info("Skipping label addition for mock card")
                return [f"mock_label_{name}" for name in label_names]
            
            board_id = card_info["idBoard"]
            board_labels = self._make_request_with_retry("GET", f"/boards/{board_id}/labels")
            
            # Handle mock board labels
            if not isinstance(board_labels, list):
                board_labels = []
            
            for label_name in label_names:
                try:
                    # Find existing label or create new one
                    label_id = None
                    for label in board_labels:
                        if label["name"] == label_name:
                            label_id = label["id"]
                            break
                    
                    if not label_id:
                        # Create new label
                        label_result = self._make_request_with_retry("POST", "/labels", params={
                            "name": label_name,
                            "color": "blue",  # Default color
                            "idBoard": board_id
                        })
                        label_id = label_result["id"]
                    
                    # Add label to card
                    self._make_request_with_retry("POST", f"/cards/{card_id}/idLabels", params={"value": label_id})
                    added_labels.append(label_name)
                    
                except Exception as e:
                    logger.warning(f"Failed to add label '{label_name}' to card: {e}")
                    continue
            
            return added_labels
            
        except Exception as e:
            logger.error(f"Failed to add labels to card {card_id}: {e}")
            return []
    
    async def export_project_tasks(self, args: Dict[str, Any]) -> Dict:
        """Export project tasks to Trello board with enhanced error handling"""
        try:
            project_id = args["project_id"]
            project_data = args.get("project_data", {})
            board_name = args.get("board_name", f"Project {project_id}")
            
            logger.info(f"Exporting project {project_id} to Trello board '{board_name}'")
            
            # Create board for the project
            board_result = await self.create_board({
                "name": board_name,
                "description": f"Tasks for project {project_id}"
            })
            
            board_id = board_result["board"]["id"]
            is_mock = board_result.get("mock_mode", False)
            
            # Default lists to create
            default_lists = ["To Do", "In Progress", "Done"]
            
            # Create default lists
            lists_created = []
            for list_name in default_lists:
                try:
                    list_id = await self._get_or_create_list(board_id, list_name)
                    lists_created.append({"name": list_name, "id": list_id})
                except Exception as e:
                    logger.warning(f"Failed to create list '{list_name}': {e}")
            
            # Export tasks if project data is provided
            cards_created = []
            cards_failed = []
            
            if project_data and "plan" in project_data:
                plan = project_data["plan"]
                
                # Parse plan items
                tasks = self._parse_plan_items(plan)
                logger.info(f"Parsed {len(tasks)} tasks from project plan")
                
                for task in tasks:
                    try:
                        card_result = await self.create_card({
                            "board_id": board_id,
                            "list_name": "To Do",
                            "name": task["name"],
                            "description": task.get("description", ""),
                            "labels": task.get("labels", [])
                        })
                        cards_created.append(card_result["card"])
                    except Exception as e:
                        logger.error(f"Failed to create card for task '{task['name']}': {e}")
                        cards_failed.append({
                            "task_name": task["name"],
                            "error": str(e)
                        })
            
            return {
                "success": True,
                "mock_mode": is_mock,
                "project_id": project_id,
                "board": board_result["board"],
                "lists_created": lists_created,
                "cards_created": len(cards_created),
                "cards_failed": len(cards_failed),
                "cards": cards_created,
                "failed_cards": cards_failed,
                "message": f"Exported {len(cards_created)} tasks to Trello board" + 
                          (f" ({len(cards_failed)} failed)" if cards_failed else "")
            }
            
        except Exception as e:
            logger.error(f"Failed to export project tasks: {e}")
            raise Exception(f"Failed to export project {args['project_id']} to Trello: {str(e)}")
    
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
    """Main function to run the enhanced MCP server"""
    try:
        server = TrelloMCPServer()
        logger.info("Starting Enhanced Trello MCP Server")
        
        async with stdio_server() as (read_stream, write_stream):
            await server.server.run(
                read_stream,
                write_stream,
                server.server.create_initialization_options(),
            )
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())