"""Comprehensive tests for pricing resolver service"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from services.pricing_resolver import PricingResolver, pricing_resolver

def test_pricing_resolver_initialization():
    """Test PricingResolver initialization"""
    resolver = PricingResolver()
    assert resolver.db_url is not None
    assert "postgresql://" in resolver.db_url

def test_get_connection_with_postgres():
    """Test database connection with psycopg2 available"""
    resolver = PricingResolver()
    
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        conn = resolver.get_connection()
        assert conn is mock_conn

def test_get_connection_without_postgres():
    """Test database connection fallback without psycopg2"""
    resolver = PricingResolver()
    
    # Temporarily remove psycopg2 availability
    original_has_postgres = resolver.__class__.__dict__.get('HAS_POSTGRES', True)
    resolver.__class__.HAS_POSTGRES = False
    
    try:
        conn = resolver.get_connection()
        assert conn is None
    finally:
        # Restore original value
        resolver.__class__.HAS_POSTGRES = original_has_postgres

def test_get_material_price_with_mock_data():
    """Test material price retrieval with mock data"""
    resolver = PricingResolver()
    
    # Test with mock data when database not available
    original_has_postgres = resolver.__class__.__dict__.get('HAS_POSTGRES', True)
    resolver.__class__.HAS_POSTGRES = False
    
    try:
        # Test known materials
        result = resolver.get_material_price("Plywood 4x8")
        assert result is not None
        assert result['material_name'] == "Plywood 4x8"
        assert result['price'] == 45.99
        assert result['unit'] == "sheet"
        assert result['vendor_name'] == "Hardware Store"
        assert result['confidence'] == 0.9
        
        # Test unknown material
        result = resolver.get_material_price("Unknown Material")
        assert result is None
        
    finally:
        # Restore original value
        resolver.__class__.HAS_POSTGRES = original_has_postgres

def test_get_material_price_with_database():
    """Test material price retrieval from database"""
    resolver = PricingResolver()
    
    with patch.object(resolver, 'get_connection') as mock_conn:
        mock_cursor = Mock()
        
        # Mock database responses
        mock_cursor.fetchone.side_effect = [
            ['material-123', 'Plywood 4x8', 'sheet'],  # Material found
            [45.99, 0.9, datetime.now(), 'Hardware Store', 4, 'PLY-001', False]  # Price found
        ]
        
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = resolver.get_material_price("Plywood 4x8")
        
        assert result is not None
        assert result['material_id'] == 'material-123'
        assert result['material_name'] == 'Plywood 4x8'
        assert result['price'] == 45.99
        assert result['confidence'] == 0.9
        assert result['vendor_name'] == 'Hardware Store'

def test_get_material_price_material_not_found():
    """Test material price when material not found in database"""
    resolver = PricingResolver()
    
    with patch.object(resolver, 'get_connection') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None  # Material not found
        
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = resolver.get_material_price("Unknown Material")
        assert result is None

def test_get_material_price_no_price_data():
    """Test material price when material found but no price data"""
    resolver = PricingResolver()
    
    with patch.object(resolver, 'get_connection') as mock_conn:
        mock_cursor = Mock()
        
        # Material found but no price data
        mock_cursor.fetchone.side_effect = [
            ['material-123', 'Test Material', 'unit'],  # Material found
            None  # No price data
        ]
        
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = resolver.get_material_price("Test Material")
        assert result is None

def test_get_material_price_database_error():
    """Test material price with database error fallback"""
    resolver = PricingResolver()
    
    with patch.object(resolver, 'get_connection', side_effect=Exception("DB error")):
        # Should fall back to mock data
        result = resolver.get_material_price("Plywood 4x8")
        assert result is not None
        assert result['material_name'] == "Plywood 4x8"

def test_get_labor_rate_with_mock_data():
    """Test labor rate retrieval with mock data"""
    resolver = PricingResolver()
    
    # Test with mock data when database not available
    original_has_postgres = resolver.__class__.__dict__.get('HAS_POSTGRES', True)
    resolver.__class__.HAS_POSTGRES = False
    
    try:
        # Test known roles
        result = resolver.get_labor_rate("Carpenter")
        assert result is not None
        assert result['role'] == "Carpenter"
        assert result['hourly_rate'] == 120.0
        assert result['efficiency'] == 0.9
        
        result = resolver.get_labor_rate("Painter")
        assert result is not None
        assert result['role'] == "Painter"
        assert result['hourly_rate'] == 100.0
        assert result['efficiency'] == 0.8
        
        # Test unknown role
        result = resolver.get_labor_rate("Unknown Role")
        assert result is None
        
    finally:
        # Restore original value
        resolver.__class__.HAS_POSTGRES = original_has_postgres

def test_get_labor_rate_with_database():
    """Test labor rate retrieval from database"""
    resolver = PricingResolver()
    
    with patch.object(resolver, 'get_connection') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [120.0, 0.9]  # hourly_rate, default_efficiency
        
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = resolver.get_labor_rate("Carpenter")
        
        assert result is not None
        assert result['role'] == "Carpenter"
        assert result['hourly_rate'] == 120.0
        assert result['efficiency'] == 0.9

def test_get_labor_rate_role_not_found():
    """Test labor rate when role not found in database"""
    resolver = PricingResolver()
    
    with patch.object(resolver, 'get_connection') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None  # Role not found
        
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = resolver.get_labor_rate("Unknown Role")
        assert result is None

def test_get_labor_rate_database_error():
    """Test labor rate with database error fallback"""
    resolver = PricingResolver()
    
    with patch.object(resolver, 'get_connection', side_effect=Exception("DB error")):
        # Should fall back to mock data
        result = resolver.get_labor_rate("Carpenter")
        assert result is not None
        assert result['role'] == "Carpenter"
        assert result['hourly_rate'] == 120.0

def test_estimate_shipping_cost():
    """Test shipping cost estimation"""
    resolver = PricingResolver()
    
    result = resolver.estimate_shipping_cost(50.0, 100.0)  # weight_kg, distance_km
    
    assert result is not None
    assert 'base_fee' in result
    assert 'per_km_rate' in result
    assert 'per_kg_rate' in result
    assert 'estimated_cost' in result
    assert 'confidence' in result
    
    # Verify calculation
    expected_cost = 50.0 + (100.0 * 2.0) + (50.0 * 5.0)  # base + distance + weight
    assert result['estimated_cost'] == expected_cost
    assert result['confidence'] == 0.7

def test_estimate_shipping_cost_edge_cases():
    """Test shipping cost estimation with edge cases"""
    resolver = PricingResolver()
    
    # Zero weight and distance
    result = resolver.estimate_shipping_cost(0.0, 0.0)
    assert result['estimated_cost'] == 50.0  # Just base fee
    
    # Very large weight and distance
    result = resolver.estimate_shipping_cost(1000.0, 500.0)
    expected_cost = 50.0 + (500.0 * 2.0) + (1000.0 * 5.0)
    assert result['estimated_cost'] == expected_cost

def test_global_instance():
    """Test global pricing resolver instance"""
    assert pricing_resolver is not None
    assert isinstance(pricing_resolver, PricingResolver)

def test_mock_prices_completeness():
    """Test that all mock prices are complete and valid"""
    resolver = PricingResolver()
    
    # Temporarily remove psycopg2 availability to use mock data
    original_has_postgres = resolver.__class__.__dict__.get('HAS_POSTGRES', True)
    resolver.__class__.HAS_POSTGRES = False
    
    try:
        # Test all mock materials
        materials = ['Plywood 4x8', '2x4 Lumber', 'Screws', 'Paint', 'Nails']
        
        for material in materials:
            result = resolver.get_material_price(material)
            assert result is not None, f"Mock data missing for {material}"
            assert 'price' in result, f"Price missing for {material}"
            assert 'unit' in result, f"Unit missing for {material}"
            assert 'vendor_name' in result, f"Vendor missing for {material}"
            assert 'confidence' in result, f"Confidence missing for {material}"
            assert result['price'] > 0, f"Invalid price for {material}"
            assert 0 <= result['confidence'] <= 1, f"Invalid confidence for {material}"
        
    finally:
        # Restore original value
        resolver.__class__.HAS_POSTGRES = original_has_postgres

def test_mock_labor_rates_completeness():
    """Test that all mock labor rates are complete and valid"""
    resolver = PricingResolver()
    
    # Temporarily remove psycopg2 availability to use mock data
    original_has_postgres = resolver.__class__.__dict__.get('HAS_POSTGRES', True)
    resolver.__class__.HAS_POSTGRES = False
    
    try:
        # Test all mock labor roles
        roles = ['Carpenter', 'Painter', 'Electrician', 'Laborer']
        
        for role in roles:
            result = resolver.get_labor_rate(role)
            assert result is not None, f"Mock data missing for {role}"
            assert 'hourly_rate' in result, f"Hourly rate missing for {role}"
            assert 'efficiency' in result, f"Efficiency missing for {role}"
            assert result['hourly_rate'] > 0, f"Invalid hourly rate for {role}"
            assert 0 < result['efficiency'] <= 1, f"Invalid efficiency for {role}"
        
    finally:
        # Restore original value
        resolver.__class__.HAS_POSTGRES = original_has_postgres

if __name__ == "__main__":
    pytest.main([__file__, "-v"])