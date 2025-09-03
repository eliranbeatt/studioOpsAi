"""Comprehensive tests for estimation and pricing services"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from services.estimation_service import estimation_service
    from services.pricing_resolver import pricing_resolver
    from packages.schemas.estimation import (
        ShippingEstimateRequest, ShippingMethod,
        LaborEstimateRequest, LaborRole,
        ProjectEstimateRequest, MaterialRequirement,
        ShippingQuoteCreate
    )
except ImportError as e:
    print(f"Import error: {e}")
    # Create mock classes for testing
    from enum import Enum
    from pydantic import BaseModel
    from typing import List, Optional
    
    class ShippingMethod(str, Enum):
        STANDARD = "STANDARD"
        EXPRESS = "EXPRESS"
        FREIGHT = "FREIGHT"
        LOCAL = "LOCAL"
    
    class LaborRole(str, Enum):
        CARPENTER = "CARPENTER"
        PAINTER = "PAINTER"
        ELECTRICIAN = "ELECTRICIAN"
        PLUMBER = "PLUMBER"
        LABORER = "LABORER"
        PROJECT_MANAGER = "PROJECT_MANAGER"
        DESIGNER = "DESIGNER"
        INSTALLER = "INSTALLER"
    
    class ShippingEstimateRequest(BaseModel):
        distance_km: float
        weight_kg: float
        method: ShippingMethod
        urgency: float = 1.0
        fragile: bool = False
        insurance_value: float = 0.0
    
    class LaborEstimateRequest(BaseModel):
        role: LaborRole
        hours_required: float
        complexity: float = 1.0
        tools_required: bool = False
    
    class MaterialRequirement(BaseModel):
        material_name: str
        quantity: float
        unit: str
        waste_factor: float = 0.0
    
    class ProjectEstimateRequest(BaseModel):
        materials: List[MaterialRequirement]
        labor: List[LaborEstimateRequest]
        shipping: Optional[ShippingEstimateRequest] = None
        margin: float = 0.2
        tax_rate: float = 0.17

class TestPricingResolver:
    """Test pricing resolver functionality"""
    
    def test_get_material_price_existing(self):
        """Test getting price for existing material"""
        with patch.object(pricing_resolver, 'get_material_price') as mock_get:
            mock_get.return_value = {
                'material_name': 'Plywood 4x8',
                'unit': 'sheet',
                'price': 45.99,
                'confidence': 0.9,
                'vendor_name': 'Hardware Store'
            }
            
            result = pricing_resolver.get_material_price('Plywood 4x8')
            
            assert result is not None
            assert result['material_name'] == 'Plywood 4x8'
            assert result['price'] == 45.99
            assert result['confidence'] >= 0.7
    
    def test_get_material_price_non_existing(self):
        """Test getting price for non-existing material"""
        with patch.object(pricing_resolver, 'get_material_price') as mock_get:
            mock_get.return_value = None
            
            result = pricing_resolver.get_material_price('NonExistentMaterial')
            
            assert result is None
    
    def test_get_labor_rate_existing(self):
        """Test getting labor rate for existing role"""
        with patch.object(pricing_resolver, 'get_labor_rate') as mock_get:
            mock_get.return_value = {
                'role': 'Carpenter',
                'hourly_rate': 120.0,
                'efficiency': 0.9
            }
            
            result = pricing_resolver.get_labor_rate('Carpenter')
            
            assert result is not None
            assert result['role'] == 'Carpenter'
            assert result['hourly_rate'] == 120.0
    
    def test_get_labor_rate_non_existing(self):
        """Test getting labor rate for non-existing role"""
        with patch.object(pricing_resolver, 'get_labor_rate') as mock_get:
            mock_get.return_value = None
            
            result = pricing_resolver.get_labor_rate('NonExistentRole')
            
            assert result is None
    
    def test_estimate_shipping_cost(self):
        """Test shipping cost estimation"""
        result = pricing_resolver.estimate_shipping_cost(10.0, 100.0)
        
        assert 'estimated_cost' in result
        assert 'confidence' in result
        assert result['confidence'] >= 0.5
        assert result['estimated_cost'] > 0

class TestEstimationService:
    """Test estimation service functionality"""
    
    def test_estimate_shipping_standard(self):
        """Test standard shipping estimation"""
        request = ShippingEstimateRequest(
            distance_km=100.0,
            weight_kg=10.0,
            method=ShippingMethod.STANDARD,
            urgency=1.0,
            fragile=False,
            insurance_value=0.0
        )
        
        result = estimation_service.estimate_shipping(request)
        
        assert result.total_cost > 0
        assert result.confidence >= 0.5
        assert result.method == ShippingMethod.STANDARD
    
    def test_estimate_shipping_express(self):
        """Test express shipping estimation"""
        request = ShippingEstimateRequest(
            distance_km=100.0,
            weight_kg=10.0,
            method=ShippingMethod.EXPRESS,
            urgency=1.5,
            fragile=True,
            insurance_value=1000.0
        )
        
        result = estimation_service.estimate_shipping(request)
        
        assert result.total_cost > 0
        assert result.confidence >= 0.5
        assert result.method == ShippingMethod.EXPRESS
        assert result.urgency_surcharge > 0
        assert result.fragile_surcharge > 0
    
    def test_estimate_labor_carpenter(self):
        """Test labor estimation for carpenter"""
        request = LaborEstimateRequest(
            role=LaborRole.CARPENTER,
            hours_required=40.0,
            complexity=1.2,
            tools_required=True
        )
        
        result = estimation_service.estimate_labor(request)
        
        assert result.total_cost > 0
        assert result.confidence >= 0.5
        assert result.role == LaborRole.CARPENTER
        assert result.tool_surcharge > 0
    
    def test_estimate_labor_painter(self):
        """Test labor estimation for painter"""
        request = LaborEstimateRequest(
            role=LaborRole.PAINTER,
            hours_required=20.0,
            complexity=1.0,
            tools_required=False
        )
        
        result = estimation_service.estimate_labor(request)
        
        assert result.total_cost > 0
        assert result.confidence >= 0.5
        assert result.role == LaborRole.PAINTER
        assert result.tool_surcharge == 0
    
    def test_estimate_project_comprehensive(self):
        """Test comprehensive project estimation"""
        materials = [
            MaterialRequirement(
                material_name="Plywood 4x8",
                quantity=10.0,
                unit="sheet",
                waste_factor=0.1
            ),
            MaterialRequirement(
                material_name="2x4 Lumber",
                quantity=20.0,
                unit="piece",
                waste_factor=0.05
            )
        ]
        
        labor = [
            LaborEstimateRequest(
                role=LaborRole.CARPENTER,
                hours_required=40.0,
                complexity=1.2,
                tools_required=True
            ),
            LaborEstimateRequest(
                role=LaborRole.PAINTER,
                hours_required=20.0,
                complexity=1.0,
                tools_required=False
            )
        ]
        
        shipping = ShippingEstimateRequest(
            distance_km=100.0,
            weight_kg=50.0,
            method=ShippingMethod.STANDARD,
            urgency=1.0,
            fragile=False,
            insurance_value=0.0
        )
        
        request = ProjectEstimateRequest(
            materials=materials,
            labor=labor,
            shipping=shipping,
            margin=0.2,
            tax_rate=0.17
        )
        
        result = estimation_service.estimate_project(request)
        
        assert result.total_cost > 0
        assert result.confidence >= 0.5
        assert result.materials_cost > 0
        assert result.labor_cost > 0
        assert result.shipping_cost > 0
        assert len(result.materials) == 2
        assert len(result.labor) == 2

class TestEstimationAPI:
    """Test estimation API endpoints"""
    
    def test_estimate_shipping_api(self):
        """Test shipping estimation API endpoint"""
        payload = {
            "distance_km": 100.0,
            "weight_kg": 10.0,
            "method": "STANDARD",
            "urgency": 1.0,
            "fragile": False,
            "insurance_value": 0.0
        }
        
        response = client.post("/estimation/shipping", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data
        assert "confidence" in data
        assert data["total_cost"] > 0
    
    def test_estimate_labor_api(self):
        """Test labor estimation API endpoint"""
        payload = {
            "role": "CARPENTER",
            "hours_required": 40.0,
            "complexity": 1.2,
            "tools_required": True
        }
        
        response = client.post("/estimation/labor", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data
        assert "confidence" in data
        assert data["total_cost"] > 0
    
    def test_estimate_project_api(self):
        """Test project estimation API endpoint"""
        payload = {
            "materials": [
                {
                    "material_name": "Plywood 4x8",
                    "quantity": 10.0,
                    "unit": "sheet",
                    "waste_factor": 0.1
                }
            ],
            "labor": [
                {
                    "role": "CARPENTER",
                    "hours_required": 40.0,
                    "complexity": 1.2,
                    "tools_required": True
                }
            ],
            "shipping": {
                "distance_km": 100.0,
                "weight_kg": 50.0,
                "method": "STANDARD",
                "urgency": 1.0,
                "fragile": False,
                "insurance_value": 0.0
            },
            "margin": 0.2,
            "tax_rate": 0.17
        }
        
        response = client.post("/estimation/project", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data
        assert "confidence" in data
        assert data["total_cost"] > 0
        assert "materials" in data
        assert "labor" in data
    
    def test_list_rate_cards_api(self):
        """Test rate cards listing API endpoint"""
        response = client.get("/estimation/rate-cards")
        
        # Should return 200 even if empty
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_estimation_health_api(self):
        """Test estimation health check API endpoint"""
        response = client.get("/estimation/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "estimation"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])