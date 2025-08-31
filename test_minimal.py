#!/usr/bin/env python3
"""Minimal test for API connectivity"""

import requests
import time

def test_connectivity():
    print("Testing connectivity to localhost:8002...")
    
    # Try multiple times with delays
    for i in range(5):
        try:
            response = requests.get('http://127.0.0.1:8002/health', timeout=2)
            print(f"Success! Status: {response.status_code}, Response: {response.text}")
            return True
        except Exception as e:
            print(f"Attempt {i+1}: {e}")
            time.sleep(1)
    
    print("All connection attempts failed")
    return False

if __name__ == "__main__":
    test_connectivity()