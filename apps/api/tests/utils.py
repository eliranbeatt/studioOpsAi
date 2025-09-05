import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import json
from typing import Any, Dict, List


def create_mock_langfuse() -> Mock:
    """Create a mock Langfuse client for testing"""
    mock_langfuse = Mock()
    
    # Mock trace methods
    mock_trace = Mock()
    mock_trace.span = Mock(return_value=Mock())
    mock_trace.event = Mock(return_value=Mock())
    mock_trace.update = Mock()
    
    mock_langfuse.trace = Mock(return_value=mock_trace)
    
    # Mock direct span creation
    mock_span = Mock()
    mock_span.end = Mock()
    mock_span.update = Mock()
    
    mock_langfuse.span = Mock(return_value=mock_span)
    
    # Mock event creation
    mock_event = Mock()
    mock_event.end = Mock()
    
    mock_langfuse.event = Mock(return_value=mock_event)
    
    return mock_langfuse


def create_mock_openai() -> Mock:
    """Create a mock OpenAI client for testing"""
    mock_openai = Mock()
    
    # Mock chat completion
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Test AI response"
    
    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)
    
    return mock_openai


def assert_dict_contains(expected: Dict[str, Any], actual: Dict[str, Any]) -> None:
    """Assert that actual dict contains all expected key-value pairs"""
    for key, expected_value in expected.items():
        assert key in actual, f"Key '{key}' not found in actual dict"
        assert actual[key] == expected_value, f"Value for key '{key}' mismatch: expected {expected_value}, got {actual[key]}"


def assert_response_status(response, expected_status: int) -> None:
    """Assert HTTP response status code"""
    assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"


def assert_response_json(response, expected_keys: List[str]) -> None:
    """Assert response contains JSON with expected keys"""
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    for key in expected_keys:
        assert key in data, f"Key '{key}' not found in response JSON"
    return data


def create_test_project_data() -> Dict[str, Any]:
    """Create test project data"""
    return {
        "name": "Test Project",
        "description": "Test project description",
        "status": "planned",
        "budget": 10000.0,
        "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
    }


def create_test_vendor_data() -> Dict[str, Any]:
    """Create test vendor data"""
    return {
        "name": "Test Vendor",
        "contact": "test@vendor.com",
        "rating": 4.5,
        "specialty": "construction",
    }


def create_test_material_data() -> Dict[str, Any]:
    """Create test material data"""
    return {
        "name": "Test Material",
        "description": "Test material description",
        "unit": "kg",
        "unit_price": 25.99,
        "category": "building",
    }