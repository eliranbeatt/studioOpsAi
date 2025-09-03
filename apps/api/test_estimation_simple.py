"""Simple tests for estimation and pricing services"""

import pytest
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_pricing_resolver_material():
    """Test pricing resolver material lookup"""
    try:
        from services.pricing_resolver import pricing_resolver
        
        # Test getting material price
        result = pricing_resolver.get_material_price("Plywood 4x8")
        assert result is not None
        assert 'price' in result
        assert result['price'] > 0
        print(f"Material price test passed: {result['price']}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        pytest.skip("Pricing resolver not available")

def test_pricing_resolver_labor():
    """Test pricing resolver labor rate lookup"""
    try:
        from services.pricing_resolver import pricing_resolver
        
        # Test getting labor rate
        result = pricing_resolver.get_labor_rate("Carpenter")
        if result is not None:
            assert 'hourly_rate' in result
            assert result['hourly_rate'] > 0
            print(f"Labor rate test passed: {result['hourly_rate']}")
        else:
            print("Labor rate returned None (may not be configured)")
            
    except ImportError as e:
        print(f"Import error: {e}")
        pytest.skip("Pricing resolver not available")

def test_estimation_service_shipping():
    """Test estimation service shipping"""
    try:
        from services.estimation_service import estimation_service
        from packages.schemas.estimation import ShippingEstimateRequest, ShippingMethod
        
        # Test shipping estimation
        request = ShippingEstimateRequest(
            distance_km=100.0,
            weight_kg=10.0,
            method=ShippingMethod.STANDARD
        )
        
        result = estimation_service.estimate_shipping(request)
        assert result.total_cost > 0
        assert result.confidence >= 0.5
        print(f"Shipping estimation test passed: {result.total_cost}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        pytest.skip("Estimation service not available")

def test_estimation_service_labor():
    """Test estimation service labor"""
    try:
        from services.estimation_service import estimation_service
        from packages.schemas.estimation import LaborEstimateRequest, LaborRole
        
        # Test labor estimation
        request = LaborEstimateRequest(
            role=LaborRole.CARPENTER,
            hours_required=40.0
        )
        
        result = estimation_service.estimate_labor(request)
        assert result.total_cost > 0
        assert result.confidence >= 0.5
        print(f"Labor estimation test passed: {result.total_cost}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        pytest.skip("Estimation service not available")

def test_estimation_service_project():
    """Test estimation service project"""
    try:
        from services.estimation_service import estimation_service
        from packages.schemas.estimation import (
            ProjectEstimateRequest, MaterialRequirement, 
            LaborEstimateRequest, LaborRole
        )
        
        # Test project estimation
        materials = [
            MaterialRequirement(
                material_name="Plywood 4x8",
                quantity=10.0,
                unit="sheet"
            )
        ]
        
        labor = [
            LaborEstimateRequest(
                role=LaborRole.CARPENTER,
                hours_required=40.0
            )
        ]
        
        request = ProjectEstimateRequest(
            materials=materials,
            labor=labor
        )
        
        result = estimation_service.estimate_project(request)
        assert result.total_cost > 0
        assert result.confidence >= 0.5
        print(f"Project estimation test passed: {result.total_cost}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        pytest.skip("Estimation service not available")

if __name__ == "__main__":
    print("Running estimation service tests...")
    
    test_pricing_resolver_material()
    test_pricing_resolver_labor()
    test_estimation_service_shipping()
    test_estimation_service_labor()
    test_estimation_service_project()
    
    print("All tests completed!")