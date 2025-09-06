"""Tests for PDF generation services"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from services.simple_pdf_service import SimplePDFService

def test_simple_pdf_service_initialization():
    """Test SimplePDFService initialization"""
    service = SimplePDFService()
    assert service.output_dir is not None
    assert os.path.exists(service.output_dir)
    assert service.font_name == 'Helvetica'

def test_generate_quote_pdf_basic():
    """Test basic quote PDF generation"""
    service = SimplePDFService()
    
    test_quote = {
        'project_name': 'Test Project',
        'client_name': 'Test Client',
        'items': [
            {
                'title': 'Test Item',
                'description': 'Test Description',
                'quantity': 1.0,
                'unit': 'unit',
                'unit_price': 10.0,
                'subtotal': 10.0
            }
        ],
        'total': 10.0,
        'currency': 'USD'
    }
    
    # Test with custom output path
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        result_path = service.generate_quote_pdf(test_quote, output_path)
        
        assert result_path == output_path
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0
        
        # Verify it's a PDF file
        with open(result_path, 'rb') as f:
            header = f.read(5)
            assert header.startswith(b'%PDF-')
            
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_generate_quote_pdf_hebrew_rtl():
    """Test Hebrew RTL quote PDF generation"""
    service = SimplePDFService()
    
    test_quote = {
        'project_name': 'פרויקט מבחן',
        'client_name': 'לקוח מבחן',
        'items': [
            {
                'title': 'עץ 2x4',
                'description': 'עץ אורן באיכות גבוהה',
                'quantity': 20.0,
                'unit': 'יחידה',
                'unit_price': 15.99,
                'subtotal': 319.80
            }
        ],
        'total': 319.80,
        'currency': 'NIS'
    }
    
    # Test with default output path
    result_path = service.generate_quote_pdf(test_quote)
    
    assert result_path is not None
    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 0
    
    # Clean up
    if os.path.exists(result_path):
        os.unlink(result_path)

def test_generate_quote_pdf_multiple_items():
    """Test PDF generation with multiple items"""
    service = SimplePDFService()
    
    test_quote = {
        'project_name': 'Multi-Item Project',
        'client_name': 'Test Client',
        'items': [
            {
                'title': 'Item 1',
                'description': 'Description 1',
                'quantity': 2.0,
                'unit': 'pcs',
                'unit_price': 5.0,
                'subtotal': 10.0
            },
            {
                'title': 'Item 2',
                'description': 'Description 2',
                'quantity': 3.0,
                'unit': 'pcs',
                'unit_price': 7.5,
                'subtotal': 22.5
            },
            {
                'title': 'Item 3',
                'description': 'Description 3',
                'quantity': 1.0,
                'unit': 'pcs',
                'unit_price': 15.0,
                'subtotal': 15.0
            }
        ],
        'total': 47.5,
        'currency': 'USD'
    }
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        result_path = service.generate_quote_pdf(test_quote, output_path)
        
        assert result_path == output_path
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_generate_quote_pdf_no_items():
    """Test PDF generation with no items"""
    service = SimplePDFService()
    
    test_quote = {
        'project_name': 'Empty Project',
        'client_name': 'Test Client',
        'items': [],
        'total': 0.0,
        'currency': 'USD'
    }
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        result_path = service.generate_quote_pdf(test_quote, output_path)
        
        assert result_path == output_path
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_generate_quote_pdf_missing_fields():
    """Test PDF generation with missing optional fields"""
    service = SimplePDFService()
    
    test_quote = {
        'project_name': 'Minimal Project',
        'client_name': 'Minimal Client',
        'items': [
            {
                'title': 'Test Item',
                'quantity': 1.0,
                'unit_price': 10.0,
                'subtotal': 10.0
            }
        ],
        'total': 10.0
        # Missing currency field
    }
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        result_path = service.generate_quote_pdf(test_quote, output_path)
        
        assert result_path == output_path
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0
        
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])