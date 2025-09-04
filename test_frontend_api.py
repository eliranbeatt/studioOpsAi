#!/usr/bin/env python3

import requests
import time

def test_frontend_api():
    """Test if the frontend API endpoints are working"""
    
    # Test the projects endpoint
    try:
        print("Testing /api/projects endpoint...")
        response = requests.get("http://localhost:3008/api/projects", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Frontend API is working!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Frontend API returned: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Frontend API not available")
        return False
    except requests.exceptions.Timeout:
        print("Frontend API request timed out")
        return False
    except Exception as e:
        print(f"Error testing frontend API: {e}")
        return False

if __name__ == "__main__":
    test_frontend_api()