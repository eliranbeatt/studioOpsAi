#!/usr/bin/env python3
"""
Enhanced Trello MCP Server Test Suite
Tests all the enhanced functionality including health checks, connection testing, and error handling
"""

import asyncio
import json
import os
import sys
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any

# Add the apps directory to the path
sys.path.append('apps')
sys.path.append('apps/trello-mcp')

def test_server_import_and_instantiation():
    """Test server import and basic instantiation"""
    print("=== Testing Server Import and Instantiation ===")
    
    results = []
    
    try:
        from server import TrelloMCPServer
        results.append(("Server Import", True, "Successfully imported TrelloMCPServer"))
        
        # Test instantiation without credentials
        os.environ.pop('TRELLO_API_KEY', None)
        os.environ.pop('TRELLO_TOKEN', None)
        
        server = TrelloMCPServer()
        results.append(("Server Instantiation (No Creds)", True, "Successfully created server instance without credentials"))
        
        # Verify mock mode is enabled
        health = server._check_health(force_check=True)
        if health["mock_mode"]:
            results.append(("Mock Mode Detection", True, "Server correctly detected missing credentials and enabled mock mode"))
        else:
            results.append(("Mock Mode Detection", False, "Server should be in mock mode without credentials"))
        
        # Test instantiation with mock credentials
        os.environ['TRELLO_API_KEY'] = 'test_key_invalid'
        os.environ['TRELLO_TOKEN'] = 'test_token_invalid'
        
        server_with_creds = TrelloMCPServer()
        results.append(("Server Instantiation (Mock Creds)", True, "Successfully created server instance with mock credentials"))
        
        # Test health check functionality
        health_detailed = server_with_creds._check_health(force_check=True)
        if "status" in health_detailed and "connection_details" in health_detailed:
            results.append(("Enhanced Health Check", True, "Health check returns detailed status information"))
        else:
            results.append(("Enhanced Health Check", False, "Health check missing required fields"))
        
    except ImportError as e:
        results.append(("Server Import", False, f"Failed to import TrelloMCPServer: {e}"))
    except Exception as e:
        results.append(("Server Instantiation", False, f"Failed to instantiate server: {e}"))
    
    return results

def test_health_check_functionality():
    """Test enhanced health check functionality"""
    print("=== Testing Enhanced Health Check Functionality ===")
    
    results = []
    
    try:
        from server import TrelloMCPServer
        
        # Test with invalid credentials
        os.environ['TRELLO_API_KEY'] = 'invalid_key'
        os.environ['TRELLO_TOKEN'] = 'invalid_token'
        
        server = TrelloMCPServer()
        
        # Test basic health check
        health = server._check_health(force_check=True)
        
        required_fields = [
            "status", "status_message", "credentials_valid", "connection_healthy",
            "mock_mode", "last_check", "connection_details", "server_info"
        ]
        
        missing_fields = [field for field in required_fields if field not in health]
        if not missing_fields:
            results.append(("Health Check Fields", True, "All required health check fields present"))
        else:
            results.append(("Health Check Fields", False, f"Missing fields: {missing_fields}"))
        
        # Test status determination
        if health["status"] in ["healthy", "degraded", "mock_mode"]:
            results.append(("Status Values", True, f"Valid status: {health['status']}"))
        else:
            results.append(("Status Values", False, f"Invalid status: {health['status']}"))
        
        # Test connection details
        if "connection_details" in health and isinstance(health["connection_details"], dict):
            conn_details = health["connection_details"]
            if "api_reachable" in conn_details and "error" in conn_details:
                results.append(("Connection Details", True, "Connection details properly structured"))
            else:
                results.append(("Connection Details", False, "Connection details missing required fields"))
        else:
            results.append(("Connection Details", False, "Connection details not properly structured"))
        
        # Test server info
        if "server_info" in health and isinstance(health["server_info"], dict):
            server_info = health["server_info"]
            if "name" in server_info and "version" in server_info:
                results.append(("Server Info", True, "Server info properly included"))
            else:
                results.append(("Server Info", False, "Server info missing required fields"))
        else:
            results.append(("Server Info", False, "Server info not properly structured"))
        
    except Exception as e:
        results.append(("Health Check Test", False, f"Health check test failed: {e}"))
    
    return results

