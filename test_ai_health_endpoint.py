#!/usr/bin/env python3
"""Test script for AI Health Monitoring Endpoint"""

import asyncio
import os
import sys
import json
import requests
import time

async def test_ai_health_endpoint():
    """Test the AI health monitoring endpoint"""
    
    print("Testing AI Health Monitoring Endpoint...")
    print("=" * 50)
    
    # Test the health endpoint
    base_url = "http://localhost:8000"  # Adjust if your API runs on a different port
    health_url = f"{base_url}/chat/health"
    
    try:
        print("\n1. Testing Health Endpoint Availability:")
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✓ Endpoint Available")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            
            # Service Health
            service_health = health_data.get('service_health', {})
            print(f"\n   Service Health:")
            print(f"   - Service Name: {service_health.get('service_name', 'Unknown')}")
            print(f"   - API Available: {service_health.get('api_available', False)}")
            print(f"   - Using OpenAI: {service_health.get('use_openai', False)}")
            print(f"   - Model: {service_health.get('model', 'Unknown')}")
            print(f"   - Consecutive Failures: {service_health.get('consecutive_failures', 0)}")
            print(f"   - Avg Response Time: {service_health.get('avg_response_time', 'N/A')}s")
            print(f"   - Cache Size: {service_health.get('cache_size', 0)}")
            
            # API Health
            api_health = health_data.get('api_health', {})
            print(f"\n   API Health:")
            print(f"   - Status: {api_health.get('status', 'unknown')}")
            if api_health.get('status') == 'healthy':
                print(f"   - Response Time: {api_health.get('response_time', 'N/A')}s")
                print(f"   - Model: {api_health.get('model', 'Unknown')}")
            else:
                print(f"   - Error: {api_health.get('error', 'Unknown')}")
                print(f"   - Consecutive Failures: {api_health.get('consecutive_failures', 0)}")
            
        else:
            print(f"   ✗ Endpoint returned status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Could not connect to API server at {base_url}")
        print(f"   Make sure the API server is running with: python -m uvicorn main:app --reload")
        
    except requests.exceptions.Timeout:
        print(f"   ✗ Request timed out")
        
    except Exception as e:
        print(f"   ✗ Error testing health endpoint: {e}")
    
    print("\n" + "=" * 50)
    print("AI Health Monitoring Endpoint Test Completed!")

if __name__ == "__main__":
    asyncio.run(test_ai_health_endpoint())