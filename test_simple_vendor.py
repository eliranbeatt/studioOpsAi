#!/usr/bin/env python3
"""
Simple vendor test that bypasses Pydantic serialization
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_simple_vendor_get():
    """Test getting vendors with raw response"""
    try:
        response = requests.get(f"{BASE_URL}/vendors/")
        print(f"GET /vendors/ - Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Raw response: {response.text[:500]}...")
        
        if response.status_code == 500:
            # Try to get more error details
            print("Checking if it's a serialization issue...")
            
            # Try a different endpoint that we know works
            health_response = requests.get(f"{BASE_URL}/health")
            print(f"Health check: {health_response.status_code} - {health_response.json()}")
            
            # Try projects endpoint that works
            projects_response = requests.get(f"{BASE_URL}/projects/")
            print(f"Projects: {projects_response.status_code}")
            if projects_response.status_code == 200:
                projects = projects_response.json()
                print(f"Projects count: {len(projects)}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    test_simple_vendor_get()