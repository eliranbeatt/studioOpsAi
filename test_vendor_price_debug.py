#!/usr/bin/env python3
"""
Debug vendor price creation issue
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_vendor_price_debug():
    """Debug vendor price creation"""
    print("Testing Vendor Price CREATE with detailed debugging...")
    
    # First create a vendor and material
    vendor_data = {"name": "Debug Vendor for Price"}
    vendor_response = requests.post(f"{BASE_URL}/vendors/", json=vendor_data)
    if vendor_response.status_code != 201:
        print(f"❌ Failed to create vendor: {vendor_response.status_code}")
        return False
    vendor_id = vendor_response.json()['id']
    print(f"✅ Created vendor: {vendor_id}")
    
    material_data = {"name": "Debug Material for Price", "unit": "kg"}
    material_response = requests.post(f"{BASE_URL}/materials/", json=material_data)
    if material_response.status_code != 201:
        print(f"❌ Failed to create material: {material_response.status_code}")
        requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
        return False
    material_id = material_response.json()['id']
    print(f"✅ Created material: {material_id}")
    
    # Now test vendor price creation with detailed logging
    vendor_price_data = {
        "vendor_id": vendor_id,
        "material_id": material_id,
        "sku": "DEBUG-SKU-001",
        "price_nis": 125.50,
        "fetched_at": datetime.now().isoformat(),
        "source_url": "https://debug.com/price",
        "confidence": 0.9,
        "is_quote": False
    }
    
    print(f"Sending vendor price data: {json.dumps(vendor_price_data, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/vendor-prices/", json=vendor_price_data)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            vendor_price = response.json()
            print(f"✅ Vendor Price CREATE successful: {vendor_price['id']}")
            
            # Cleanup
            requests.delete(f"{BASE_URL}/vendor-prices/{vendor_price['id']}")
            requests.delete(f"{BASE_URL}/materials/{material_id}")
            requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
            return True
        else:
            print(f"❌ Vendor Price CREATE failed")
            # Cleanup
            requests.delete(f"{BASE_URL}/materials/{material_id}")
            requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during vendor price creation: {e}")
        # Cleanup
        requests.delete(f"{BASE_URL}/materials/{material_id}")
        requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
        return False

if __name__ == "__main__":
    print("🔍 Debugging Vendor Price CREATE")
    print("=" * 40)
    
    # Test health first
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print(f"❌ API not healthy: {response.status_code}")
            exit(1)
        print("✅ API is healthy")
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        exit(1)
    
    test_vendor_price_debug()