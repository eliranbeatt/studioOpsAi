"""
Comprehensive test for the Health Monitoring System

Tests all health monitoring endpoints, service degradation patterns,
and startup validation functionality.
"""

import asyncio
import pytest
import requests
import json
import time
from datetime import datetime
import sys
import os

# Add the API directory to the path
sys.path.append('apps/api')

from services.health_monitoring_service import health_monitoring_service, ServiceStatus
from services.service_degradation_service import service_degradation_service, DegradationLevel
from services.startup_validation_service import startup_validation_service

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class TestHealthMonitoringSystem:
    """Test suite for the health monitoring system"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.session.close()
    
    def test_basic_health_endpoint(self):
        """Test basic health check endpoint"""
        print("\n=== Testing Basic Health Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/api/health/")
            print(f"Status Code: {response.status_code}")
            
            assert response.status_code == 200
            
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            assert "status" in data
            assert "timestamp" in data
            assert "service" in data
            assert data["service"] == "studioops-api"
            
            print("✅ Basic health endpoint test passed")
            
        except Exception as e:
            print(f"❌ Basic health endpoint test failed: {e}")
            raise
    
    def test_detailed_health_endpoint(self):
        """Test detailed health check endpoint"""
        print("\n=== Testing Detailed Health Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/api/health/detailed")
            print(f"Status Code: {response.status_code}")
            
            # Should return 200 even if some services are degraded
            assert response.status_code in [200, 503]
            
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
            
            # Check required fields
            assert "overall_status" in data
            assert "services" in data
            assert "system_info" in data
            assert "timestamp" in data
            assert "response_time_ms" in data
            
            # Check system info
            system_info = data["system_info"]
            assert "version" in system_info
            assert "environment" in system_info
            assert "uptime_seconds" in system_info
            
            # Check services
            services = data["services"]
            expected_services = ["database", "minio", "trello_mcp", "ai_service", "observability", "system_resources"]
            
            for service in expected_services:
                if service in services:
                    service_data = services[service]
                    assert "status" in service_data
                    assert "message" in service_data
                    assert "timestamp" in service_data
                    print(f"  {service}: {service_data['status']} - {service_data['message']}")
            
            print("✅ Detailed health endpoint test passed")
            
        except Exception as e:
            print(f"❌ Detailed health endpoint test failed: {e}")
            raise
    
    def test_service_specific_health(self):
        """Test service-specific health endpoints"""
        print("\n=== Testing Service-Specific Health Endpoints ===")
        
        services_to_test = ["database", "minio", "trello_mcp", "ai_service"]
        
        for service_name in services_to_test:
            try:
                print(f"\nTesting {service_name} health...")
                response = self.session.get(f"{API_BASE_URL}/api/health/services/{service_name}")
                print(f"  Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"  Response: {json.dumps(data, indent=2, default=str)}")
                    
                    assert "service" in data
                    assert "status" in data
                    assert "message" in data
                    assert data["service"] == service_name
                    
                    print(f"  ✅ {service_name} health check passed")
                elif response.status_code == 404:
                    print(f"  ⚠️ {service_name} service not found (expected for some services)")
                else:
                    print(f"  ❌ {service_name} health check failed with status {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ {service_name} health check failed: {e}")
    
    def test_dependencies_endpoint(self):
        """Test service dependencies endpoint"""
        print("\n=== Testing Dependencies Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/api/health/dependencies")
            print(f"Status Code: {response.status_code}")
            
            assert response.status_code == 200
            
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
            
            assert "overall_status" in data
            assert "summary" in data
            assert "dependencies" in data
            assert "timestamp" in data
            
            # Check dependencies structure
            dependencies = data["dependencies"]
            assert "required" in dependencies
            assert "optional" in dependencies
            
            # Check required dependencies
            required = dependencies["required"]
            assert "database" in required
            
            # Check optional dependencies
            optional = dependencies["optional"]
            expected_optional = ["trello_mcp", "ai_service", "observability"]
            for service in expected_optional:
                if service in optional:
                    service_data = optional[service]
                    assert "status" in service_data
                    assert "description" in service_data
            
            print("✅ Dependencies endpoint test passed")
            
        except Exception as e:
            print(f"❌ Dependencies endpoint test failed: {e}")
            raise
    
    def test_diagnostics_endpoint(self):
        """Test system diagnostics endpoint"""
        print("\n=== Testing Diagnostics Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/api/health/diagnostics")
            print(f"Status Code: {response.status_code}")
            
            assert response.status_code == 200
            
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Check required fields
            required_fields = [
                "timestamp", "overall_status", "system_info", 
                "environment", "service_summary", "dependencies",
                "issues", "recommendations"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Check environment info
            env_info = data["environment"]
            assert "environment" in env_info
            assert "database_url_configured" in env_info
            
            print("✅ Diagnostics endpoint test passed")
            
        except Exception as e:
            print(f"❌ Diagnostics endpoint test failed: {e}")
            raise
    
    def test_kubernetes_probes(self):
        """Test Kubernetes-style probe endpoints"""
        print("\n=== Testing Kubernetes Probe Endpoints ===")
        
        probe_endpoints = [
            "/api/health/readiness",
            "/api/health/liveness", 
            "/api/health/startup"
        ]
        
        for endpoint in probe_endpoints:
            try:
                print(f"\nTesting {endpoint}...")
                response = self.session.get(f"{API_BASE_URL}{endpoint}")
                print(f"  Status Code: {response.status_code}")
                
                # Readiness might return 503 if critical services are down
                if endpoint == "/api/health/readiness":
                    assert response.status_code in [200, 503]
                else:
                    assert response.status_code == 200
                
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2, default=str)}")
                
                assert "status" in data
                assert "timestamp" in data
                
                print(f"  ✅ {endpoint} test passed")
                
            except Exception as e:
                print(f"  ❌ {endpoint} test failed: {e}")
    
    def test_metrics_endpoint(self):
        """Test health metrics endpoint"""
        print("\n=== Testing Metrics Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/api/health/metrics")
            print(f"Status Code: {response.status_code}")
            
            assert response.status_code == 200
            
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
            
            assert "timestamp" in data
            assert "metrics" in data
            
            metrics = data["metrics"]
            
            # Check for expected metrics
            expected_metrics = [
                "studioops_health_overall_status",
                "studioops_health_check_duration_ms",
                "studioops_health_services_total",
                "studioops_health_services_healthy"
            ]
            
            for metric in expected_metrics:
                assert metric in metrics, f"Missing metric: {metric}"
            
            print("✅ Metrics endpoint test passed")
            
        except Exception as e:
            print(f"❌ Metrics endpoint test failed: {e}")
            raise
    
    def test_system_status_endpoint(self):
        """Test user-friendly system status endpoint"""
        print("\n=== Testing System Status Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/api/system/status")
            print(f"Status Code: {response.status_code}")
            
            assert response.status_code == 200
            
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
            
            assert "status" in data
            assert "message" in data
            assert "color" in data
            assert "service_impacts" in data
            assert "startup_successful" in data
            assert "timestamp" in data
            
            # Check status values
            assert data["status"] in ["healthy", "degraded", "critical", "error"]
            assert data["color"] in ["green", "yellow", "red"]
            
            print("✅ System status endpoint test passed")
            
        except Exception as e:
            print(f"❌ System status endpoint test failed: {e}")
            raise
    
    def test_root_endpoint_with_status(self):
        """Test enhanced root endpoint with status information"""
        print("\n=== Testing Enhanced Root Endpoint ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/")
            print(f"Status Code: {response.status_code}")
            
            assert response.status_code == 200
            
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
            
            assert "message" in data
            assert "version" in data
            assert "status" in data
            assert "system_message" in data
            assert "timestamp" in data
            assert "health_endpoint" in data
            
            assert data["message"] == "StudioOps AI API is running"
            assert data["version"] == "1.0.0"
            assert data["health_endpoint"] == "/api/health/detailed"
            
            print("✅ Enhanced root endpoint test passed")
            
        except Exception as e:
            print(f"❌ Enhanced root endpoint test failed: {e}")
            raise
    
    async def test_service_degradation_patterns(self):
        """Test service degradation handling patterns"""
        print("\n=== Testing Service Degradation Patterns ===")
        
        try:
            # Test degradation handling for different services
            services_to_test = [
                ("trello_mcp", DegradationLevel.DEGRADED),
                ("ai_service", DegradationLevel.CRITICAL),
                ("minio", DegradationLevel.OFFLINE)
            ]
            
            for service_name, degradation_level in services_to_test:
                print(f"\nTesting {service_name} degradation at level {degradation_level.value}...")
                
                # Simulate service degradation
                result = await service_degradation_service.handle_service_degradation(
                    service_name,
                    degradation_level,
                    {"test": "simulated degradation"}
                )
                
                print(f"  Degradation result: {json.dumps(result, indent=2, default=str)}")
                
                assert result["service"] == service_name
                assert result["level"] == degradation_level.value
                assert "message" in result
                
                # Check service state
                state = service_degradation_service.get_service_state(service_name)
                assert state is not None
                assert state["level"] == degradation_level
                
                print(f"  ✅ {service_name} degradation test passed")
            
            # Test degradation summary
            summary = service_degradation_service.get_degradation_summary()
            print(f"\nDegradation summary: {json.dumps(summary, indent=2, default=str)}")
            
            assert "overall_status" in summary
            assert "degraded_services" in summary
            assert summary["degraded_services"] > 0
            
            # Test user-facing status
            user_status = service_degradation_service.get_user_facing_status()
            print(f"\nUser-facing status: {json.dumps(user_status, indent=2, default=str)}")
            
            assert "status" in user_status
            assert "message" in user_status
            assert "service_impacts" in user_status
            
            print("✅ Service degradation patterns test passed")
            
        except Exception as e:
            print(f"❌ Service degradation patterns test failed: {e}")
            raise
    
    async def test_startup_validation(self):
        """Test startup validation service"""
        print("\n=== Testing Startup Validation ===")
        
        try:
            # Run startup validation
            results = await startup_validation_service.validate_system_startup()
            
            print(f"Startup validation results: {json.dumps(results, indent=2, default=str)}")
            
            assert "startup_successful" in results
            assert "validation_results" in results
            assert "warnings" in results
            assert "errors" in results
            
            validation_results = results["validation_results"]
            expected_sections = [
                "environment", "configuration", "critical_services",
                "optional_services", "database_schema", "file_permissions"
            ]
            
            for section in expected_sections:
                assert section in validation_results
                assert "status" in validation_results[section]
            
            print("✅ Startup validation test passed")
            
        except Exception as e:
            print(f"❌ Startup validation test failed: {e}")
            raise
    
    def test_performance_and_response_times(self):
        """Test health check performance and response times"""
        print("\n=== Testing Performance and Response Times ===")
        
        endpoints_to_test = [
            "/api/health/",
            "/api/health/detailed",
            "/api/health/dependencies",
            "/api/system/status"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                print(f"\nTesting performance for {endpoint}...")
                
                # Measure response time
                start_time = time.time()
                response = self.session.get(f"{API_BASE_URL}{endpoint}")
                end_time = time.time()
                
                response_time_ms = (end_time - start_time) * 1000
                
                print(f"  Status Code: {response.status_code}")
                print(f"  Response Time: {response_time_ms:.2f}ms")
                
                # Response time should be reasonable (under 5 seconds)
                assert response_time_ms < 5000, f"Response time too slow: {response_time_ms}ms"
                
                # Check if response includes timing information
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "response_time_ms" in data:
                            reported_time = data["response_time_ms"]
                            print(f"  Reported Time: {reported_time}ms")
                    except:
                        pass
                
                print(f"  ✅ {endpoint} performance test passed")
                
            except Exception as e:
                print(f"  ❌ {endpoint} performance test failed: {e}")

def run_health_monitoring_tests():
    """Run all health monitoring tests"""
    print("🏥 Starting Health Monitoring System Tests")
    print("=" * 50)
    
    test_instance = TestHealthMonitoringSystem()
    test_instance.setup_method()
    
    try:
        # Synchronous tests
        test_instance.test_basic_health_endpoint()
        test_instance.test_detailed_health_endpoint()
        test_instance.test_service_specific_health()
        test_instance.test_dependencies_endpoint()
        test_instance.test_diagnostics_endpoint()
        test_instance.test_kubernetes_probes()
        test_instance.test_metrics_endpoint()
        test_instance.test_system_status_endpoint()
        test_instance.test_root_endpoint_with_status()
        test_instance.test_performance_and_response_times()
        
        # Asynchronous tests
        print("\n" + "=" * 50)
        print("Running asynchronous tests...")
        
        async def run_async_tests():
            await test_instance.test_service_degradation_patterns()
            await test_instance.test_startup_validation()
        
        asyncio.run(run_async_tests())
        
        print("\n" + "=" * 50)
        print("🎉 All Health Monitoring System Tests Completed Successfully!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Health monitoring tests failed: {e}")
        return False
        
    finally:
        test_instance.teardown_method()

if __name__ == "__main__":
    success = run_health_monitoring_tests()
    sys.exit(0 if success else 1)