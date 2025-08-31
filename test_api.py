#!/usr/bin/env python3
"""Test script for the API"""

import requests
import time

def test_api():
    print("Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:8002/health', timeout=5)
        print(f"Health endpoint: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Test root endpoint
    try:
        response = requests.get('http://localhost:8002/', timeout=5)
        print(f"Root endpoint: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Root endpoint error: {e}")
    
    # Test chat message
    try:
        response = requests.post(
            'http://localhost:8002/chat/message', 
            json={'message': 'hello'},
            timeout=5
        )
        print(f"Chat endpoint: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Chat endpoint error: {e}")
    
    # Test plan generation
    try:
        response = requests.post(
            'http://localhost:8002/chat/generate_plan', 
            json={
                'project_name': 'Test Project',
                'project_description': 'Build a cabinet with drawers'
            },
            timeout=10
        )
        print(f"Plan generation: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Plan generation error: {e}")

if __name__ == "__main__":
    test_api()