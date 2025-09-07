#!/usr/bin/env python3
"""
Debug session ID generation
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_session_id_generation():
    """Test session ID generation"""
    
    print("🔍 Debugging Session ID Generation")
    print("=" * 40)
    
    # Test 1: Send chat message without session_id
    chat_message = {
        "message": "Hello, this is a test message"
    }
    
    print("Sending chat message without session_id...")
    response = requests.post(f"{API_BASE_URL}/chat/message", json=chat_message)
    
    if response.status_code == 200:
        chat_response = response.json()
        session_id = chat_response.get('session_id')
        print(f"✅ Response received")
        print(f"Session ID: {session_id}")
        print(f"Session ID type: {type(session_id)}")
        print(f"Session ID length: {len(session_id)}")
        print(f"Session ID format: {'UUID' if len(session_id) == 36 and session_id.count('-') == 4 else 'Other'}")
        
        # Test 2: Send follow-up with the same session_id
        follow_up = {
            "message": "This is a follow-up message",
            "session_id": session_id
        }
        
        print(f"\nSending follow-up with session_id: {session_id}")
        response2 = requests.post(f"{API_BASE_URL}/chat/message", json=follow_up)
        
        if response2.status_code == 200:
            print("✅ Follow-up successful")
            chat_response2 = response2.json()
            session_id2 = chat_response2.get('session_id')
            print(f"Follow-up session ID: {session_id2}")
            print(f"Session IDs match: {session_id == session_id2}")
        else:
            print(f"❌ Follow-up failed: {response2.status_code}")
            print(f"Error: {response2.text}")
            
    else:
        print(f"❌ Initial message failed: {response.status_code}")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_session_id_generation()