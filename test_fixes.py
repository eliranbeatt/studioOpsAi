#!/usr/bin/env python3
"""
Test the specific fixes for Material UPDATE, Vendor Price CREATE, and Purchase CREATE
"""

import requests
import json
from datetime import datetime
import uuid

BASE_URL = "http://localhost:8000"

def test_material_update():
    """Test material update with partial data"""
    print("Testing Material UPDATE...")
    
    # First create a material
    material_data = {
        "name": "Test Material for Update",
        "unit": "kg",
        "category": "test",
        "typical_waste_pct": 5.0
    }
    
    response = requests.post(f"{BASE_URL}/materials/", json=material_data)
    if response.status_code != 201:
        print(f"❌ Failed to create material: {response.status_code} - {response.text}")
        return False
    
    material = response.json()
    material_id = material['id']
    print(f"✅ Created material: {material_id}")
    
    # Now test partial update (without unit field)
    update_data = {
        "name": "Updated Test Material",
        "typical_waste_pct": 7.5,
        "category": "updated-test-materials"
    }
    
    response = requests.put(f"{BASE_URL}/materials/{material_id}", json=update_data)
    if response.status_code == 200:
        updated_material = response.json()
        print(f"✅ Material UPDATE successful: {updated_material['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/materials/{material_id}")
        return True
    else:
        print(f"❌ Material UPDATE failed: {response.status_code} - {response.text}")
        # Cleanup
        requests.delete(f"{BASE_URL}/materials/{material_id}")
        return False

def test_vendor_price_create():
    """Test vendor price creation with fetched_at"""
    print("\nTesting Vendor Price CREATE...")
    
    # First create a vendor and material
    vendor_data = {"name": "Test Vendor for Price"}
    vendor_response = requests.post(f"{BASE_URL}/vendors/", json=vendor_data)
    if vendor_response.status_code != 201:
        print(f"❌ Failed to create vendor: {vendor_response.status_code}")
        return False
    vendor_id = vendor_response.json()['id']
    
    material_data = {"name": "Test Material for Price", "unit": "kg"}
    material_response = requests.post(f"{BASE_URL}/materials/", json=material_data)
    if material_response.status_code != 201:
        print(f"❌ Failed to create material: {material_response.status_code}")
        requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
        return False
    material_id = material_response.json()['id']
    
    # Now test vendor price creation
    vendor_price_data = {
        "vendor_id": vendor_id,
        "material_id": material_id,
        "sku": "TEST-SKU-001",
        "price_nis": 125.50,
        "fetched_at": datetime.now().isoformat(),
        "source_url": "https://test.com/price",
        "confidence": 0.9,
        "is_quote": False
    }
    
    response = requests.post(f"{BASE_URL}/vendor-prices/", json=vendor_price_data)
    if response.status_code == 200:
        vendor_price = response.json()
        print(f"✅ Vendor Price CREATE successful: {vendor_price['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/vendor-prices/{vendor_price['id']}")
        requests.delete(f"{BASE_URL}/materials/{material_id}")
        requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
        return True
    else:
        print(f"❌ Vendor Price CREATE failed: {response.status_code} - {response.text}")
        # Cleanup
        requests.delete(f"{BASE_URL}/materials/{material_id}")
        requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
        return False

def test_purchase_create():
    """Test purchase creation with all fields"""
    print("\nTesting Purchase CREATE...")
    
    # First create a vendor and material
    vendor_data = {"name": "Test Vendor for Purchase"}
    vendor_response = requests.post(f"{BASE_URL}/vendors/", json=vendor_data)
    if vendor_response.status_code != 201:
        print(f"❌ Failed to create vendor: {vendor_response.status_code}")
        return False
    vendor_id = vendor_response.json()['id']
    
    material_data = {"name": "Test Material for Purchase", "unit": "kg"}
    material_response = requests.post(f"{BASE_URL}/materials/", json=material_data)
    if material_response.status_code != 201:
        print(f"❌ Failed to create material: {material_response.status_code}")
        requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
        return False
    material_id = material_response.json()['id']
    
    # Now test purchase creation
    purchase_data = {
        "vendor_id": vendor_id,
        "material_id": material_id,
        "sku": "PURCHASE-SKU-001",
        "qty": 10.5,
        "unit": "kg",
        "unit_price_nis": 125.50,
        "total_nis": 1317.75,
        "currency": "NIS",
        "tax_vat_pct": 17.0,
        "occurred_at": "2024-01-15",
        "receipt_path": "/receipts/test-receipt.pdf"
    }
    
    response = requests.post(f"{BASE_URL}/purchases/", json=purchase_data)
    if response.status_code == 200:
        purchase = response.json()
        print(f"✅ Purchase CREATE successful: {purchase['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/purchases/{purchase['id']}")
        requests.delete(f"{BASE_URL}/materials/{material_id}")
        requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
        return True
    else:
        print(f"❌ Purchase CREATE failed: {response.status_code} - {response.text}")
        # Cleanup
        requests.delete(f"{BASE_URL}/materials/{material_id}")
        requests.delete(f"{BASE_URL}/vendors/{vendor_id}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Specific CRUD Fixes")
    print("=" * 40)
    
    # Wait for API to be ready
    import time
    time.sleep(5)
    
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
    
    results = []
    results.append(test_material_update())
    results.append(test_vendor_price_create())
    results.append(test_purchase_create())
    
    print("\n" + "=" * 40)
    print("📊 RESULTS")
    print("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All fixes working!")
    else:
        print("⚠️  Some fixes still need work")