def test_retry_logic_and_error_handling():
    """Test enhanced retry logic and error handling"""
    print("=== Testing Retry Logic and Error Handling ===")
    
    results = []
    
    try:
        from server import TrelloMCPServer
        
        # Test with invalid credentials to trigger retry logic
        os.environ['TRELLO_API_KEY'] = 'invalid_key'
        os.environ['TRELLO_TOKEN'] = 'invalid_token'
        
        server = TrelloMCPServer()
        
        # Test API request with retry logic
        start_time = time.time()
        response = server._make_request_with_retry("GET", "/members/me", max_retries=2, base_delay=0.1)
        elapsed_time = time.time() - start_time
        
        # Should return mock response due to invalid credentials
        if response.get("mock", False):
            results.append(("Retry Logic Fallback", True, "Correctly fell back to mock response after retries"))
        else:
            results.append(("Retry Logic Fallback", False, "Should have returned mock response"))
        
        # Check for error details in mock response
        if "_error_details" in response:
            error_details = response["_error_details"]
            if "last_error" in error_details and "attempts" in error_details:
                results.append(("Error Details", True, "Error details properly included in mock response"))
            else:
                results.append(("Error Details", False, "Error details missing required fields"))
        else:
            results.append(("Error Details", False, "Error details not included in mock response"))
        
        # Test that retry logic takes appropriate time (should be quick with base_delay=0.1)
        if elapsed_time < 5.0:  # Should complete quickly with short delays
            results.append(("Retry Timing", True, f"Retry logic completed in reasonable time: {elapsed_time:.2f}s"))
        else:
            results.append(("Retry Timing", False, f"Retry logic took too long: {elapsed_time:.2f}s"))
        
    except Exception as e:
        results.append(("Retry Logic Test", False, f"Retry logic test failed: {e}"))
    
    return results

async def test_connection_testing_tool():
    """Test the new connection testing tool"""
    print("=== Testing Connection Testing Tool ===")
    
    results = []
    
    try:
        from server import TrelloMCPServer
        
        # Test with invalid credentials
        os.environ['TRELLO_API_KEY'] = 'invalid_key'
        os.environ['TRELLO_TOKEN'] = 'invalid_token'
        
        server = TrelloMCPServer()
        
        # Test connection testing with basic operations
        test_result = await server.test_connection({
            "test_operations": ["auth", "boards"],
            "cleanup_test_data": True
        })
        
        # Check overall structure
        required_fields = ["overall_status", "test_results", "summary", "recommendations", "timestamp"]
        missing_fields = [field for field in required_fields if field not in test_result]
        
        if not missing_fields:
            results.append(("Connection Test Structure", True, "All required fields present in connection test result"))
        else:
            results.append(("Connection Test Structure", False, f"Missing fields: {missing_fields}"))
        
        # Check test results
        if isinstance(test_result["test_results"], list) and len(test_result["test_results"]) > 0:
            results.append(("Test Results", True, f"Generated {len(test_result['test_results'])} test results"))
            
            # Check individual test structure
            first_test = test_result["test_results"][0]
            test_fields = ["test_name", "success", "message", "details"]
            missing_test_fields = [field for field in test_fields if field not in first_test]
            
            if not missing_test_fields:
                results.append(("Individual Test Structure", True, "Individual tests properly structured"))
            else:
                results.append(("Individual Test Structure", False, f"Missing test fields: {missing_test_fields}"))
        else:
            results.append(("Test Results", False, "No test results generated"))
        
        # Check summary
        if isinstance(test_result["summary"], dict):
            summary_fields = ["total_tests", "passed", "failed", "success_rate"]
            missing_summary_fields = [field for field in summary_fields if field not in test_result["summary"]]
            
            if not missing_summary_fields:
                results.append(("Test Summary", True, "Test summary properly structured"))
            else:
                results.append(("Test Summary", False, f"Missing summary fields: {missing_summary_fields}"))
        else:
            results.append(("Test Summary", False, "Test summary not properly structured"))
        
        # Check recommendations
        if isinstance(test_result["recommendations"], list) and len(test_result["recommendations"]) > 0:
            results.append(("Recommendations", True, f"Generated {len(test_result['recommendations'])} recommendations"))
        else:
            results.append(("Recommendations", False, "No recommendations generated"))
        
    except Exception as e:
        results.append(("Connection Testing Tool", False, f"Connection testing tool failed: {e}"))
    
    return results

