#!/usr/bin/env python3
"""
Simple test to verify API connection
"""

import requests
import time

def test_api_connection():
    """Test if the API is accessible"""
    
    print("🔌 Testing API Connection")
    print("=" * 30)
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

if __name__ == "__main__":
    # Wait a moment for server to start
    time.sleep(2)
    test_api_connection()