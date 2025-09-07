#!/usr/bin/env python3
"""
Test chat-project linking functionality
"""

import requests
import asyncio
import asyncpg
import os
import uuid
import json

API_BASE_URL = "http://localhost:8000"
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')

async def test_chat_project_linking():
    """Test that chat messages are properly linked to projects"""
    
    print("🧪 Testing Chat-Project Linking")
    print("=" * 40)
    
    # Step 1: Create a test project
    test_project = {
        "name": "Chat Link Test Project",
        "client_name": "Test Client",
        "status": "active",
        "description": "Test project for chat linking"
    }
    
    response = requests.post(f"{API_BASE_URL}/projects", json=test_project)
    if response.status_code != 200:
        print(f"❌ Failed to create test project: {response.status_code}")
        return False
    
    project_data = response.json()
    project_id = project_data['id']
    print(f"✅ Created test project: {project_id}")
    
    # Step 2: Send chat message with project context
    chat_message = {
        "message": "What materials do I need for this construction project?",
        "project_id": project_id
    }
    
    response = requests.post(f"{API_BASE_URL}/chat/message", json=chat_message)
    if response.status_code != 200:
        print(f"❌ Chat message failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    chat_response = response.json()
    session_id = chat_response.get('session_id')
    print(f"✅ Chat message sent, session: {session_id}")
    
    # Step 3: Send follow-up message to same session
    follow_up = {
        "message": "Can you provide cost estimates?",
        "project_id": project_id,
        "session_id": session_id
    }
    
    response = requests.post(f"{API_BASE_URL}/chat/message", json=follow_up)
    if response.status_code != 200:
        print(f"❌ Follow-up message failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    print("✅ Follow-up message sent")
    
    # Step 4: Verify database linkage
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Check if chat session exists and is linked to project
        session_data = await conn.fetchrow("""
            SELECT id, project_id, title, context 
            FROM chat_sessions 
            WHERE id = $1
        """, session_id)
        
        if not session_data:
            print(f"❌ Chat session not found in database: {session_id}")
            return False
        
        if str(session_data['project_id']) != project_id:
            print(f"❌ Session project mismatch: {session_data['project_id']} != {project_id}")
            return False
        
        print(f"✅ Chat session properly linked to project")
        
        # Check if messages exist and are linked
        messages = await conn.fetch("""
            SELECT cm.message, cm.response, cm.is_user, cm.project_context
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.id
            WHERE cs.project_id = $1
            ORDER BY cm.created_at
        """, uuid.UUID(project_id))
        
        if not messages:
            print("❌ No chat messages found linked to project")
            return False
        
        print(f"✅ Found {len(messages)} chat messages linked to project")
        
        # Verify message content
        user_messages = [msg for msg in messages if msg['is_user']]
        ai_messages = [msg for msg in messages if not msg['is_user']]
        
        print(f"   - User messages: {len(user_messages)}")
        print(f"   - AI messages: {len(ai_messages)}")
        
        # Check project context in messages
        context_messages = [msg for msg in messages if msg['project_context'] and 'project_id' in msg['project_context']]
        print(f"   - Messages with project context: {len(context_messages)}")
        
        if len(context_messages) == 0:
            print("⚠️  No messages have project context")
        
        return True
        
    finally:
        await conn.close()
        
        # Cleanup: Delete test project
        requests.delete(f"{API_BASE_URL}/projects/{project_id}")
        print("✅ Cleaned up test project")

async def test_timestamp_consistency():
    """Test timestamp format consistency between API and DB"""
    
    print("\n🕐 Testing Timestamp Consistency")
    print("=" * 40)
    
    # Create test project
    test_project = {
        "name": "Timestamp Test Project",
        "client_name": "Test Client",
        "status": "active"
    }
    
    response = requests.post(f"{API_BASE_URL}/projects", json=test_project)
    if response.status_code != 200:
        print(f"❌ Failed to create test project: {response.status_code}")
        return False
    
    project_data = response.json()
    project_id = project_data['id']
    
    # Get project from API
    api_response = requests.get(f"{API_BASE_URL}/projects")
    if api_response.status_code != 200:
        print(f"❌ Failed to get projects from API: {api_response.status_code}")
        return False
    
    api_projects = api_response.json()
    api_project = next((p for p in api_projects if p['id'] == project_id), None)
    
    if not api_project:
        print("❌ Test project not found in API response")
        return False
    
    # Get same project from database
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        db_project = await conn.fetchrow("""
            SELECT id, name, client_name, status, created_at, updated_at
            FROM projects WHERE id = $1
        """, uuid.UUID(project_id))
        
        if not db_project:
            print("❌ Test project not found in database")
            return False
        
        # Compare timestamp formats
        api_created = api_project['created_at']
        db_created = db_project['created_at'].isoformat()
        
        api_updated = api_project['updated_at']
        db_updated = db_project['updated_at'].isoformat() if db_project['updated_at'] else None
        
        print(f"API created_at: {api_created}")
        print(f"DB created_at:  {db_created}")
        
        if api_updated and db_updated:
            print(f"API updated_at: {api_updated}")
            print(f"DB updated_at:  {db_updated}")
        
        # Check if formats match
        created_match = api_created == db_created
        updated_match = (api_updated == db_updated) if (api_updated and db_updated) else True
        
        if created_match and updated_match:
            print("✅ Timestamp formats are consistent")
            return True
        else:
            print("❌ Timestamp formats are inconsistent")
            return False
        
    finally:
        await conn.close()
        
        # Cleanup
        requests.delete(f"{API_BASE_URL}/projects/{project_id}")
        print("✅ Cleaned up test project")

async def main():
    """Run all tests"""
    print("🚀 COMPREHENSIVE CHAT-PROJECT LINKING TEST")
    print("=" * 50)
    
    try:
        # Test 1: Chat-Project Linking
        linking_success = await test_chat_project_linking()
        
        # Test 2: Timestamp Consistency
        timestamp_success = await test_timestamp_consistency()
        
        print("\n📊 TEST RESULTS")
        print("=" * 20)
        print(f"Chat-Project Linking: {'✅ PASS' if linking_success else '❌ FAIL'}")
        print(f"Timestamp Consistency: {'✅ PASS' if timestamp_success else '❌ FAIL'}")
        
        if linking_success and timestamp_success:
            print("\n🎉 ALL TESTS PASSED!")
            return True
        else:
            print("\n⚠️  SOME TESTS FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)