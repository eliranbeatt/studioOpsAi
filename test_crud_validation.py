#!/usr/bin/env python3
"""
Comprehensive CRUD validation test for all StudioOps entities.
Tests all endpoints, foreign key relationships, complex queries, and data integrity.
"""

import requests
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
import sys
import time

# API base URL
BASE_URL = "http://localhost:8000"

class CRUDValidator:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.errors = []
        self.successes = []
        
    def log_success(self, message):
        print(f"✅ {message}")
        self.successes.append(message)
        
    def log_error(self, message):
        print(f"❌ {message}")
        self.errors.append(message)
        
    def log_info(self, message):
        print(f"ℹ️  {message}")
        
    def check_api_health(self):
        """Check if API is running and database is connected"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("database") == "connected":
                    self.log_success("API health check passed - database connected")
                    return True
                else:
                    self.log_error("Database not connected")
                    return False
            else:
                self.log_error(f"API health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_error(f"Failed to connect to API: {e}")
            return False
    
    def test_vendors_crud(self):
        """Test vendors CRUD operations"""
        self.log_info("Testing Vendors CRUD operations...")
        
        # CREATE - Test vendor creation
        vendor_data = {
            "name": "Test Vendor CRUD",
            "contact": {
                "email": "test@vendor.com",
                "phone": "123-456-7890"
            },
            "url": "https://testvendor.com",
            "rating": 4,
            "notes": "Test vendor for CRUD validation"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/vendors/", json=vendor_data)
            if response.status_code == 201:
                vendor = response.json()
                self.test_data['vendor_id'] = vendor['id']
                self.log_success(f"Created vendor: {vendor['name']} (ID: {vendor['id']})")
            else:
                self.log_error(f"Failed to create vendor: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_error(f"Exception creating vendor: {e}")
            return False
        
        # READ - Test vendor retrieval
        try:
            response = self.session.get(f"{BASE_URL}/vendors/{self.test_data['vendor_id']}")
            if response.status_code == 200:
                vendor = response.json()
                if vendor['name'] == vendor_data['name']:
                    self.log_success("Vendor retrieval successful")
                else:
                    self.log_error("Vendor data mismatch on retrieval")
            else:
                self.log_error(f"Failed to retrieve vendor: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception retrieving vendor: {e}")
        
        # UPDATE - Test vendor update
        update_data = {
            "name": "Updated Test Vendor CRUD",
            "rating": 5,
            "notes": "Updated notes for CRUD validation"
        }
        
        try:
            response = self.session.put(f"{BASE_URL}/vendors/{self.test_data['vendor_id']}", json=update_data)
            if response.status_code == 200:
                vendor = response.json()
                if vendor['name'] == update_data['name'] and vendor['rating'] == update_data['rating']:
                    self.log_success("Vendor update successful")
                else:
                    self.log_error("Vendor update data mismatch")
            else:
                self.log_error(f"Failed to update vendor: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_error(f"Exception updating vendor: {e}")
        
        # LIST - Test vendor listing
        try:
            response = self.session.get(f"{BASE_URL}/vendors/")
            if response.status_code == 200:
                vendors = response.json()
                if isinstance(vendors, list) and len(vendors) > 0:
                    self.log_success(f"Vendor listing successful - found {len(vendors)} vendors")
                else:
                    self.log_error("Vendor listing returned empty or invalid data")
            else:
                self.log_error(f"Failed to list vendors: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception listing vendors: {e}")
        
        return True
    
    def test_materials_crud(self):
        """Test materials CRUD operations"""
        self.log_info("Testing Materials CRUD operations...")
        
        # CREATE - Test material creation
        material_data = {
            "name": "Test Material CRUD",
            "spec": "High-quality test material specification",
            "unit": "kg",
            "category": "test-category",
            "typical_waste_pct": 5.5,
            "notes": "Test material for CRUD validation"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/materials/", json=material_data)
            if response.status_code == 201:
                material = response.json()
                self.test_data['material_id'] = material['id']
                self.log_success(f"Created material: {material['name']} (ID: {material['id']})")
            else:
                self.log_error(f"Failed to create material: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_error(f"Exception creating material: {e}")
            return False
        
        # READ - Test material retrieval
        try:
            response = self.session.get(f"{BASE_URL}/materials/{self.test_data['material_id']}")
            if response.status_code == 200:
                material = response.json()
                if material['name'] == material_data['name']:
                    self.log_success("Material retrieval successful")
                else:
                    self.log_error("Material data mismatch on retrieval")
            else:
                self.log_error(f"Failed to retrieve material: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception retrieving material: {e}")
        
        # UPDATE - Test material update
        update_data = {
            "name": "Updated Test Material CRUD",
            "typical_waste_pct": 7.5,
            "notes": "Updated notes for CRUD validation"
        }
        
        try:
            response = self.session.put(f"{BASE_URL}/materials/{self.test_data['material_id']}", json=update_data)
            if response.status_code == 200:
                material = response.json()
                if material['name'] == update_data['name']:
                    self.log_success("Material update successful")
                else:
                    self.log_error("Material update data mismatch")
            else:
                self.log_error(f"Failed to update material: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_error(f"Exception updating material: {e}")
        
        # LIST - Test material listing
        try:
            response = self.session.get(f"{BASE_URL}/materials/")
            if response.status_code == 200:
                materials = response.json()
                if isinstance(materials, list) and len(materials) > 0:
                    self.log_success(f"Material listing successful - found {len(materials)} materials")
                else:
                    self.log_error("Material listing returned empty or invalid data")
            else:
                self.log_error(f"Failed to list materials: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception listing materials: {e}")
        
        return True
    
    def test_projects_crud(self):
        """Test projects CRUD operations"""
        self.log_info("Testing Projects CRUD operations...")
        
        # CREATE - Test project creation
        project_data = {
            "name": "Test Project CRUD",
            "client_name": "Test Client",
            "status": "draft",
            "start_date": "2024-01-15",
            "due_date": "2024-03-15",
            "budget_planned": 50000.00
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/projects/", json=project_data)
            if response.status_code in [200, 201]:
                project = response.json()
                self.test_data['project_id'] = project['id']
                self.log_success(f"Created project: {project['name']} (ID: {project['id']})")
            else:
                self.log_error(f"Failed to create project: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_error(f"Exception creating project: {e}")
            return False
        
        # READ - Test project retrieval
        try:
            response = self.session.get(f"{BASE_URL}/projects/{self.test_data['project_id']}")
            if response.status_code == 200:
                project = response.json()
                if project['name'] == project_data['name']:
                    self.log_success("Project retrieval successful")
                else:
                    self.log_error("Project data mismatch on retrieval")
            else:
                self.log_error(f"Failed to retrieve project: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception retrieving project: {e}")
        
        # UPDATE - Test project update
        update_data = {
            "name": "Updated Test Project CRUD",
            "status": "active",
            "budget_actual": 45000.00
        }
        
        try:
            response = self.session.put(f"{BASE_URL}/projects/{self.test_data['project_id']}", json=update_data)
            if response.status_code == 200:
                project = response.json()
                if project['name'] == update_data['name'] and project['status'] == update_data['status']:
                    self.log_success("Project update successful")
                else:
                    self.log_error("Project update data mismatch")
            else:
                self.log_error(f"Failed to update project: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_error(f"Exception updating project: {e}")
        
        # LIST - Test project listing
        try:
            response = self.session.get(f"{BASE_URL}/projects/")
            if response.status_code == 200:
                projects = response.json()
                if isinstance(projects, list) and len(projects) > 0:
                    self.log_success(f"Project listing successful - found {len(projects)} projects")
                else:
                    self.log_error("Project listing returned empty or invalid data")
            else:
                self.log_error(f"Failed to list projects: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception listing projects: {e}")
        
        return True
    
    def test_vendor_prices_crud(self):
        """Test vendor prices CRUD operations and foreign key relationships"""
        self.log_info("Testing Vendor Prices CRUD operations...")
        
        if 'vendor_id' not in self.test_data or 'material_id' not in self.test_data:
            self.log_error("Cannot test vendor prices - missing vendor or material IDs")
            return False
        
        # CREATE - Test vendor price creation with foreign keys
        price_data = {
            "vendor_id": self.test_data['vendor_id'],
            "material_id": self.test_data['material_id'],
            "sku": "TEST-SKU-001",
            "price_nis": 125.50,
            "fetched_at": datetime.now().isoformat(),
            "source_url": "https://test-vendor.com/product/123",
            "confidence": 0.95,
            "is_quote": False
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/vendor-prices/", json=price_data)
            if response.status_code == 201:
                price = response.json()
                self.test_data['vendor_price_id'] = price['id']
                self.log_success(f"Created vendor price: {price['price_nis']} NIS (ID: {price['id']})")
            else:
                self.log_error(f"Failed to create vendor price: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_error(f"Exception creating vendor price: {e}")
            return False
        
        # READ - Test vendor price retrieval
        try:
            response = self.session.get(f"{BASE_URL}/vendor-prices/{self.test_data['vendor_price_id']}")
            if response.status_code == 200:
                price = response.json()
                if str(price['vendor_id']) == str(self.test_data['vendor_id']):
                    self.log_success("Vendor price retrieval successful with correct foreign key")
                else:
                    self.log_error("Vendor price foreign key mismatch")
            else:
                self.log_error(f"Failed to retrieve vendor price: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception retrieving vendor price: {e}")
        
        # LIST - Test vendor price listing
        try:
            response = self.session.get(f"{BASE_URL}/vendor-prices/")
            if response.status_code == 200:
                prices = response.json()
                if isinstance(prices, list) and len(prices) > 0:
                    self.log_success(f"Vendor price listing successful - found {len(prices)} prices")
                else:
                    self.log_error("Vendor price listing returned empty or invalid data")
            else:
                self.log_error(f"Failed to list vendor prices: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception listing vendor prices: {e}")
        
        return True
    
    def test_purchases_crud(self):
        """Test purchases CRUD operations with foreign key relationships"""
        self.log_info("Testing Purchases CRUD operations...")
        
        if not all(key in self.test_data for key in ['vendor_id', 'material_id', 'project_id']):
            self.log_error("Cannot test purchases - missing required foreign key IDs")
            return False
        
        # CREATE - Test purchase creation with multiple foreign keys
        purchase_data = {
            "vendor_id": self.test_data['vendor_id'],
            "material_id": self.test_data['material_id'],
            "project_id": self.test_data['project_id'],
            "qty": 10.5,
            "unit_price_nis": 125.50,
            "tax_vat_pct": 17.0,
            "occurred_at": "2024-01-20",
            "receipt_path": "/receipts/test-receipt-001.pdf"
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/purchases/", json=purchase_data)
            if response.status_code == 201:
                purchase = response.json()
                self.test_data['purchase_id'] = purchase['id']
                self.log_success(f"Created purchase: {purchase['qty']} units at {purchase['unit_price_nis']} NIS (ID: {purchase['id']})")
            else:
                self.log_error(f"Failed to create purchase: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_error(f"Exception creating purchase: {e}")
            return False
        
        # READ - Test purchase retrieval
        try:
            response = self.session.get(f"{BASE_URL}/purchases/{self.test_data['purchase_id']}")
            if response.status_code == 200:
                purchase = response.json()
                if (str(purchase['vendor_id']) == str(self.test_data['vendor_id']) and
                    str(purchase['material_id']) == str(self.test_data['material_id']) and
                    str(purchase['project_id']) == str(self.test_data['project_id'])):
                    self.log_success("Purchase retrieval successful with correct foreign keys")
                else:
                    self.log_error("Purchase foreign key mismatch")
            else:
                self.log_error(f"Failed to retrieve purchase: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception retrieving purchase: {e}")
        
        # LIST - Test purchase listing
        try:
            response = self.session.get(f"{BASE_URL}/purchases/")
            if response.status_code == 200:
                purchases = response.json()
                if isinstance(purchases, list) and len(purchases) > 0:
                    self.log_success(f"Purchase listing successful - found {len(purchases)} purchases")
                else:
                    self.log_error("Purchase listing returned empty or invalid data")
            else:
                self.log_error(f"Failed to list purchases: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception listing purchases: {e}")
        
        return True
    
    def test_rate_cards_crud(self):
        """Test rate cards CRUD operations"""
        self.log_info("Testing Rate Cards CRUD operations...")
        
        # CREATE - Test rate card creation
        rate_card_data = {
            "role": "test-developer",
            "hourly_rate_nis": 150.00,
            "overtime_rules_json": {
                "after_hours": 8,
                "multiplier": 1.5
            },
            "default_efficiency": 0.85
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/rate-cards/", json=rate_card_data)
            if response.status_code == 201:
                rate_card = response.json()
                self.test_data['rate_card_role'] = rate_card['role']
                self.log_success(f"Created rate card: {rate_card['role']} at {rate_card['hourly_rate_nis']} NIS/hour")
            else:
                self.log_error(f"Failed to create rate card: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_error(f"Exception creating rate card: {e}")
            return False
        
        # READ - Test rate card retrieval
        try:
            response = self.session.get(f"{BASE_URL}/rate-cards/{self.test_data['rate_card_role']}")
            if response.status_code == 200:
                rate_card = response.json()
                if rate_card['role'] == rate_card_data['role']:
                    self.log_success("Rate card retrieval successful")
                else:
                    self.log_error("Rate card data mismatch on retrieval")
            else:
                self.log_error(f"Failed to retrieve rate card: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception retrieving rate card: {e}")
        
        # UPDATE - Test rate card update
        update_data = {
            "hourly_rate_nis": 175.00,
            "default_efficiency": 0.90
        }
        
        try:
            response = self.session.put(f"{BASE_URL}/rate-cards/{self.test_data['rate_card_role']}", json=update_data)
            if response.status_code == 200:
                rate_card = response.json()
                if float(rate_card['hourly_rate_nis']) == update_data['hourly_rate_nis']:
                    self.log_success("Rate card update successful")
                else:
                    self.log_error("Rate card update data mismatch")
            else:
                self.log_error(f"Failed to update rate card: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_error(f"Exception updating rate card: {e}")
        
        # LIST - Test rate card listing
        try:
            response = self.session.get(f"{BASE_URL}/rate-cards/")
            if response.status_code == 200:
                rate_cards = response.json()
                if isinstance(rate_cards, list) and len(rate_cards) > 0:
                    self.log_success(f"Rate card listing successful - found {len(rate_cards)} rate cards")
                else:
                    self.log_error("Rate card listing returned empty or invalid data")
            else:
                self.log_error(f"Failed to list rate cards: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception listing rate cards: {e}")
        
        return True
    
    def test_shipping_quotes_crud(self):
        """Test shipping quotes CRUD operations"""
        self.log_info("Testing Shipping Quotes CRUD operations...")
        
        # CREATE - Test shipping quote creation
        quote_data = {
            "route_hash": "test-route-hash-001",
            "distance_km": 25.5,
            "weight_kg": 150.0,
            "type": "standard",
            "base_fee_nis": 50.00,
            "per_km_nis": 2.50,
            "per_kg_nis": 0.75,
            "surge_json": {
                "peak_hours": False,
                "weather_factor": 1.0
            },
            "fetched_at": datetime.now().isoformat(),
            "source": "test-shipping-api",
            "confidence": 0.88
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/shipping-quotes/", json=quote_data)
            if response.status_code == 201:
                quote = response.json()
                self.test_data['shipping_quote_id'] = quote['id']
                self.log_success(f"Created shipping quote: {quote['base_fee_nis']} NIS base fee (ID: {quote['id']})")
            else:
                self.log_error(f"Failed to create shipping quote: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log_error(f"Exception creating shipping quote: {e}")
            return False
        
        # READ - Test shipping quote retrieval
        try:
            response = self.session.get(f"{BASE_URL}/shipping-quotes/{self.test_data['shipping_quote_id']}")
            if response.status_code == 200:
                quote = response.json()
                if quote['route_hash'] == quote_data['route_hash']:
                    self.log_success("Shipping quote retrieval successful")
                else:
                    self.log_error("Shipping quote data mismatch on retrieval")
            else:
                self.log_error(f"Failed to retrieve shipping quote: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception retrieving shipping quote: {e}")
        
        # LIST - Test shipping quote listing
        try:
            response = self.session.get(f"{BASE_URL}/shipping-quotes/")
            if response.status_code == 200:
                quotes = response.json()
                if isinstance(quotes, list) and len(quotes) > 0:
                    self.log_success(f"Shipping quote listing successful - found {len(quotes)} quotes")
                else:
                    self.log_error("Shipping quote listing returned empty or invalid data")
            else:
                self.log_error(f"Failed to list shipping quotes: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception listing shipping quotes: {e}")
        
        return True
    
    def test_complex_queries(self):
        """Test complex queries and joins"""
        self.log_info("Testing complex queries and joins...")
        
        # Test project with related data query
        if 'project_id' in self.test_data:
            try:
                response = self.session.get(f"{BASE_URL}/projects/{self.test_data['project_id']}/details")
                if response.status_code == 200:
                    self.log_success("Complex project details query successful")
                elif response.status_code == 404:
                    self.log_info("Project details endpoint not implemented (expected)")
                else:
                    self.log_error(f"Project details query failed: {response.status_code}")
            except Exception as e:
                self.log_error(f"Exception in project details query: {e}")
        
        # Test vendor with prices query
        if 'vendor_id' in self.test_data:
            try:
                response = self.session.get(f"{BASE_URL}/vendors/{self.test_data['vendor_id']}/prices")
                if response.status_code == 200:
                    self.log_success("Vendor prices join query successful")
                elif response.status_code == 404:
                    self.log_info("Vendor prices endpoint not implemented (expected)")
                else:
                    self.log_error(f"Vendor prices query failed: {response.status_code}")
            except Exception as e:
                self.log_error(f"Exception in vendor prices query: {e}")
        
        # Test material with vendor prices query
        if 'material_id' in self.test_data:
            try:
                response = self.session.get(f"{BASE_URL}/materials/{self.test_data['material_id']}/prices")
                if response.status_code == 200:
                    self.log_success("Material prices join query successful")
                elif response.status_code == 404:
                    self.log_info("Material prices endpoint not implemented (expected)")
                else:
                    self.log_error(f"Material prices query failed: {response.status_code}")
            except Exception as e:
                self.log_error(f"Exception in material prices query: {e}")
    
    def test_data_integrity(self):
        """Test data integrity and constraints"""
        self.log_info("Testing data integrity and constraints...")
        
        # Test duplicate vendor creation (should handle gracefully)
        duplicate_vendor = {
            "name": "Test Vendor CRUD",  # Same name as created earlier
            "contact": {"email": "duplicate@test.com"}
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/vendors/", json=duplicate_vendor)
            if response.status_code in [201, 409]:  # Created or conflict
                self.log_success("Duplicate vendor handling works correctly")
            else:
                self.log_error(f"Unexpected response for duplicate vendor: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception testing duplicate vendor: {e}")
        
        # Test invalid foreign key reference
        invalid_purchase = {
            "vendor_id": "00000000-0000-0000-0000-000000000000",  # Non-existent vendor
            "material_id": self.test_data.get('material_id'),
            "project_id": self.test_data.get('project_id'),
            "qty": 1.0,
            "unit_price_nis": 100.00
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/purchases/", json=invalid_purchase)
            if response.status_code in [400, 404, 422]:  # Bad request or not found
                self.log_success("Invalid foreign key constraint handled correctly")
            else:
                self.log_error(f"Invalid foreign key not properly rejected: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception testing invalid foreign key: {e}")
        
        # Test required field validation
        invalid_material = {
            "spec": "Missing required name field"
            # Missing required 'name' and 'unit' fields
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/materials/", json=invalid_material)
            if response.status_code in [400, 422]:  # Validation error
                self.log_success("Required field validation works correctly")
            else:
                self.log_error(f"Required field validation failed: {response.status_code}")
        except Exception as e:
            self.log_error(f"Exception testing required field validation: {e}")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        self.log_info("Cleaning up test data...")
        
        # Delete in reverse order of creation to handle foreign key constraints
        cleanup_order = [
            ('purchases', 'purchase_id'),
            ('vendor-prices', 'vendor_price_id'),
            ('shipping-quotes', 'shipping_quote_id'),
            ('rate-cards', 'rate_card_role'),
            ('projects', 'project_id'),
            ('materials', 'material_id'),
            ('vendors', 'vendor_id')
        ]
        
        for endpoint, id_key in cleanup_order:
            if id_key in self.test_data:
                try:
                    response = self.session.delete(f"{BASE_URL}/{endpoint}/{self.test_data[id_key]}")
                    if response.status_code in [200, 204, 404]:  # Success or already deleted
                        self.log_success(f"Cleaned up {endpoint}: {self.test_data[id_key]}")
                    else:
                        self.log_error(f"Failed to cleanup {endpoint}: {response.status_code}")
                except Exception as e:
                    self.log_error(f"Exception cleaning up {endpoint}: {e}")
    
    def run_all_tests(self):
        """Run all CRUD validation tests"""
        print("🚀 Starting comprehensive CRUD validation tests...")
        print("=" * 60)
        
        # Check API health first
        if not self.check_api_health():
            print("❌ API health check failed - aborting tests")
            return False
        
        # Run all CRUD tests
        test_methods = [
            self.test_vendors_crud,
            self.test_materials_crud,
            self.test_projects_crud,
            self.test_vendor_prices_crud,
            self.test_purchases_crud,
            self.test_rate_cards_crud,
            self.test_shipping_quotes_crud,
            self.test_complex_queries,
            self.test_data_integrity
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                print()  # Add spacing between tests
            except Exception as e:
                self.log_error(f"Unexpected error in {test_method.__name__}: {e}")
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("=" * 60)
        print("📊 CRUD Validation Test Summary:")
        print(f"✅ Successes: {len(self.successes)}")
        print(f"❌ Errors: {len(self.errors)}")
        
        if self.errors:
            print("\n❌ Error Details:")
            for error in self.errors:
                print(f"  - {error}")
        
        if len(self.errors) == 0:
            print("\n🎉 All CRUD validation tests passed!")
            return True
        else:
            print(f"\n⚠️  {len(self.errors)} issues found during validation")
            return False

if __name__ == "__main__":
    validator = CRUDValidator()
    success = validator.run_all_tests()
    sys.exit(0 if success else 1)