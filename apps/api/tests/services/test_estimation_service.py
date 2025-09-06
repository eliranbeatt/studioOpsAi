"""Comprehensive tests for estimation service"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import uuid

from services.estimation_service import EstimationService, estimation_service
from packages.schemas.estimation import (
    ShippingEstimateRequest, ShippingMethod,
    LaborEstimateRequest, LaborRole,
    ProjectEstimateRequest, MaterialRequirement,
    ShippingQuoteCreate, RateCardUpdate
)
from services.pricing_resolver import pricing_resolver

def test_estimation_service_initialization():
    """Test EstimationService initialization"""
    service = EstimationService()
    assert service.db_url is not None
    assert "postgresql://" in service.db_url
    assert len(service.shipping_rates) == 4  # STANDARD, EXPRESS, FREIGHT, LOCAL
    assert len(service.labor_efficiency) == 8  # All labor roles

def test_get_db_connection():
    """Test database connection"""
    service = EstimationService()
    
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        conn = service.get_db_connection()
        assert conn is mock_conn

def test_estimate_shipping_basic():
    """Test basic shipping estimation"""
    service = EstimationService()
    
    request = ShippingEstimateRequest(
        distance_km=100.0,
        weight_kg=50.0,
        method=ShippingMethod.STANDARD,
        urgency=1.0,
        fragile=False,
        insurance_value=0.0
    )
    
    with patch.object(service, '_get_historical_shipping_quote', return_value=None):
        result = service.estimate_shipping(request)
        
        assert result is not None
        assert result.total_cost > 0
        assert result.base_cost == 50.0  # STANDARD base fee
        assert result.distance_cost == 200.0  # 100km * 2.0 per_km
        assert result.weight_cost == 250.0  # 50kg * 5.0 per_kg
        assert result.confidence == 0.7  # Default confidence

def test_estimate_shipping_with_historical_data():
    """Test shipping estimation with historical data"""
    service = EstimationService()
    
    request = ShippingEstimateRequest(
        distance_km=100.0,
        weight_kg=50.0,
        method=ShippingMethod.STANDARD,
        urgency=1.0,
        fragile=False,
        insurance_value=0.0
    )
    
    historical_data = {
        'base_fee': 45.0,
        'per_km': 1.8,
        'per_kg': 4.5,
        'distance': 90.0,
        'weight': 45.0,
        'method': 'standard',
        'confidence': 0.9
    }
    
    with patch.object(service, '_get_historical_shipping_quote', return_value=historical_data):
        result = service.estimate_shipping(request)
        
        assert result is not None
        assert result.total_cost > 0
        assert result.confidence == 0.855  # 0.9 * 0.95
        assert "historical" in result.notes.lower()

def test_estimate_shipping_with_surcharges():
    """Test shipping estimation with surcharges"""
    service = EstimationService()
    
    request = ShippingEstimateRequest(
        distance_km=100.0,
        weight_kg=50.0,
        method=ShippingMethod.EXPRESS,
        urgency=1.5,  # 50% surcharge
        fragile=True,  # 15% surcharge
        insurance_value=10000.0  # 0.5% insurance cost
    )
    
    with patch.object(service, '_get_historical_shipping_quote', return_value=None):
        result = service.estimate_shipping(request)
        
        assert result is not None
        assert result.urgency_surcharge > 0
        assert result.fragile_surcharge > 0
        assert result.insurance_cost == 50.0  # 10000 * 0.005

def test_estimate_shipping_error_fallback():
    """Test shipping estimation error fallback"""
    service = EstimationService()
    
    request = ShippingEstimateRequest(
        distance_km=100.0,
        weight_kg=50.0,
        method=ShippingMethod.STANDARD,
        urgency=1.0,
        fragile=False,
        insurance_value=0.0
    )
    
    with patch.object(service, '_get_historical_shipping_quote', side_effect=Exception("DB error")):
        with patch.object(pricing_resolver, 'estimate_shipping_cost') as mock_fallback:
            mock_fallback.return_value = {
                'base_fee': 50.0,
                'per_km_rate': 2.0,
                'per_kg_rate': 5.0,
                'estimated_cost': 350.0,
                'confidence': 0.7
            }
            
            result = service.estimate_shipping(request)
            
            assert result is not None
            assert result.total_cost == 350.0
            assert "fallback" in result.notes.lower()

def test_get_historical_shipping_quote():
    """Test historical shipping quote retrieval"""
    service = EstimationService()
    
    request = ShippingEstimateRequest(
        distance_km=100.0,
        weight_kg=50.0,
        method=ShippingMethod.STANDARD,
        urgency=1.0,
        fragile=False,
        insurance_value=0.0
    )
    
    with patch.object(service, 'get_db_connection') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [
            45.0, 1.8, 4.5, 90.0, 45.0, 'standard', 0.9
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = service._get_historical_shipping_quote(request)
        
        assert result is not None
        assert result['base_fee'] == 45.0
        assert result['per_km'] == 1.8
        assert result['confidence'] == 0.9

def test_estimate_labor_with_database_rates():
    """Test labor estimation with database rates"""
    service = EstimationService()
    
    request = LaborEstimateRequest(
        role=LaborRole.CARPENTER,
        hours_required=10.0,
        complexity=1.2,
        tools_required=True
    )
    
    with patch.object(pricing_resolver, 'get_labor_rate') as mock_get_rate:
        mock_get_rate.return_value = {
            'role': 'Carpenter',
            'hourly_rate': 120.0,
            'efficiency': 0.9,
            'vendor_name': 'Test Vendor'
        }
        
        result = service.estimate_labor(request)
        
        assert result is not None
        assert result.base_rate == 120.0
        assert result.regular_hours == 8.0  # 8-hour standard day
        assert result.overtime_hours == 3.11  # (10/0.9) - 8 = 11.11 - 8 = 3.11
        assert result.tool_surcharge > 0
        assert result.complexity_multiplier == 1.2

def test_estimate_labor_fallback_rates():
    """Test labor estimation with fallback rates"""
    service = EstimationService()
    
    request = LaborEstimateRequest(
        role=LaborRole.CARPENTER,
        hours_required=10.0,
        complexity=1.0,
        tools_required=False
    )
    
    with patch.object(pricing_resolver, 'get_labor_rate', return_value=None):
        result = service.estimate_labor(request)
        
        assert result is not None
        assert result.base_rate == 120.0  # Fallback rate for Carpenter
        assert result.total_cost == 1200.0  # 10 hours * 120.0 rate
        assert result.confidence == 0.7  # Lower confidence for fallback

def test_estimate_labor_error_fallback():
    """Test labor estimation error fallback"""
    service = EstimationService()
    
    request = LaborEstimateRequest(
        role=LaborRole.CARPENTER,
        hours_required=10.0,
        complexity=1.0,
        tools_required=False
    )
    
    with patch.object(pricing_resolver, 'get_labor_rate', side_effect=Exception("DB error")):
        result = service.estimate_labor(request)
        
        assert result is not None
        assert result.base_rate == 100.0  # Default fallback rate
        assert result.total_cost == 1000.0  # 10 hours * 100.0 rate
        assert result.confidence == 0.5  # Very low confidence for error fallback

def test_estimate_project_comprehensive():
    """Test comprehensive project estimation"""
    service = EstimationService()
    
    materials = [
        MaterialRequirement(
            material_name="Plywood 4x8",
            quantity=5.0,
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
            complexity=1.1,
            tools_required=True
        ),
        LaborEstimateRequest(
            role=LaborRole.LABORER,
            hours_required=20.0,
            complexity=1.0,
            tools_required=False
        )
    ]
    
    shipping = ShippingEstimateRequest(
        distance_km=50.0,
        weight_kg=200.0,
        method=ShippingMethod.STANDARD,
        urgency=1.0,
        fragile=False,
        insurance_value=0.0
    )
    
    request = ProjectEstimateRequest(
        materials=materials,
        labor=labor,
        shipping=shipping,
        margin=0.2,  # 20% margin
        tax_rate=0.17  # 17% tax
    )
    
    # Mock pricing resolver responses
    with patch.object(pricing_resolver, 'get_material_price') as mock_material:
        mock_material.side_effect = [
            {
                'material_id': 'mock-plywood-id',
                'material_name': 'Plywood 4x8',
                'unit': 'sheet',
                'price': 45.99,
                'confidence': 0.9,
                'vendor_name': 'Hardware Store'
            },
            {
                'material_id': 'mock-lumber-id',
                'material_name': '2x4 Lumber',
                'unit': 'piece',
                'price': 8.99,
                'confidence': 0.9,
                'vendor_name': 'Lumber Yard'
            }
        ]
        
        with patch.object(service, 'estimate_labor') as mock_labor:
            mock_labor.side_effect = [
                MagicMock(total_cost=5280.0, confidence=0.85),  # Carpenter: 40h * 120 * 1.1 = 5280
                MagicMock(total_cost=1600.0, confidence=0.8)   # Laborer: 20h * 80 = 1600
            ]
            
            with patch.object(service, 'estimate_shipping') as mock_shipping:
                mock_shipping.return_value = MagicMock(total_cost=350.0, confidence=0.7)
                
                result = service.estimate_project(request)
                
                assert result is not None
                assert result.materials_cost > 0
                assert result.labor_cost == 6880.0  # 5280 + 1600
                assert result.shipping_cost == 350.0
                assert result.subtotal > 0
                assert result.margin_amount > 0
                assert result.tax_amount > 0
                assert result.total_cost > 0
                assert result.confidence > 0.5
                assert len(result.materials) == 2
                assert len(result.labor) == 2

def test_save_shipping_quote():
    """Test saving shipping quote to database"""
    service = EstimationService()
    
    quote = ShippingQuoteCreate(
        distance_km=100.0,
        weight_kg=50.0,
        method=ShippingMethod.STANDARD,
        base_fee_nis=45.0,
        per_km_nis=1.8,
        per_kg_nis=4.5,
        source="test",
        confidence=0.9
    )
    
    with patch.object(service, 'get_db_connection') as mock_conn:
        mock_cursor = Mock()
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = service.save_shipping_quote(quote)
        
        assert result is True
        mock_cursor.execute.assert_called_once()

def test_update_rate_card():
    """Test updating rate card in database"""
    service = EstimationService()
    
    update = RateCardUpdate(
        hourly_rate_nis=120.0,
        default_efficiency=0.9,
        overtime_rules='{"rate": 1.5, "threshold": 8}'
    )
    
    with patch.object(service, 'get_db_connection') as mock_conn:
        mock_cursor = Mock()
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = service.update_rate_card("Carpenter", update)
        
        assert result is True
        mock_cursor.execute.assert_called_once()

def test_global_instance():
    """Test global estimation service instance"""
    assert estimation_service is not None
    assert isinstance(estimation_service, EstimationService)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])