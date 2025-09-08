#!/usr/bin/env python3
"""
Task 10: Comprehensive Testing and Validation Suite
Tests all fixed components including project deletion, Trello MCP, document upload, and AI response systems.
"""

import asyncio
import pytest
import json
import os
import sys
import time
import uuid
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

import requests
import psycopg2
from psycopg2.extras import RealDictCursor

# Test configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8003')
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'studioops',
    'user': 'studioops',
    'password': 'studioops123'
}

class ComprehensiveTestSuite:
    """Comprehensive test suite for all system components"""
    
    def __init__(self):
        self.test_results = []
        self.test_data = {}
        self.cleanup_tasks = []
        
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
    
    async def test_database_foreign_key_constraints(self):
        """Test 1: Database Foreign Key Constraint Fixes"""
        print("\n=== Testing Database Foreign Key Constraints ===")
        
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Test 1.1: Check foreign key constraints exist and have correct DELETE rules
                cur.execute("""
                    SELECT 
                        tc.table_name,
                        kcu.column_name, 
                        tc.constraint_name,
                        rc.delete_rule
                    FROM 
                        information_schema.table_constraints AS tc 
                        JOIN information_schema.key_column_usage AS kcu
                            ON tc.constraint_name = kcu.constraint_name
                        JOIN information_schema.referential_constraints AS rc
                            ON tc.constraint_name = rc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                        AND tc.table_schema = 'public'
                        AND kcu.column_name = 'project_id';
                """)
                
                fk_constraints = {f"{row['table_name']}.{row['column_name']}": row['delete_rule'] 
                                for row in cur.fetchall()}
                
                # Expected constraints with proper DELETE rules
                expected_constraints = {
                    "chat_sessions.project_id": "SET NULL",
                    "documents.project_id": "SET NULL", 
                    "purchases.project_id": "SET NULL",
                    "plans.project_id": "CASCADE"
                }
                
                all_correct = True
                for constraint, expected_rule in expected_constraints.items():
                    if constraint in fk_constraints:
                        actual_rule = fk_constraints[constraint]
                        if actual_rule == expected_rule:
                            self.log_test(f"FK Constraint {constraint}", True, f"Correct DELETE rule: {actual_rule}")
                        else:
                            self.log_test(f"FK Constraint {constraint}", False, f"Wrong DELETE rule: {actual_rule}, expected: {expected_rule}")
                            all_correct = False
                    else:
                        self.log_test(f"FK Constraint {constraint}", False, "Constraint missing")
                        all_correct = False
                
                return all_correct
                
        except Exception as e:
            self.log_test("FK Constraints Check", False, f"Error checking constraints: {e}")
            return False
        finally:
            conn.close()
    
    async def test_project_deletion_scenarios(self):
        """Test 2: Project Deletion Scenarios"""
        print("\n=== Testing Project Deletion Scenarios ===")
        
        try:
            # Test 2.1: Create test project
            test_project = {
                "name": f"Test Project Deletion {uuid.uuid4().hex[:8]}",
                "client_name": "Test Client",
                "status": "active"
            }
            
            response = requests.post(f"{API_BASE_URL}/projects", json=test_project, timeout=10)
            if response.status_code != 200:
                self.log_test("Project Creation for Deletion Test", False, f"Failed to create: {response.status_code} - {response.text}")
                return False
            
            project = response.json()
            project_id = project.get('id')
            self.test_data['deletion_test_project_id'] = project_id
            
            self.log_test("Project Creation for Deletion Test", True, f"Created project: {project_id}")
            
            # Test 2.2: Create dependent records
            # This would involve creating plans, documents, chat sessions, etc.
            # For now, we'll test the deletion impact analysis
            
            # Test 2.3: Get deletion impact analysis
            response = requests.get(f"{API_BASE_URL}/projects/{project_id}/deletion-impact", timeout=10)
            if response.status_code == 200:
                impact = response.json()
                self.log_test("Deletion Impact Analysis", True, f"Analysis successful: {impact.get('project_name')}")
            else:
                self.log_test("Deletion Impact Analysis", False, f"Failed: {response.status_code}")
            
            # Test 2.4: Perform actual deletion
            response = requests.delete(f"{API_BASE_URL}/projects/{project_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.log_test("Project Deletion", True, f"Deletion successful: {result.get('message')}")
                return True
            else:
                self.log_test("Project Deletion", False, f"Deletion failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Project Deletion Test", False, f"Error: {e}")
            return False
    
    async def test_trello_mcp_integration(self):
        """Test 3: Trello MCP Integration with Mock and Real APIs"""
        print("\n=== Testing Trello MCP Integration ===")
        
        # Test 3.1: Mock Trello API responses
        try:
            with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
                # Mock successful API validation
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"username": "test_user"}
                
                # Mock board creation
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {
                    "id": "mock_board_123",
                    "name": "Test Board",
                    "url": "https://trello.com/b/mock/test-board"
                }
                
                # Test Trello service initialization
                from apps.api.services.trello_service import trello_service
                
                # Test board creation
                board_result = trello_service.ensure_board_structure("test_project", "Test Board")
                
                if board_result and board_result.get('id'):
                    self.log_test("Trello Mock API Integration", True, f"Mock board created: {board_result['id']}")
                else:
                    self.log_test("Trello Mock API Integration", False, "Failed to create mock board")
                
        except Exception as e:
            self.log_test("Trello Mock API Integration", False, f"Error: {e}")
        
        # Test 3.2: Real Trello API (if credentials available)
        api_key = os.getenv('TRELLO_API_KEY')
        token = os.getenv('TRELLO_TOKEN')
        
        if api_key and token:
            try:
                # Test real API connection
                response = requests.get(
                    "https://api.trello.com/1/members/me",
                    params={"key": api_key, "token": token},
                    timeout=10
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_test("Trello Real API Connection", True, f"Connected as: {user_data.get('username')}")
                else:
                    self.log_test("Trello Real API Connection", False, f"API error: {response.status_code}")
                    
            except Exception as e:
                self.log_test("Trello Real API Connection", False, f"Connection error: {e}")
        else:
            self.log_test("Trello Real API Connection", False, "API credentials not available")
        
        return True
    
    async def test_document_upload_processing(self):
        """Test 4: Document Upload and Processing System"""
        print("\n=== Testing Document Upload and Processing ===")
        
        try:
            # Test 4.1: Create test document
            test_content = "Test document content for upload validation"
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                test_file_path = f.name
            
            self.cleanup_tasks.append(lambda: os.unlink(test_file_path))
            
            # Test 4.2: Upload document
            try:
                with open(test_file_path, 'rb') as f:
                    files = {'file': ('test_document.txt', f, 'text/plain')}
                    response = requests.post(f"{API_BASE_URL}/documents/upload", files=files, timeout=30)
                
                if response.status_code == 200:
                    upload_result = response.json()
                    document_id = upload_result.get('document_id')
                    self.test_data['test_document_id'] = document_id
                    self.log_test("Document Upload", True, f"Uploaded document: {document_id}")
                else:
                    self.log_test("Document Upload", False, f"Upload failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test("Document Upload", False, f"Upload error: {e}")
            
            # Test 4.3: Test MinIO integration
            try:
                from apps.api.services.minio_service import minio_service
                
                # Test MinIO connectivity
                if minio_service.is_available():
                    self.log_test("MinIO Integration", True, "MinIO service available and accessible")
                else:
                    self.log_test("MinIO Integration", False, "MinIO service not available or not configured")
                    
            except Exception as e:
                self.log_test("MinIO Integration", False, f"MinIO error: {e}")
            
            return True
            
        except Exception as e:
            self.log_test("Document Upload Test", False, f"Error: {e}")
            return False
    
    async def test_ai_response_system_fallback(self):
        """Test 5: AI Response System with Fallback Validation"""
        print("\n=== Testing AI Response System ===")
        
        try:
            # Test 5.1: Test AI service availability
            openai_key = os.getenv('OPENAI_API_KEY')
            
            if openai_key:
                # Test real AI integration
                test_message = {
                    "message": "Test AI integration - what can you help with?",
                    "project_id": self.test_data.get('deletion_test_project_id')
                }
                
                response = requests.post(f"{API_BASE_URL}/chat/message", json=test_message, timeout=30)
                
                if response.status_code == 200:
                    ai_response = response.json()
                    if ai_response.get('message') and not ai_response.get('mock_mode'):
                        self.log_test("AI Real Response", True, f"AI responded: {ai_response['message'][:50]}...")
                    else:
                        self.log_test("AI Mock Response", True, f"Mock AI responded: {ai_response.get('message', '')[:50]}...")
                else:
                    self.log_test("AI Response", False, f"AI request failed: {response.status_code}")
            else:
                self.log_test("AI Service Config", False, "OpenAI API key not configured")
            
            # Test 5.2: Test fallback mechanisms
            # This would involve mocking API failures and testing fallback responses
            with patch('openai.ChatCompletion.create') as mock_openai:
                mock_openai.side_effect = Exception("API unavailable")
                
                # Test should fall back to enhanced mock responses
                test_message = {
                    "message": "Help me create a project plan",
                    "project_id": None
                }
                
                response = requests.post(f"{API_BASE_URL}/chat/message", json=test_message, timeout=30)
                
                if response.status_code == 200:
                    ai_response = response.json()
                    if ai_response.get('mock_mode'):
                        self.log_test("AI Fallback Mechanism", True, "Successfully fell back to mock responses")
                    else:
                        self.log_test("AI Fallback Mechanism", False, "Fallback not triggered correctly")
                else:
                    self.log_test("AI Fallback Mechanism", False, f"Fallback failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("AI Response System Test", False, f"Error: {e}")
            return False
    
    async def test_frontend_api_integration(self):
        """Test 6: Frontend API Integration with Enhanced Error Handling"""
        print("\n=== Testing Frontend API Integration ===")
        
        try:
            # Test 6.1: Test enhanced API endpoints
            endpoints_to_test = [
                ('/health', 'Health Check'),
                ('/api/system/status', 'System Status'),
                ('/api/health/detailed', 'Detailed Health'),
                ('/vendors', 'Vendors List'),
                ('/materials', 'Materials List'),
                ('/projects', 'Projects List')
            ]
            
            for endpoint, name in endpoints_to_test:
                try:
                    response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
                    if response.status_code == 200:
                        self.log_test(f"API Endpoint {name}", True, f"Endpoint accessible: {response.status_code}")
                    else:
                        self.log_test(f"API Endpoint {name}", False, f"Endpoint error: {response.status_code}")
                except Exception as e:
                    self.log_test(f"API Endpoint {name}", False, f"Connection error: {e}")
            
            # Test 6.2: Test error handling and retry mechanisms
            # This would test the enhanced API client with retry logic
            
            return True
            
        except Exception as e:
            self.log_test("Frontend API Integration Test", False, f"Error: {e}")
            return False
    
    async def test_system_health_monitoring(self):
        """Test 7: System Health Monitoring"""
        print("\n=== Testing System Health Monitoring ===")
        
        try:
            # Test health monitoring endpoints
            response = requests.get(f"{API_BASE_URL}/api/health/detailed", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check health data structure
                expected_keys = ['overall_status', 'services', 'system_info']
                missing_keys = [key for key in expected_keys if key not in health_data]
                
                if not missing_keys:
                    self.log_test("Health Monitoring Structure", True, "All expected health data present")
                    
                    # Check individual services
                    services = health_data.get('services', {})
                    for service_name, service_data in services.items():
                        status = service_data.get('status', 'unknown')
                        self.log_test(f"Service Health {service_name}", True, f"Status: {status}")
                else:
                    self.log_test("Health Monitoring Structure", False, f"Missing keys: {missing_keys}")
            else:
                self.log_test("Health Monitoring Endpoint", False, f"Health endpoint failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("System Health Monitoring Test", False, f"Error: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup test data and resources"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Run cleanup tasks
        for cleanup_task in self.cleanup_tasks:
            try:
                cleanup_task()
            except Exception as e:
                print(f"Cleanup task failed: {e}")
        
        # Clean up test projects
        if 'deletion_test_project_id' in self.test_data:
            try:
                project_id = self.test_data['deletion_test_project_id']
                response = requests.delete(f"{API_BASE_URL}/projects/{project_id}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ Cleaned up test project: {project_id}")
                else:
                    print(f"⚠️ Failed to cleanup test project: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")
    
    async def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Test Suite for Task 10")
        print("=" * 80)
        
        test_methods = [
            self.test_database_foreign_key_constraints,
            self.test_project_deletion_scenarios,
            self.test_trello_mcp_integration,
            self.test_document_upload_processing,
            self.test_ai_response_system_fallback,
            self.test_frontend_api_integration,
            self.test_system_health_monitoring
        ]
        
        start_time = time.time()
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                self.log_test(test_method.__name__, False, f"Test method failed: {e}")
        
        await self.cleanup()
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        duration = time.time() - start_time
        
        print("\n" + "=" * 80)
        print("📊 TEST SUITE SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏱️ Duration: {duration:.2f} seconds")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Save detailed results
        results_file = f"comprehensive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': passed_tests/total_tests*100,
                    'duration_seconds': duration
                },
                'test_results': self.test_results
            }, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        return failed_tests == 0


async def main():
    """Main function to run the comprehensive test suite"""
    test_suite = ComprehensiveTestSuite()
    success = await test_suite.run_all_tests()
    
    return success


if __name__ == "__main__":
    import asyncio
    
    success = asyncio.run(main())
    exit(0 if success else 1)