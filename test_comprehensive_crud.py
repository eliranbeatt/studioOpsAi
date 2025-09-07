#!/usr/bin/env python3
"""
Comprehensive CRUD Operations Test
Tests all entity endpoints, foreign key relationships, complex queries, and data integrity constraints.
"""

import requests
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
import time

# API base URL
BASE_URL = "http://localhost:8000"

class CRUDTester:
    def __init__(self):
        self.test_results = []
        self.created_entities = {
            'vendors': [],
            'materials': [],
            'projects': [],
            'vendor_prices': [],
            'purchases': [],
            'shipping_quotes': [],
            'rate_cards': []
        }
    
    def log_test(self, test_name, success, message="", data=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if data:
            result['data'] = data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
        if not success and data:
            print(f"    Data: {data}")
    
    def test_health_check(self):
        """Test API health endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy' and data.get('database') == 'connected':
                    self.log_test("Health Check", True, "API and database are healthy")
                    return True
                else:
                    self.log_test("Health Check", False, f"Unhealthy status: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {e}")
            return False
    
    def test_vendors_crud(self):
        """Test vendors CRUD operations"""
        # CREATE
        vendor_data = {
            "name": "Test Vendor Ltd",
            "contact": {"email": "test@vendor.com", "phone": "+972-50-1234567"},
            "url": "https://testvendor.com",
            "rating": 4,
            "notes": "Test vendor for CRUD validation"
        }
        
        try:
            # Create vendor
            response = requests.post(f"{BASE_URL}/vendors/", json=vendor_data)
            if response.status_code == 201:
                vendor = response.json()
                vendor_id = vendor['id']
                self.created_entities['vendors'].append(vendor_id)
                self.log_test("Vendor CREATE", True, f"Created vendor with ID: {vendor_id}")
            else:
                self.log_test("Vendor CREATE", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # READ (single)
            response = requests.get(f"{BASE_URL}/vendors/{vendor_id}")
            if response.status_code == 200:
                retrieved_vendor = response.json()
                if retrieved_vendor['name'] == vendor_data['name']:
                    self.log_test("Vendor READ (single)", True, "Retrieved vendor matches created data")
                else:
                    self.log_test("Vendor READ (single)", False, "Retrieved vendor data mismatch")
            else:
                self.log_test("Vendor READ (single)", False, f"HTTP {response.status_code}: {response.text}")
            
            # READ (all)
            response = requests.get(f"{BASE_URL}/vendors/")
            if response.status_code == 200:
                vendors = response.json()
                if any(v['id'] == vendor_id for v in vendors):
                    self.log_test("Vendor READ (all)", True, f"Found vendor in list of {len(vendors)} vendors")
                else:
                    self.log_test("Vendor READ (all)", False, "Created vendor not found in list")
            else:
                self.log_test("Vendor READ (all)", False, f"HTTP {response.status_code}: {response.text}")
            
            # UPDATE
            update_data = {
                "name": "Updated Test Vendor Ltd",
                "rating": 5,
                "notes": "Updated notes for testing"
            }
            response = requests.put(f"{BASE_URL}/vendors/{vendor_id}", json=update_data)
            if response.status_code == 200:
                updated_vendor = response.json()
                if updated_vendor['name'] == update_data['name'] and updated_vendor['rating'] == 5:
                    self.log_test("Vendor UPDATE", True, "Vendor updated successfully")
                else:
                    self.log_test("Vendor UPDATE", False, "Update data mismatch")
            else:
                self.log_test("Vendor UPDATE", False, f"HTTP {response.status_code}: {response.text}")
            
            return True
            
        except Exception as e:
            self.log_test("Vendor CRUD", False, f"Exception: {e}")
            return False
    
    def test_materials_crud(self):
        """Test materials CRUD operations"""
        material_data = {
            "name": "Test Material",
            "spec": "High-grade test material specification",
            "unit": "kg",
            "category": "test-materials",
            "typical_waste_pct": 5.5,
            "notes": "Test material for CRUD validation"
        }
        
        try:
            # CREATE
            response = requests.post(f"{BASE_URL}/materials/", json=material_data)
            if response.status_code == 201:
                material = response.json()
                material_id = material['id']
                self.created_entities['materials'].append(material_id)
                self.log_test("Material CREATE", True, f"Created material with ID: {material_id}")
            else:
                self.log_test("Material CREATE", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # READ (single)
            response = requests.get(f"{BASE_URL}/materials/{material_id}")
            if response.status_code == 200:
                retrieved_material = response.json()
                if (retrieved_material['name'] == material_data['name'] and 
                    retrieved_material['typical_waste_pct'] == material_data['typical_waste_pct']):
                    self.log_test("Material READ (single)", True, "Retrieved material matches created data")
                else:
                    self.log_test("Material READ (single)", False, "Retrieved material data mismatch")
            else:
                self.log_test("Material READ (single)", False, f"HTTP {response.status_code}: {response.text}")
            
            # READ (all)
            response = requests.get(f"{BASE_URL}/materials/")
            if response.status_code == 200:
                materials = response.json()
                if any(m['id'] == material_id for m in materials):
                    self.log_test("Material READ (all)", True, f"Found material in list of {len(materials)} materials")
                else:
                    self.log_test("Material READ (all)", False, "Created material not found in list")
            else:
                self.log_test("Material READ (all)", False, f"HTTP {response.status_code}: {response.text}")
            
            # UPDATE
            update_data = {
                "name": "Updated Test Material",
                "typical_waste_pct": 7.5,
                "category": "updated-test-materials"
            }
            response = requests.put(f"{BASE_URL}/materials/{material_id}", json=update_data)
            if response.status_code == 200:
                updated_material = response.json()
                if (updated_material['name'] == update_data['name'] and 
                    updated_material['typical_waste_pct'] == update_data['typical_waste_pct']):
                    self.log_test("Material UPDATE", True, "Material updated successfully")
                else:
                    self.log_test("Material UPDATE", False, "Update data mismatch")
            else:
                self.log_test("Material UPDATE", False, f"HTTP {response.status_code}: {response.text}")
            
            return True
            
        except Exception as e:
            self.log_test("Material CRUD", False, f"Exception: {e}")
            return False
    
    def test_projects_crud(self):
        """Test projects CRUD operations"""
        project_data = {
            "name": "Test Project",
            "client_name": "Test Client Corp",
            "status": "active",
            "start_date": "2024-01-15",
            "due_date": "2024-03-15",
            "budget_planned": 50000.00,
            "budget_actual": 0.00
        }
        
        try:
            # CREATE
            response = requests.post(f"{BASE_URL}/projects/", json=project_data)
            if response.status_code == 200:
                project = response.json()
                project_id = project['id']
                self.created_entities['projects'].append(project_id)
                self.log_test("Project CREATE", True, f"Created project with ID: {project_id}")
            else:
                self.log_test("Project CREATE", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # READ (single)
            response = requests.get(f"{BASE_URL}/projects/{project_id}")
            if response.status_code == 200:
                retrieved_project = response.json()
                if retrieved_project['name'] == project_data['name']:
                    self.log_test("Project READ (single)", True, "Retrieved project matches created data")
                else:
                    self.log_test("Project READ (single)", False, "Retrieved project data mismatch")
            else:
                self.log_test("Project READ (single)", False, f"HTTP {response.status_code}: {response.text}")
            
            # READ (all)
            response = requests.get(f"{BASE_URL}/projects/")
            if response.status_code == 200:
                projects = response.json()
                if any(p['id'] == project_id for p in projects):
                    self.log_test("Project READ (all)", True, f"Found project in list of {len(projects)} projects")
                else:
                    self.log_test("Project READ (all)", False, "Created project not found in list")
            else:
                self.log_test("Project READ (all)", False, f"HTTP {response.status_code}: {response.text}")
            
            # UPDATE
            update_data = {
                "name": "Updated Test Project",
                "status": "completed",
                "budget_actual": 45000.00
            }
            response = requests.put(f"{BASE_URL}/projects/{project_id}", json=update_data)
            if response.status_code == 200:
                updated_project = response.json()
                if updated_project['name'] == update_data['name']:
                    self.log_test("Project UPDATE", True, "Project updated successfully")
                else:
                    self.log_test("Project UPDATE", False, "Update data mismatch")
            else:
                self.log_test("Project UPDATE", False, f"HTTP {response.status_code}: {response.text}")
            
            return True
            
        except Exception as e:
            self.log_test("Project CRUD", False, f"Exception: {e}")
            return False
    
    def test_foreign_key_relationships(self):
        """Test foreign key relationships between entities"""
        if not (self.created_entities['vendors'] and self.created_entities['materials']):
            self.log_test("Foreign Key Test", False, "Missing vendor or material entities for FK test")
            return False
        
        vendor_id = self.created_entities['vendors'][0]
        material_id = self.created_entities['materials'][0]
        
        # Test vendor_prices with foreign keys
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
        
        try:
            response = requests.post(f"{BASE_URL}/vendor-prices/", json=vendor_price_data)
            if response.status_code == 200:
                vendor_price = response.json()
                price_id = vendor_price['id']
                self.created_entities['vendor_prices'].append(price_id)
                self.log_test("Vendor Price FK CREATE", True, f"Created vendor price with FK relationships")
                
                # Test querying by vendor
                response = requests.get(f"{BASE_URL}/vendor-prices/vendor/{vendor_id}")
                if response.status_code == 200:
                    vendor_prices = response.json()
                    if any(vp['id'] == price_id for vp in vendor_prices):
                        self.log_test("Vendor Price FK QUERY (by vendor)", True, "Found price by vendor FK")
                    else:
                        self.log_test("Vendor Price FK QUERY (by vendor)", False, "Price not found by vendor FK")
                else:
                    self.log_test("Vendor Price FK QUERY (by vendor)", False, f"HTTP {response.status_code}")
                
                # Test querying by material
                response = requests.get(f"{BASE_URL}/vendor-prices/material/{material_id}")
                if response.status_code == 200:
                    material_prices = response.json()
                    if any(mp['id'] == price_id for mp in material_prices):
                        self.log_test("Vendor Price FK QUERY (by material)", True, "Found price by material FK")
                    else:
                        self.log_test("Vendor Price FK QUERY (by material)", False, "Price not found by material FK")
                else:
                    self.log_test("Vendor Price FK QUERY (by material)", False, f"HTTP {response.status_code}")
                
            else:
                self.log_test("Vendor Price FK CREATE", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Foreign Key Test", False, f"Exception: {e}")
            return False
    
    def test_purchases_crud(self):
        """Test purchases CRUD operations"""
        if not (self.created_entities['vendors'] and self.created_entities['materials']):
            self.log_test("Purchase CRUD", False, "Missing vendor or material entities for purchase test")
            return False
        
        vendor_id = self.created_entities['vendors'][0]
        material_id = self.created_entities['materials'][0]
        
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
        
        try:
            # CREATE
            response = requests.post(f"{BASE_URL}/purchases/", json=purchase_data)
            if response.status_code == 200:
                purchase = response.json()
                purchase_id = purchase['id']
                self.created_entities['purchases'].append(purchase_id)
                self.log_test("Purchase CREATE", True, f"Created purchase with ID: {purchase_id}")
            else:
                self.log_test("Purchase CREATE", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # READ (single)
            response = requests.get(f"{BASE_URL}/purchases/{purchase_id}")
            if response.status_code == 200:
                retrieved_purchase = response.json()
                if str(retrieved_purchase['vendor_id']) == vendor_id:
                    self.log_test("Purchase READ (single)", True, "Retrieved purchase matches created data")
                else:
                    self.log_test("Purchase READ (single)", False, "Retrieved purchase data mismatch")
            else:
                self.log_test("Purchase READ (single)", False, f"HTTP {response.status_code}: {response.text}")
            
            # Test querying by vendor
            response = requests.get(f"{BASE_URL}/purchases/vendor/{vendor_id}")
            if response.status_code == 200:
                vendor_purchases = response.json()
                if any(p['id'] == purchase_id for p in vendor_purchases):
                    self.log_test("Purchase QUERY (by vendor)", True, "Found purchase by vendor")
                else:
                    self.log_test("Purchase QUERY (by vendor)", False, "Purchase not found by vendor")
            else:
                self.log_test("Purchase QUERY (by vendor)", False, f"HTTP {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Purchase CRUD", False, f"Exception: {e}")
            return False
    
    def test_shipping_quotes_crud(self):
        """Test shipping quotes CRUD operations"""
        shipping_quote_data = {
            "route_hash": "test_route_123",
            "distance_km": 50.5,
            "weight_kg": 25.0,
            "type": "standard",
            "base_fee_nis": 100.0,
            "per_km_nis": 2.5,
            "per_kg_nis": 1.0,
            "surge_json": {"peak_hours": True, "multiplier": 1.2},
            "fetched_at": datetime.now().isoformat(),
            "source": "test_api",
            "confidence": 0.85
        }
        
        try:
            # CREATE
            response = requests.post(f"{BASE_URL}/shipping-quotes/", json=shipping_quote_data)
            if response.status_code == 200:
                quote = response.json()
                quote_id = quote['id']
                self.created_entities['shipping_quotes'].append(quote_id)
                self.log_test("Shipping Quote CREATE", True, f"Created shipping quote with ID: {quote_id}")
            else:
                self.log_test("Shipping Quote CREATE", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # READ (single)
            response = requests.get(f"{BASE_URL}/shipping-quotes/{quote_id}")
            if response.status_code == 200:
                retrieved_quote = response.json()
                if retrieved_quote['route_hash'] == shipping_quote_data['route_hash']:
                    self.log_test("Shipping Quote READ (single)", True, "Retrieved quote matches created data")
                else:
                    self.log_test("Shipping Quote READ (single)", False, "Retrieved quote data mismatch")
            else:
                self.log_test("Shipping Quote READ (single)", False, f"HTTP {response.status_code}: {response.text}")
            
            # Test estimate endpoint
            response = requests.post(f"{BASE_URL}/shipping-quotes/estimate", params={
                "distance_km": 50.5,
                "weight_kg": 25.0,
                "type": "standard"
            })
            if response.status_code == 200:
                estimate = response.json()
                if 'cost' in estimate and 'components' in estimate:
                    self.log_test("Shipping Quote ESTIMATE", True, f"Estimate calculated: {estimate['cost']} NIS")
                else:
                    self.log_test("Shipping Quote ESTIMATE", False, "Invalid estimate response format")
            else:
                self.log_test("Shipping Quote ESTIMATE", False, f"HTTP {response.status_code}: {response.text}")
            
            return True
            
        except Exception as e:
            self.log_test("Shipping Quote CRUD", False, f"Exception: {e}")
            return False
    
    def test_rate_cards_crud(self):
        """Test rate cards CRUD operations"""
        rate_card_data = {
            "role": "test-developer",
            "hourly_rate_nis": 150.0,
            "overtime_rules_json": {"after_hours": 8, "multiplier": 1.5},
            "default_efficiency": 1.0
        }
        
        try:
            # CREATE
            response = requests.post(f"{BASE_URL}/rate-cards/", json=rate_card_data)
            if response.status_code == 200:
                rate_card = response.json()
                role = rate_card['role']
                self.created_entities['rate_cards'].append(role)
                self.log_test("Rate Card CREATE", True, f"Created rate card for role: {role}")
            else:
                self.log_test("Rate Card CREATE", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # READ (single)
            response = requests.get(f"{BASE_URL}/rate-cards/{role}")
            if response.status_code == 200:
                retrieved_card = response.json()
                if retrieved_card['hourly_rate_nis'] == rate_card_data['hourly_rate_nis']:
                    self.log_test("Rate Card READ (single)", True, "Retrieved rate card matches created data")
                else:
                    self.log_test("Rate Card READ (single)", False, "Retrieved rate card data mismatch")
            else:
                self.log_test("Rate Card READ (single)", False, f"HTTP {response.status_code}: {response.text}")
            
            # READ (all)
            response = requests.get(f"{BASE_URL}/rate-cards/")
            if response.status_code == 200:
                rate_cards = response.json()
                if any(rc['role'] == role for rc in rate_cards):
                    self.log_test("Rate Card READ (all)", True, f"Found rate card in list of {len(rate_cards)} cards")
                else:
                    self.log_test("Rate Card READ (all)", False, "Created rate card not found in list")
            else:
                self.log_test("Rate Card READ (all)", False, f"HTTP {response.status_code}: {response.text}")
            
            return True
            
        except Exception as e:
            self.log_test("Rate Card CRUD", False, f"Exception: {e}")
            return False
    
    def test_data_integrity_constraints(self):
        """Test data integrity and validation constraints"""
        tests_passed = 0
        total_tests = 0
        
        # Test invalid vendor rating (should be 1-5)
        total_tests += 1
        invalid_vendor = {
            "name": "Invalid Vendor",
            "rating": 10  # Invalid rating > 5
        }
        try:
            response = requests.post(f"{BASE_URL}/vendors/", json=invalid_vendor)
            if response.status_code >= 400:
                self.log_test("Data Integrity - Invalid Vendor Rating", True, "Correctly rejected invalid rating")
                tests_passed += 1
            else:
                self.log_test("Data Integrity - Invalid Vendor Rating", False, "Should have rejected invalid rating")
        except Exception as e:
            self.log_test("Data Integrity - Invalid Vendor Rating", False, f"Exception: {e}")
        
        # Test invalid material waste percentage (should be 0-100)
        total_tests += 1
        invalid_material = {
            "name": "Invalid Material",
            "unit": "kg",
            "typical_waste_pct": 150.0  # Invalid percentage > 100
        }
        try:
            response = requests.post(f"{BASE_URL}/materials/", json=invalid_material)
            if response.status_code >= 400:
                self.log_test("Data Integrity - Invalid Waste Percentage", True, "Correctly rejected invalid waste percentage")
                tests_passed += 1
            else:
                self.log_test("Data Integrity - Invalid Waste Percentage", False, "Should have rejected invalid waste percentage")
        except Exception as e:
            self.log_test("Data Integrity - Invalid Waste Percentage", False, f"Exception: {e}")
        
        # Test missing required fields
        total_tests += 1
        incomplete_vendor = {
            "contact": {"email": "test@test.com"}
            # Missing required 'name' field
        }
        try:
            response = requests.post(f"{BASE_URL}/vendors/", json=incomplete_vendor)
            if response.status_code >= 400:
                self.log_test("Data Integrity - Missing Required Field", True, "Correctly rejected missing required field")
                tests_passed += 1
            else:
                self.log_test("Data Integrity - Missing Required Field", False, "Should have rejected missing required field")
        except Exception as e:
            self.log_test("Data Integrity - Missing Required Field", False, f"Exception: {e}")
        
        return tests_passed == total_tests
    
    def test_complex_queries(self):
        """Test complex queries and search functionality"""
        if not self.created_entities['vendor_prices']:
            self.log_test("Complex Queries", False, "No vendor prices available for complex query testing")
            return False
        
        try:
            # Test vendor price search with filters
            response = requests.get(f"{BASE_URL}/vendor-prices/search", params={
                "q": "TEST",
                "since": "2024-01-01T00:00:00"
            })
            if response.status_code == 200:
                search_results = response.json()
                self.log_test("Complex Query - Vendor Price Search", True, f"Search returned {len(search_results)} results")
            else:
                self.log_test("Complex Query - Vendor Price Search", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Complex Queries", False, f"Exception: {e}")
            return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        cleanup_results = []
        
        # Delete in reverse order to handle foreign key constraints
        for entity_type in ['vendor_prices', 'purchases', 'shipping_quotes', 'rate_cards', 'projects', 'materials', 'vendors']:
            for entity_id in self.created_entities[entity_type]:
                try:
                    if entity_type == 'rate_cards':
                        # Rate cards use role as primary key
                        response = requests.delete(f"{BASE_URL}/{entity_type.replace('_', '-')}/{entity_id}")
                    else:
                        response = requests.delete(f"{BASE_URL}/{entity_type.replace('_', '-')}/{entity_id}")
                    
                    if response.status_code in [200, 204]:
                        cleanup_results.append(f"✅ Deleted {entity_type}: {entity_id}")
                    else:
                        cleanup_results.append(f"❌ Failed to delete {entity_type}: {entity_id} - HTTP {response.status_code}")
                except Exception as e:
                    cleanup_results.append(f"❌ Error deleting {entity_type}: {entity_id} - {e}")
        
        return cleanup_results
    
    def run_all_tests(self):
        """Run all CRUD validation tests"""
        print("🚀 Starting Comprehensive CRUD Operations Test")
        print("=" * 60)
        
        # Health check first
        if not self.test_health_check():
            print("❌ Health check failed. Aborting tests.")
            return False
        
        # Run all CRUD tests
        test_methods = [
            self.test_vendors_crud,
            self.test_materials_crud,
            self.test_projects_crud,
            self.test_foreign_key_relationships,
            self.test_purchases_crud,
            self.test_shipping_quotes_crud,
            self.test_rate_cards_crud,
            self.test_data_integrity_constraints,
            self.test_complex_queries
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test method {test_method.__name__} failed with exception: {e}")
        
        print("\n" + "=" * 60)
        print("🧹 Cleaning up test data...")
        cleanup_results = self.cleanup_test_data()
        for result in cleanup_results:
            print(result)
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_count = sum(1 for result in self.test_results if result['success'])
        total_count = len(self.test_results)
        
        print(f"Total Tests: {total_count}")
        print(f"Passed: {success_count}")
        print(f"Failed: {total_count - success_count}")
        print(f"Success Rate: {(success_count/total_count)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        print("\n" + "=" * 60)
        
        return success_count == total_count

if __name__ == "__main__":
    tester = CRUDTester()
    success = tester.run_all_tests()
    
    # Save detailed results to file
    with open('crud_test_results.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: crud_test_results.json")
    
    if success:
        print("🎉 All CRUD operations validated successfully!")
        exit(0)
    else:
        print("⚠️  Some tests failed. Check the results above.")
        exit(1)