def test_mock_response_enhancements():
    """Test enhanced mock response functionality"""
    print("=== Testing Enhanced Mock Response Functionality ===")
    
    results = []
    
    try:
        from server import TrelloMCPServer
        
        # Test without credentials to ensure mock mode
        os.environ.pop('TRELLO_API_KEY', None)
        os.environ.pop('TRELLO_TOKEN', None)
        
        server = TrelloMCPServer()
        
        # Test various mock responses
        mock_tests = [
            ("GET", "/members/me", "User info mock"),
            ("POST", "/boards", "Board creation mock"),
            ("GET", "/boards", "Boards list mock"),
            ("POST", "/cards", "Card creation mock"),
            ("GET", "/boards/test/lists", "Board lists mock")
        ]
        
        for method, endpoint, description in mock_tests:
            try:
                response = server._mock_response(method, endpoint, {"name": "Test"}, None)
                
                # Check if response is properly formatted (dict with mock=True or list with mock items)
                is_valid_mock = False
                if isinstance(response, dict) and response.get("mock", False):
                    is_valid_mock = True
                elif isinstance(response, list) and len(response) > 0 and all(item.get("mock", False) for item in response):
                    is_valid_mock = True
                
                if is_valid_mock:
                    results.append((description, True, f"Generated appropriate mock response for {method} {endpoint}"))
                else:
                    results.append((description, False, f"Mock response not properly formatted for {method} {endpoint}"))
                    
            except Exception as e:
                results.append((description, False, f"Mock response failed for {method} {endpoint}: {e}"))
        
        # Test mock response with error details
        response_with_error = server._make_request_with_retry("GET", "/members/me", max_retries=1)
        if response_with_error.get("mock", False) and "_error_details" in response_with_error:
            results.append(("Mock Error Details", True, "Mock responses include error details when API fails"))
        else:
            results.append(("Mock Error Details", False, "Mock responses should include error details"))
        
    except Exception as e:
        results.append(("Mock Response Test", False, f"Mock response test failed: {e}"))
    
    return results

async def test_board_operations_with_fallback():
    """Test board operations with fallback to mock"""
    print("=== Testing Board Operations with Fallback ===")
    
    results = []
    
    try:
        from server import TrelloMCPServer
        
        # Test with invalid credentials to trigger fallback
        os.environ['TRELLO_API_KEY'] = 'invalid_key'
        os.environ['TRELLO_TOKEN'] = 'invalid_token'
        
        server = TrelloMCPServer()
        
        # Test board creation
        board_result = await server.create_board({
            "name": "Test Board",
            "description": "Test board for fallback testing"
        })
        
        if board_result["success"] and board_result.get("mock_mode", False):
            results.append(("Board Creation Fallback", True, "Board creation successfully fell back to mock"))
        else:
            results.append(("Board Creation Fallback", False, "Board creation fallback not working properly"))
        
        # Test card creation
        card_result = await server.create_card({
            "board_id": "mock_board_123",
            "list_name": "To Do",
            "name": "Test Card",
            "description": "Test card for fallback testing"
        })
        
        if card_result["success"] and card_result.get("mock_mode", False):
            results.append(("Card Creation Fallback", True, "Card creation successfully fell back to mock"))
        else:
            results.append(("Card Creation Fallback", False, "Card creation fallback not working properly"))
        
        # Test boards listing
        boards_result = await server.get_boards({"filter": "open"})
        
        if boards_result["success"] and boards_result.get("mock_mode", False):
            results.append(("Boards Listing Fallback", True, "Boards listing successfully fell back to mock"))
        else:
            results.append(("Boards Listing Fallback", False, "Boards listing fallback not working properly"))
        
    except Exception as e:
        results.append(("Board Operations Test", False, f"Board operations test failed: {e}"))
    
    return results

async def main():
    """Run all enhanced Trello MCP server tests"""
    print("Starting Enhanced Trello MCP Server Tests...")
    print("=" * 60)
    
    all_results = []
    
    # Run all test suites
    test_suites = [
        ("Import and Instantiation", test_server_import_and_instantiation()),
        ("Health Check Functionality", test_health_check_functionality()),
        ("Retry Logic and Error Handling", test_retry_logic_and_error_handling()),
        ("Connection Testing Tool", await test_connection_testing_tool()),
        ("Mock Response Enhancements", test_mock_response_enhancements()),
        ("Board Operations with Fallback", await test_board_operations_with_fallback())
    ]
    
    for suite_name, suite_results in test_suites:
        print(f"\n--- {suite_name} ---")
        for test_name, success, message in suite_results:
            status = "✅" if success else "❌"
            print(f"  {status} {test_name}: {message}")
        all_results.extend(suite_results)
    
    # Generate final report
    print("\n" + "=" * 60)
    print("ENHANCED TRELLO MCP SERVER TEST REPORT")
    print("=" * 60)
    
    total_tests = len(all_results)
    passed_tests = sum(1 for result in all_results if result[1])
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\nFAILED TESTS:")
        for test_name, success, message in all_results:
            if not success:
                print(f"  ❌ {test_name}: {message}")
    
    # Save detailed report
    report_data = {
        "test_suite": "Enhanced Trello MCP Server Tests",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0
        },
        "results": [
            {
                "test": result[0],
                "success": result[1], 
                "message": result[2]
            }
            for result in all_results
        ]
    }
    
    report_file = f"trello_mcp_enhanced_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    if failed_tests == 0:
        print("\n🎉 All enhanced Trello MCP server tests PASSED!")
        return True
    else:
        print("\n⚠️  Some enhanced Trello MCP server tests FAILED!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)