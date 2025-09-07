#!/usr/bin/env python3
"""
Detailed vendor testing to debug 500 errors
"""

import requests
import json
import traceback

BASE_URL = "http://localhost:8000"

def test_vendor_get():
    """Test getting vendors first"""
    try:
        response = requests.get(f"{BASE_URL}/vendors/")
        print(f"GET /vendors/ - Status: {response.status_code}")
        if response.status_code == 200:
            vendors = response.json()
            print(f"Found {len(vendors)} vendors")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_vendor_post_minimal():
    """Test posting minimal vendor data"""
    vendor_data = {"name": "Minimal Vendor"}
    
    try:
        response = requests.post(f"{BASE_URL}/vendors/", json=vendor_data)
        print(f"POST /vendors/ (minimal) - Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Exception: {e}")
        traceback.print_exc()
        return None

def test_vendor_post_full():
    """Test posting full vendor data"""
    vendor_data = {
        "name": "Full Test Vendor",
        "contact": {"email": "test@example.com", "phone": "123-456-7890"},
        "url": "https://example.com",
        "rating": 4,
        "notes": "Test vendor"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/vendors/", json=vendor_data)
        print(f"POST /vendors/ (full) - Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Exception: {e}")
        traceback.print_exc()
        return None

def main():
    print("🔍 Detailed Vendor Testing")
    print("=" * 40)
    
    # Test GET first
    if test_vendor_get():
        print("✅ GET vendors works")
    else:
        print("❌ GET vendors failed")
    
    print()
    
    # Test POST minimal
    vendor1 = test_vendor_post_minimal()
    if vendor1:
        print("✅ POST minimal vendor works")
    else:
        print("❌ POST minimal vendor failed")
    
    print()
    
    # Test POST full
    vendor2 = test_vendor_post_full()
    if vendor2:
        print("✅ POST full vendor works")
    else:
        print("❌ POST full vendor failed")

if __name__ == "__main__":
    main()