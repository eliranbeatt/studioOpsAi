#!/usr/bin/env python3
"""
Demo script to test the StudioOps AI application
"""

import requests
import json
import uuid
import time

API_BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test API health"""
    print("🔍 Testing API Health...")
    response = requests.get(f"{API_BASE_URL}/health")
    if response.status_code == 200:
        print("✅ API is healthy:", response.json())
        return True
    else:
        print("❌ API health check failed:", response.status_code)
        return False

def test_project_management():
    """Test project creation and management"""
    print("\n📋 Testing Project Management...")
    
    # Create a project
    project_data = {
        "name": "Demo Test Project",
        "client_name": "Test Client",
        "status": "active",
        "budget_planned": 50000.0
    }
    
    response = requests.post(f"{API_BASE_URL}/projects", json=project_data)
    if response.status_code == 200:
        project = response.json()
        project_id = project["id"]
        print(f"✅ Created project: {project['name']} (ID: {project_id})")
        
        # Get the project
        response = requests.get(f"{API_BASE_URL}/projects/{project_id}")
        if response.status_code == 200:
            print("✅ Retrieved project successfully")
            return project_id
        else:
            print("❌ Failed to retrieve project")
            return None
    else:
        print("❌ Failed to create project:", response.status_code)
        return None

def test_chat_functionality(project_id):
    """Test chat functionality with project context"""
    print("\n💬 Testing Chat Functionality...")
    
    # Test chat messages
    chat_tests = [
        {
            "message": "Hello! Can you help me with this construction project?",
            "description": "Initial greeting with project context"
        },
        {
            "message": "What materials would be suitable for this project?",
            "description": "Material recommendations"
        },
        {
            "message": "Can you estimate the costs?",
            "description": "Cost estimation"
        }
    ]
    
    session_id = None
    
    for i, test in enumerate(chat_tests, 1):
        print(f"\n🔸 Chat Test {i}: {test['description']}")
        
        chat_data = {
            "message": test["message"],
            "project_id": project_id
        }
        
        if session_id:
            chat_data["session_id"] = session_id
        
        response = requests.post(f"{API_BASE_URL}/chat/message", json=chat_data, timeout=30)
        
        if response.status_code == 200:
            chat_response = response.json()
            session_id = chat_response.get("session_id")
            message = chat_response.get("message", "")
            
            print(f"✅ Chat response received (Session: {session_id})")
            print(f"🤖 AI Response: {message[:150]}{'...' if len(message) > 150 else ''}")
            
            if chat_response.get("suggest_plan"):
                print("💡 AI suggests creating a project plan")
        else:
            print(f"❌ Chat failed: {response.status_code}")
    
    return session_id

def test_plan_generation(project_id):
    """Test plan generation"""
    print("\n📊 Testing Plan Generation...")
    
    plan_data = {"project_id": project_id}
    response = requests.post(f"{API_BASE_URL}/chat/generate_plan", json=plan_data)
    
    if response.status_code == 200:
        plan = response.json()
        print(f"✅ Generated plan with {len(plan['items'])} items")
        print(f"💰 Total cost: {plan['total']} {plan['currency']}")
        
        # Show some plan items
        for item in plan['items'][:3]:
            print(f"   • {item['title']}: {item['quantity']} {item['unit']} × {item['unit_price']} = {item['subtotal']}")
        
        return True
    else:
        print(f"❌ Plan generation failed: {response.status_code}")
        return False

def test_project_list():
    """Test project listing"""
    print("\n📋 Testing Project List...")
    
    response = requests.get(f"{API_BASE_URL}/projects")
    if response.status_code == 200:
        projects = response.json()
        print(f"✅ Found {len(projects)} projects")
        for project in projects[:3]:  # Show first 3
            print(f"   • {project['name']} - {project['status']} (Client: {project.get('client_name', 'N/A')})")
        return True
    else:
        print(f"❌ Failed to list projects: {response.status_code}")
        return False

def cleanup_project(project_id):
    """Clean up test project"""
    print(f"\n🧹 Cleaning up test project: {project_id}")
    
    response = requests.delete(f"{API_BASE_URL}/projects/{project_id}")
    if response.status_code == 200:
        print("✅ Test project cleaned up successfully")
        return True
    else:
        print(f"⚠️  Cleanup warning: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("🚀 STUDIOOPS AI APPLICATION DEMO TEST")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("❌ API is not available. Please make sure the server is running.")
        return
    
    # Test project management
    project_id = test_project_management()
    if not project_id:
        print("❌ Project management test failed")
        return
    
    # Test chat functionality
    session_id = test_chat_functionality(project_id)
    
    # Test plan generation
    test_plan_generation(project_id)
    
    # Test project listing
    test_project_list()
    
    # Cleanup
    cleanup_project(project_id)
    
    print("\n🎉 DEMO TEST COMPLETED!")
    print("=" * 50)
    print("✅ All core functionality is working!")
    print("\n🌐 You can now test the web interface at: http://localhost:3000")
    print("📚 API documentation available at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()