#!/usr/bin/env python3
"""
Debug vendor creation issue
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_vendor_creation():
    vendor_data = {
        "name": "Test Vendor Ltd",
        "contact": {"email": "test@vendor.com", "phone": "+972-50-1234567"},
        "url": "https://testvendor.com",
        "rating": 4,
        "notes": "Test vendor for debugging"
    }
    
    print("Testing vendor creation...")
    print(f"Data: {json.dumps(vendor_data, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/vendors/", json=vendor_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 201:
            vendor = response.json()
            print(f"✅ Success! Created vendor: {vendor}")
            return vendor
        else:
            print(f"❌ Failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_material_creation():
    material_data = {
        "name": "Test Material",
        "spec": "High-grade test material specification",
        "unit": "kg",
        "category": "test-materials",
        "typical_waste_pct": 5.5,
        "notes": "Test material for debugging"
    }
    
    print("\nTesting material creation...")
    print(f"Data: {json.dumps(material_data, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/materials/", json=material_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 201:
            material = response.json()
            print(f"✅ Success! Created material: {material}")
            return material
        else:
            print(f"❌ Failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_get_vendors():
    print("\nTesting get all vendors...")
    try:
        response = requests.get(f"{BASE_URL}/vendors/")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            vendors = response.json()
            print(f"✅ Success! Found {len(vendors)} vendors")
            return vendors
        else:
            print(f"❌ Failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Debugging Vendor and Material API Issues")
    print("=" * 50)
    
    # Test health first
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health Check Failed: {e}")
    
    # Test getting existing vendors
    test_get_vendors()
    
    # Test creating vendor
    vendor = test_vendor_creation()
    
    # Test creating material
    material = test_material_creation()