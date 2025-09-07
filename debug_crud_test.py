#!/usr/bin/env python3
"""
Debug CRUD operations to identify specific issues
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Test basic API connection"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def test_vendor_creation():
    """Test vendor creation with minimal data"""
    print("\n=== Testing Vendor Creation ===")
    
    # Test with minimal required fields
    vendor_data = {
        "name": "Debug Test Vendor",
        "unit": "piece"  # This might be the issue - wrong field
    }
    
    try:
        response = requests.post(f"{BASE_URL}/vendors/", json=vendor_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 201:
            # Try with correct schema
            vendor_data_correct = {
                "name": "Debug Test Vendor",
                "contact": {"email": "test@example.com"},
                "rating": 4
            }
            
            print("\nTrying with correct schema...")
            response2 = requests.post(f"{BASE_URL}/vendors/", json=vendor_data_correct)
            print(f"Status: {response2.status_code}")
            print(f"Response: {response2.text}")
            
            if response2.status_code == 201:
                return response2.json()
        else:
            return response.json()
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

def test_material_creation():
    """Test material creation with minimal data"""
    print("\n=== Testing Material Creation ===")
    
    # Test with required fields based on schema
    material_data = {
        "name": "Debug Test Material",
        "unit": "kg",
        "typical_waste_pct": 5.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/materials/", json=material_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            return response.json()
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

def test_project_creation():
    """Test project creation"""
    print("\n=== Testing Project Creation ===")
    
    project_data = {
        "name": "Debug Test Project",
        "client_name": "Debug Client"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/projects/", json=project_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            return response.json()
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

def test_rate_card_creation():
    """Test rate card creation"""
    print("\n=== Testing Rate Card Creation ===")
    
    rate_card_data = {
        "role": "debug-tester",
        "hourly_rate_nis": 100.0,
        "default_efficiency": 1.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/rate-cards/", json=rate_card_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            return response.json()
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

def test_shipping_quote_creation():
    """Test shipping quote creation"""
    print("\n=== Testing Shipping Quote Creation ===")
    
    quote_data = {
        "distance_km": 10.0,
        "weight_kg": 5.0,
        "base_fee_nis": 50.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/shipping-quotes/", json=quote_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            return response.json()
            
    except Exception as e:
        print(f"Exception: {e}")
    
    return None

def main():
    print("🔍 Debug CRUD Test")
    print("=" * 40)
    
    if not test_api_connection():
        print("❌ API connection failed")
        return
    
    # Test each endpoint
    vendor = test_vendor_creation()
    material = test_material_creation()
    project = test_project_creation()
    rate_card = test_rate_card_creation()
    shipping_quote = test_shipping_quote_creation()
    
    print("\n" + "=" * 40)
    print("📊 Results Summary:")
    print(f"Vendor: {'✅' if vendor else '❌'}")
    print(f"Material: {'✅' if material else '❌'}")
    print(f"Project: {'✅' if project else '❌'}")
    print(f"Rate Card: {'✅' if rate_card else '❌'}")
    print(f"Shipping Quote: {'✅' if shipping_quote else '❌'}")

if __name__ == "__main__":
    main()