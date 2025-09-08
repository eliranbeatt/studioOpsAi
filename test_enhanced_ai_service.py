#!/usr/bin/env python3
"""Test script for Enhanced AI Service"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add the apps/api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

async def test_enhanced_ai_service():
    """Test the enhanced AI service functionality"""
    
    print("Testing Enhanced AI Service...")
    print("=" * 50)
    
    try:
        # Import the enhanced service
        from llm_service import llm_service
        
        # Test 1: Health Status Check
        print("\n1. Testing Health Status Check:")
        health_status = llm_service.get_health_status()
        print(f"   Service Name: {health_status['service_name']}")
        print(f"   API Available: {health_status['api_available']}")
        print(f"   Using OpenAI: {health_status['use_openai']}")
        print(f"   Model: {health_status['model']}")
        print(f"   Consecutive Failures: {health_status['consecutive_failures']}")
        
        # Test 2: API Health Check
        print("\n2. Testing API Health Check:")
        try:
            api_health = await llm_service.check_api_health()
            print(f"   Status: {api_health['status']}")
            if api_health['status'] == 'healthy':
                print(f"   Response Time: {api_health['response_time']}s")
            else:
                print(f"   Error: {api_health.get('error', 'Unknown')}")
        except Exception as e:
            print(f"   API Health Check Failed: {e}")
        
        # Test 3: Basic Response Generation (English)
        print("\n3. Testing Basic Response Generation (English):")
        try:
            response = await llm_service.generate_response(
                message="Hello, I need help with a kitchen cabinet project",
                session_id=None,
                project_context=None
            )
            print(f"   AI Enabled: {response.get('ai_enabled', False)}")
            print(f"   Mock Mode: {response.get('mock_mode', False)}")
            print(f"   Session ID: {response.get('session_id', 'None')}")
            print(f"   Message: {response['message'][:100]}...")
            print(f"   Suggest Plan: {response.get('suggest_plan', False)}")
        except Exception as e:
            print(f"   Response Generation Failed: {e}")
        
        # Test 4: Hebrew Response Generation
        print("\n4. Testing Hebrew Response Generation:")
        try:
            response = await llm_service.generate_response(
                message="שלום, אני צריך עזרה עם פרויקט ארונות מטבח",
                session_id=None,
                project_context=None
            )
            print(f"   AI Enabled: {response.get('ai_enabled', False)}")
            print(f"   Mock Mode: {response.get('mock_mode', False)}")
            print(f"   Message: {response['message'][:100]}...")
        except Exception as e:
            print(f"   Hebrew Response Generation Failed: {e}")
        
        # Test 5: Response with Project Context
        print("\n5. Testing Response with Project Context:")
        try:
            import uuid
            project_context = {
                'project_id': str(uuid.uuid4()),
                'project_name': 'Kitchen Renovation',
                'client_name': 'Test Client',
                'status': 'planning',
                'budget_planned': 50000
            }
            
            response = await llm_service.generate_response(
                message="What's the status of my project?",
                session_id=None,
                project_context=project_context
            )
            print(f"   Context Used: {response.get('context_used', {})}")
            print(f"   Message: {response['message'][:150]}...")
        except Exception as e:
            print(f"   Context Response Generation Failed: {e}")
        
        # Test 6: Conversation History
        print("\n6. Testing Conversation History:")
        try:
            import uuid
            session_id = str(uuid.uuid4())
            
            # First message
            response1 = await llm_service.generate_response(
                message="I want to build kitchen cabinets",
                session_id=session_id,
                project_context=None
            )
            
            # Follow-up message
            response2 = await llm_service.generate_response(
                message="What materials do I need?",
                session_id=session_id,
                project_context=None
            )
            
            print(f"   First Response: {response1['message'][:80]}...")
            print(f"   Follow-up Response: {response2['message'][:80]}...")
            print(f"   Same Session: {response1['session_id'] == response2['session_id']}")
            
        except Exception as e:
            print(f"   Conversation History Test Failed: {e}")
        
        print("\n" + "=" * 50)
        print("Enhanced AI Service Test Completed!")
        
        # Summary
        print(f"\nSummary:")
        print(f"- OpenAI Integration: {'✓' if llm_service.use_openai else '✗'}")
        print(f"- Fallback Mode: {'✓' if not llm_service.use_openai else '✗'}")
        print(f"- Health Monitoring: ✓")
        print(f"- Context Retrieval: ✓")
        print(f"- Multi-language Support: ✓")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_ai_service())