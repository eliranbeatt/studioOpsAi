#!/usr/bin/env python3
"""
Comprehensive tests for StudioOps AI ingestion pipeline
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID

from services.ingestion_service import ingestion_service
from services.ocr_service import ocr_service
from services.unstructured_service import unstructured_service
from services.instructor_service import instructor_service


def test_ingestion_service_initialization():
    """Test that ingestion service initializes correctly"""
    assert ingestion_service is not None
    assert hasattr(ingestion_service, 'pipeline_stages')
    assert len(ingestion_service.pipeline_stages) == 7
    expected_stages = ["parse", "classify", "pack", "extract", "validate", "link", "stage"]
    assert ingestion_service.pipeline_stages == expected_stages


def test_parse_stage_with_mock_data():
    """Test parse stage with mock document data"""
    
    # Mock file path
    mock_file_path = "/fake/path/document.pdf"
    
    # Mock OCR service response
    with patch.object(ocr_service, 'process_pdf_with_ocr') as mock_ocr:
        mock_ocr.return_value = {
            'success': True,
            'output_path': '/fake/path/ocr_output.pdf',
            'languages_used': ['heb', 'eng'],
            'extracted_text_length': 1500,
            'has_hebrew_text': True
        }
        
        # Mock Unstructured service response
        with patch.object(unstructured_service, 'parse_document') as mock_parse:
            mock_parse.return_value = {
                'success': True,
                'elements_count': 25,
                'structured_data': [
                    {'text': 'Invoice Number: INV-2024-001', 'type': 'Title'},
                    {'text': 'Vendor: Home Center', 'type': 'Text'},
                    {'text': 'Date: 2024-01-15', 'type': 'Text'}
                ],
                'metadata': {'page_count': 2, 'languages_detected': ['hebrew', 'english']}
            }
            
            # Call parse stage
            result = ingestion_service._parse_stage(mock_file_path, "test-trace-123")
            
            # Assertions
            assert result['success'] == True
            assert result['elements_count'] == 25
            assert 'extracted_text' in result
            assert 'Invoice Number: INV-2024-001' in result['extracted_text']
            assert 'Vendor: Home Center' in result['extracted_text']


def test_classify_stage():
    """Test document classification stage"""
    
    test_text = """
    INVOICE
    Vendor: Home Center
    Invoice Number: INV-2024-001
    Date: January 15, 2024
    
    Item Description: Plywood 4x8
    Quantity: 5
    Unit Price: 120.00
    Total: 600.00
    """
    
    # Mock instructor service
    with patch.object(instructor_service, 'classify_text') as mock_classify:
        mock_classify.return_value = {
            'category': 'invoice',
            'confidence': 0.92,
            'reasoning': 'Document contains invoice-specific fields and structure',
            'alternatives': ['quote', 'purchase_order']
        }
        
        result = ingestion_service._classify_stage(test_text, "test-trace-123")
        
        assert result['success'] == True
        assert result['document_type'] == 'invoice'
        assert result['confidence'] == 0.92


def test_extract_all_text():
    """Test text extraction from structured data"""
    
    parse_result = {
        'success': True,
        'structured_data': [
            {'text': 'Invoice Header', 'type': 'Title'},
            {'text': 'Vendor: ABC Supplies', 'type': 'Text'},
            {'text': 'Total: $1,000.00', 'type': 'Text'}
        ]
    }
    
    extracted_text = ingestion_service._extract_all_text(parse_result)
    
    assert 'Invoice Header' in extracted_text
    assert 'Vendor: ABC Supplies' in extracted_text
    assert 'Total: $1,000.00' in extracted_text


def test_build_context_chunks():
    """Test context chunk building for RAG"""
    
    structured_data = [
        {'text': 'Section 1', 'type': 'Title'},
        {'text': 'Content for section 1 goes here.', 'type': 'Text'},
        {'text': 'More content in section 1.', 'type': 'Text'},
        {'text': 'Section 2', 'type': 'Title'},
        {'text': 'Content for section 2.', 'type': 'Text'}
    ]
    
    chunks = ingestion_service._build_context_chunks(structured_data, 'invoice')
    
    assert len(chunks) >= 2  # Should have at least 2 chunks for 2 sections
    assert any('Section 1' in chunk for chunk in chunks)
    assert any('Section 2' in chunk for chunk in chunks)


def test_get_extraction_schema():
    """Test extraction schema selection based on document type"""
    
    # Test invoice schema
    invoice_schema = ingestion_service._get_extraction_schema('invoice')
    assert invoice_schema is not None
    
    # Test quote schema
    quote_schema = ingestion_service._get_extraction_schema('quote')
    assert quote_schema is not None
    
    # Test generic schema
    generic_schema = ingestion_service._get_extraction_schema('unknown')
    assert generic_schema is not None


def test_validate_item():
    """Test item validation logic"""
    
    # Test valid item
    valid_item = {
        'title': 'Plywood 4x8',
        'qty': 5.0,
        'unit': 'sheet',
        'unit_price_nis': 120.0,
        'total_price_nis': 600.0
    }
    
    validation = ingestion_service._validate_item(valid_item)
    assert validation['is_valid'] == True
    assert len(validation['issues']) == 0
    assert validation['confidence_score'] > 0.7
    
    # Test invalid item (negative price)
    invalid_item = {
        'title': 'Plywood 4x8',
        'qty': 5.0,
        'unit': 'sheet',
        'unit_price_nis': -120.0,  # Invalid negative price
        'total_price_nis': -600.0
    }
    
    validation = ingestion_service._validate_item(invalid_item)
    assert validation['is_valid'] == False
    assert 'invalid_unit_price' in validation['issues']
    assert 'invalid_total_price' in validation['issues']
    assert validation['confidence_score'] < 0.7


def test_stage_stage():
    """Test results staging logic"""
    
    pipeline_results = {
        'extract': {
            'extracted_items': [
                {
                    'id': 'item-1',
                    'title': 'Plywood 4x8',
                    'qty': 5.0,
                    'unit': 'sheet',
                    'unit_price_nis': 120.0,
                    'total_price_nis': 600.0,
                    'confidence': 0.8
                }
            ]
        },
        'validate': {
            'validation_results': [
                {
                    'item_id': 'item-1',
                    'is_valid': True,
                    'issues': [],
                    'confidence_score': 0.85
                }
            ],
            'valid_items_count': 1,
            'total_items_count': 1,
            'validation_rate': 1.0
        },
        'link': {
            'summary': {'total_items': 1}
        }
    }
    
    result = ingestion_service._stage_stage(pipeline_results, "test-trace-123")
    
    assert result['success'] == True
    assert result['overall_confidence'] > 0.8
    assert result['requires_review'] == False
    assert result['total_items_extracted'] == 1


def test_process_document_simulation():
    """Test complete document processing simulation"""
    
    mock_file_path = "/fake/path/test.pdf"
    document_id = UUID('12345678-1234-5678-1234-567812345678')
    
    # Mock all service calls
    with patch.object(ingestion_service, '_parse_stage') as mock_parse, \
         patch.object(ingestion_service, '_classify_stage') as mock_classify, \
         patch.object(ingestion_service, '_pack_stage') as mock_pack, \
         patch.object(ingestion_service, '_extract_stage') as mock_extract, \
         patch.object(ingestion_service, '_validate_stage') as mock_validate, \
         patch.object(ingestion_service, '_link_stage') as mock_link, \
         patch.object(ingestion_service, '_stage_stage') as mock_stage:
        
        # Setup mock responses
        mock_parse.return_value = {
            'success': True,
            'elements_count': 15,
            'extracted_text': 'Invoice content with materials and prices',
            'metadata': {}
        }
        
        mock_classify.return_value = {
            'success': True,
            'document_type': 'invoice',
            'confidence': 0.9
        }
        
        mock_pack.return_value = {
            'success': True,
            'context_chunks': ['chunk1', 'chunk2']
        }
        
        mock_extract.return_value = {
            'success': True,
            'extracted_items': [
                {
                    'id': 'extracted-1',
                    'title': 'Plywood 4x8',
                    'qty': 5.0,
                    'unit': 'sheet',
                    'unit_price_nis': 120.0,
                    'total_price_nis': 600.0,
                    'confidence': 0.8
                }
            ]
        }
        
        mock_validate.return_value = {
            'success': True,
            'validation_results': [{'item_id': 'extracted-1', 'is_valid': True, 'confidence_score': 0.85}],
            'valid_items_count': 1,
            'total_items_count': 1
        }
        
        mock_link.return_value = {
            'success': True,
            'summary': {'total_items': 1}
        }
        
        mock_stage.return_value = {
            'success': True,
            'overall_confidence': 0.88,
            'requires_review': False,
            'total_items_extracted': 1
        }
        
        # Call the main processing method
        result = ingestion_service.process_document(mock_file_path, document_id)
        
        # Assertions
        assert result['success'] == True
        assert result['document_id'] == str(document_id)
        assert result['pipeline_status'] == 'completed'
        assert result['requires_review'] == False
        assert 'results' in result
        assert len(result['results']) == 7  # All 7 stages should be present


def test_hebrew_text_detection():
    """Test Hebrew text detection in parsing"""
    
    test_text = "זהו טקסט בעברית עם מספרים 123 ומחירים ₪120.00"
    
    # Test Hebrew character detection
    has_hebrew = any('֐' <= char <= '׿' for char in test_text)
    assert has_hebrew == True
    
    # Test price detection in Hebrew text
    has_prices = '₪120.00' in test_text
    assert has_prices == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])