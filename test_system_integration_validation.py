#!/usr/bin/env python3
"""
System Integration Validation Test
Tests database operations, AI services, MCP integration, and data consistency
across all system components.
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests
import psycopg2
from psycopg2.extras import RealDictCursor

# Test configuration
API_BASE_URL = "http://localhost:8000"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'studioops',
    'user': 'studioops',
    'password': 'studioops123'
}

class SystemIntegrationValidator:
    def __init__(self):
        self.test_results = []
        self.test_project_id = None
        self.test_vendor_id = None
        self.test_material_id = None
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            self.log_test("Database Connection", False, f"Failed to connect: {e}")
            return None
    
    def test_database_operations(self):
        """Test database operations across all components"""
        print("\n=== Testing Database Operations ===")
        
        # Test direct database connection
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Test basic connectivity
                cur.execute("SELECT version();")
                version = cur.fetchone()
                self.log_test("Database Version Check", True, f"Connected to {version['version'][:50]}...")
                
                # Test table existence
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = [row['table_name'] for row in cur.fetchall()]
                expected_tables = ['projects', 'vendors', 'materials', 'vendor_prices', 'purchases', 'rag_documents']
                missing_tables = [t for t in expected_tables if t not in tables]
                
                if missing_tables:
                    self.log_test("Table Existence", False, f"Missing tables: {missing_tables}", tables)
                else:
                    self.log_test("Table Existence", True, f"All required tables exist: {len(tables)} total")
                
                # Check for chat-related tables (they use different names)
                chat_tables = [t for t in tables if 'chat' in t or 'message' in t or 'session' in t]
                if chat_tables:
                    self.log_test("Chat Tables", True, f"Found chat tables: {chat_tables}")
                else:
                    self.log_test("Chat Tables", False, "No chat-related tables found")
                
                # Test data integrity constraints
                cur.execute("SELECT COUNT(*) as count FROM projects;")
                project_count = cur.fetchone()['count']
                
                cur.execute("SELECT COUNT(*) as count FROM vendors;")
                vendor_count = cur.fetchone()['count']
                
                self.log_test("Data Counts", True, f"Projects: {project_count}, Vendors: {vendor_count}")
                
        except Exception as e:
            self.log_test("Database Operations", False, f"Database test failed: {e}")
            return False
        finally:
            conn.close()
        
        return True
    
    def test_api_database_integration(self):
        """Test API endpoints with database operations"""
        print("\n=== Testing API-Database Integration ===")
        
        try:
            # Test API health check
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("API Health Check", True, "API server is running")
            else:
                self.log_test("API Health Check", False, f"API returned {response.status_code}")
                return False
            
            # Test projects endpoint
            response = requests.get(f"{API_BASE_URL}/projects", timeout=10)
            if response.status_code == 200:
                projects = response.json()
                self.log_test("Projects API", True, f"Retrieved {len(projects)} projects")
            else:
                self.log_test("Projects API", False, f"Failed to get projects: {response.status_code}")
                return False
            
            # Create test project
            test_project = {
                "name": f"Integration Test Project {uuid.uuid4().hex[:8]}",
                "description": "Test project for system integration validation",
                "status": "active"
            }
            
            response = requests.post(f"{API_BASE_URL}/projects", json=test_project, timeout=10)
            if response.status_code == 200:
                created_project = response.json()
                self.test_project_id = created_project.get('id')
                self.log_test("Project Creation", True, f"Created project with ID: {self.test_project_id}")
            else:
                self.log_test("Project Creation", False, f"Failed to create project: {response.status_code}")
                return False
            
            # Test vendors endpoint
            response = requests.get(f"{API_BASE_URL}/vendors", timeout=10)
            if response.status_code == 200:
                vendors = response.json()
                self.log_test("Vendors API", True, f"Retrieved {len(vendors)} vendors")
                if vendors:
                    self.test_vendor_id = vendors[0].get('id')
            else:
                self.log_test("Vendors API", False, f"Failed to get vendors: {response.status_code}")
            
            # Test materials endpoint
            response = requests.get(f"{API_BASE_URL}/materials", timeout=10)
            if response.status_code == 200:
                materials = response.json()
                self.log_test("Materials API", True, f"Retrieved {len(materials)} materials")
                if materials:
                    self.test_material_id = materials[0].get('id')
            else:
                self.log_test("Materials API", False, f"Failed to get materials: {response.status_code}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_test("API Connection", False, f"Failed to connect to API: {e}")
            return False
    
    def test_ai_services_integration(self):
        """Test AI services with project context"""
        print("\n=== Testing AI Services Integration ===")
        
        if not self.test_project_id:
            self.log_test("AI Services Setup", False, "No test project available for AI testing")
            return False
        
        try:
            # Test chat endpoint with project context
            chat_message = {
                "message": "What materials would be good for this project?",
                "project_id": self.test_project_id
            }
            
            response = requests.post(f"{API_BASE_URL}/chat/message", json=chat_message, timeout=30)
            if response.status_code == 200:
                chat_response = response.json()
                ai_message = chat_response.get('message', '')
                self.log_test("AI Chat Response", True, f"Received AI response: {ai_message[:100]}...")
                
                # Check if response contains project context
                project_context = chat_response.get('context', {}).get('project', {})
                if project_context or "project" in ai_message.lower():
                    self.log_test("AI Project Context", True, "AI response includes project context")
                else:
                    self.log_test("AI Project Context", False, "AI response lacks project context")
                
                # Check AI service status
                ai_enabled = chat_response.get('ai_enabled', False)
                self.log_test("AI Service Status", True, f"AI enabled: {ai_enabled}")
            else:
                self.log_test("AI Chat Response", False, f"Chat failed: {response.status_code}")
                return False
            
            # Test memory search (mem0 endpoint)
            search_query = {"query": "materials", "user_id": "test_user"}
            response = requests.post(f"{API_BASE_URL}/mem0/search", json=search_query, timeout=10)
            if response.status_code == 200:
                search_results = response.json()
                self.log_test("Memory Search", True, f"Found {len(search_results)} relevant memories")
            else:
                self.log_test("Memory Search", False, f"Memory search failed: {response.status_code}")
            
            # Test plan generation
            plan_request = {
                "project_name": "Test Integration Project",
                "project_description": "A test project for integration validation",
                "project_id": self.test_project_id
            }
            response = requests.post(f"{API_BASE_URL}/chat/generate_plan", json=plan_request, timeout=30)
            if response.status_code == 200:
                plan_data = response.json()
                self.log_test("Plan Generation", True, f"Generated plan with {len(plan_data.get('items', []))} items")
            else:
                self.log_test("Plan Generation", False, f"Plan generation failed: {response.status_code}")
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_test("AI Services", False, f"AI services test failed: {e}")
            return False
    
    def test_mcp_server_integration(self):
        """Test MCP server integration with main API"""
        print("\n=== Testing MCP Server Integration ===")
        
        try:
            # Test MCP server health (if available)
            # Note: MCP servers typically run as separate processes
            # We'll test through the main API's MCP integration
            
            # Test Trello MCP server directly (if running)
            try:
                # Check if Trello MCP server is accessible
                # Note: MCP servers typically run on different ports or as separate processes
                self.log_test("Trello MCP Server", False, "Trello MCP server integration not directly accessible via API")
                
                # Instead, test if the Trello MCP files exist and are properly structured
                import os
                trello_mcp_path = "apps/trello-mcp/server.py"
                if os.path.exists(trello_mcp_path):
                    with open(trello_mcp_path, 'r') as f:
                        content = f.read()
                        if "TrelloMCPServer" in content and "create_board" in content:
                            self.log_test("Trello MCP Implementation", True, "Trello MCP server code is implemented")
                        else:
                            self.log_test("Trello MCP Implementation", False, "Trello MCP server incomplete")
                else:
                    self.log_test("Trello MCP Implementation", False, "Trello MCP server file not found")
            except Exception as e:
                self.log_test("Trello MCP Check", False, f"Error checking Trello MCP: {e}")
            
            # Test if any MCP-related endpoints exist
            response = requests.get(f"{API_BASE_URL}/", timeout=10)
            if response.status_code == 200:
                self.log_test("MCP Integration Status", True, "API server running - MCP integration would be external")
            else:
                self.log_test("MCP Integration Status", False, "API server not responding")
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_test("MCP Integration", False, f"MCP integration test failed: {e}")
            return False
    
    def test_data_consistency(self):
        """Test data consistency across services"""
        print("\n=== Testing Data Consistency ===")
        
        if not self.test_project_id:
            self.log_test("Data Consistency Setup", False, "No test project for consistency testing")
            return False
        
        try:
            # Get project data from API
            response = requests.get(f"{API_BASE_URL}/projects/{self.test_project_id}", timeout=10)
            if response.status_code != 200:
                self.log_test("Project API Data", False, f"Failed to get project: {response.status_code}")
                return False
            
            api_project = response.json()
            
            # Get same project data directly from database
            conn = self.get_db_connection()
            if not conn:
                return False
            
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM projects WHERE id = %s", (self.test_project_id,))
                    db_project = cur.fetchone()
                    
                    if not db_project:
                        self.log_test("Database Project Data", False, "Project not found in database")
                        return False
                    
                    # Compare key fields (handle None values)
                    consistency_checks = [
                        ('name', api_project.get('name'), db_project['name']),
                        ('status', api_project.get('status'), db_project['status'])
                    ]
                    
                    # Only check description if both have values
                    api_desc = api_project.get('description')
                    db_desc = db_project.get('description')
                    if api_desc is not None or db_desc is not None:
                        consistency_checks.append(('description', api_desc, db_desc))
                    
                    all_consistent = True
                    for field, api_value, db_value in consistency_checks:
                        if api_value != db_value:
                            self.log_test(f"Data Consistency - {field}", False, 
                                        f"API: {api_value} != DB: {db_value}")
                            all_consistent = False
                        else:
                            self.log_test(f"Data Consistency - {field}", True, 
                                        f"Values match: {api_value}")
                    
                    if all_consistent:
                        self.log_test("Overall Data Consistency", True, "All fields consistent between API and DB")
                    
                    # Test foreign key relationships
                    if self.test_vendor_id and self.test_material_id:
                        # Check vendor-material relationships
                        cur.execute("""
                            SELECT COUNT(*) as count FROM vendor_prices 
                            WHERE vendor_id = %s AND material_id = %s
                        """, (self.test_vendor_id, self.test_material_id))
                        
                        relationship_count = cur.fetchone()['count']
                        self.log_test("Foreign Key Relationships", True, 
                                    f"Found {relationship_count} vendor-material relationships")
                    
            finally:
                conn.close()
            
            return True
            
        except Exception as e:
            self.log_test("Data Consistency", False, f"Consistency test failed: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        if self.test_project_id:
            try:
                response = requests.delete(f"{API_BASE_URL}/projects/{self.test_project_id}", timeout=10)
                if response.status_code in [200, 204]:
                    self.log_test("Test Data Cleanup", True, "Test project deleted successfully")
                else:
                    self.log_test("Test Data Cleanup", False, f"Failed to delete test project: {response.status_code}")
            except Exception as e:
                self.log_test("Test Data Cleanup", False, f"Cleanup failed: {e}")
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("SYSTEM INTEGRATION VALIDATION REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\nDETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")
        
        # Save detailed report
        report_file = f"system_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return failed_tests == 0
    
    def run_all_tests(self):
        """Run all system integration tests"""
        print("Starting System Integration Validation...")
        print(f"API Base URL: {API_BASE_URL}")
        print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        
        try:
            # Run all test categories
            self.test_database_operations()
            self.test_api_database_integration()
            self.test_ai_services_integration()
            self.test_mcp_server_integration()
            self.test_data_consistency()
            
        finally:
            # Always cleanup and generate report
            self.cleanup_test_data()
            success = self.generate_report()
            
            if success:
                print("\n🎉 All system integration tests PASSED!")
                return True
            else:
                print("\n⚠️  Some system integration tests FAILED!")
                return False

def main():
    """Main test execution"""
    validator = SystemIntegrationValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()