import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import json
from typing import Any, Dict, List, Optional
import uuid
from faker import Faker

fake = Faker()


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
    
    # Mock embeddings
    mock_embedding_response = Mock()
    mock_embedding_response.data = [Mock()]
    mock_embedding_response.data[0].embedding = [0.1, 0.2, 0.3]
    
    mock_openai.embeddings.create = AsyncMock(return_value=mock_embedding_response)
    
    return mock_openai


def create_mock_chromadb() -> Mock:
    """Create a mock ChromaDB client for testing"""
    mock_client = Mock()
    mock_collection = Mock()
    
    # Mock collection methods
    mock_collection.get.return_value = {'ids': [], 'documents': [], 'metadatas': []}
    mock_collection.query.return_value = {
        'ids': [['doc_1']],
        'documents': [['Test document content']],
        'metadatas': [[{'title': 'Test Document', 'source': 'test', 'type': 'document'}]],
        'distances': [[0.1]]
    }
    mock_collection.add = Mock()
    mock_collection.update = Mock()
    mock_collection.delete = Mock()
    
    mock_client.get_collection.return_value = mock_collection
    mock_client.create_collection.return_value = mock_collection
    mock_client.list_collections.return_value = [mock_collection]
    
    return mock_client


def create_mock_trello() -> Mock:
    """Create a mock Trello client for testing"""
    mock_trello = Mock()
    
    # Mock board operations
    mock_trello.boards.get.return_value = {
        'id': 'board_123',
        'name': 'Test Board',
        'lists': [
            {'id': 'list_1', 'name': 'To Do'},
            {'id': 'list_2', 'name': 'In Progress'}
        ]
    }
    
    # Mock card operations
    mock_trello.cards.new.return_value = {'id': 'card_123', 'name': 'Test Card'}
    mock_trello.cards.get.return_value = {'id': 'card_123', 'name': 'Test Card'}
    mock_trello.cards.update = Mock()
    
    return mock_trello


def assert_dict_contains(expected: Dict[str, Any], actual: Dict[str, Any]) -> None:
    """Assert that actual dict contains all expected key-value pairs"""
    for key, expected_value in expected.items():
        assert key in actual, f"Key '{key}' not found in actual dict"
        assert actual[key] == expected_value, f"Value for key '{key}' mismatch: expected {expected_value}, got {actual[key]}"


def assert_response_status(response, expected_status: int) -> None:
    """Assert HTTP response status code"""
    assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"


def assert_response_json(response, expected_keys: List[str]) -> Dict[str, Any]:
    """Assert response contains JSON with expected keys"""
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    for key in expected_keys:
        assert key in data, f"Key '{key}' not found in response JSON"
    return data


def assert_error_response(response, expected_status: int, expected_error: str) -> None:
    """Assert error response with specific status and error message"""
    assert_response_status(response, expected_status)
    data = response.json()
    assert "detail" in data
    assert expected_error in data["detail"]


def create_test_project_data(**overrides) -> Dict[str, Any]:
    """Create test project data"""
    base_data = {
        "name": fake.company(),
        "description": fake.text(),
        "status": "planned",
        "budget": float(fake.random_number(digits=5, fix_len=True)),
        "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
    }
    return {**base_data, **overrides}


def create_test_vendor_data(**overrides) -> Dict[str, Any]:
    """Create test vendor data"""
    base_data = {
        "name": fake.company(),
        "contact": fake.email(),
        "rating": round(fake.random.uniform(1.0, 5.0), 1),
        "specialty": fake.random.choice(['construction', 'electrical', 'plumbing', 'landscaping']),
    }
    return {**base_data, **overrides}


def create_test_material_data(**overrides) -> Dict[str, Any]:
    """Create test material data"""
    base_data = {
        "name": fake.word(),
        "description": fake.text(),
        "unit": fake.random.choice(['kg', 'm', 'unit', 'piece']),
        "unit_price": round(fake.random.uniform(1.0, 100.0), 2),
        "category": fake.random.choice(['building', 'electrical', 'plumbing', 'finishing']),
    }
    return {**base_data, **overrides}


def create_test_chat_message(**overrides) -> Dict[str, Any]:
    """Create test chat message data"""
    base_data = {
        "content": fake.text(),
        "role": fake.random.choice(['user', 'assistant']),
        "session_id": str(uuid.uuid4()),
    }
    return {**base_data, **overrides}


def create_test_quote_data(**overrides) -> Dict[str, Any]:
    """Create test quote data"""
    base_data = {
        "project_name": fake.company(),
        "client_name": fake.name(),
        "items": [
            {
                "title": fake.word(),
                "description": fake.text(),
                "quantity": float(fake.random_number(digits=2)),
                "unit": fake.random.choice(['unit', 'hour', 'day', 'm']),
                "unit_price": round(fake.random.uniform(10.0, 1000.0), 2),
                "subtotal": round(fake.random.uniform(100.0, 5000.0), 2),
            }
        ],
        "total": round(fake.random.uniform(1000.0, 10000.0), 2),
        "currency": fake.random.choice(['USD', 'EUR', 'GBP', 'NIS']),
    }
    return {**base_data, **overrides}


def create_test_user_data(**overrides) -> Dict[str, Any]:
    """Create test user data"""
    base_data = {
        "username": fake.user_name(),
        "email": fake.email(),
        "password": fake.password(),
        "full_name": fake.name(),
    }
    return {**base_data, **overrides}


def assert_pagination_response(response, expected_total: int) -> None:
    """Assert pagination response structure"""
    data = assert_response_json(response, ["items", "total", "page", "size"])
    assert isinstance(data["items"], list)
    assert data["total"] == expected_total
    assert data["page"] >= 1
    assert data["size"] >= 1


def assert_created_response(response, expected_type: str) -> Dict[str, Any]:
    """Assert created response structure"""
    assert_response_status(response, 201)
    data = assert_response_json(response, ["id", "message"])
    assert data["id"] is not None
    assert expected_type.lower() in data["message"].lower()
    return data


def assert_updated_response(response) -> Dict[str, Any]:
    """Assert updated response structure"""
    assert_response_status(response, 200)
    data = assert_response_json(response, ["success", "message"])
    assert data["success"] is True
    return data


def assert_deleted_response(response) -> Dict[str, Any]:
    """Assert deleted response structure"""
    assert_response_status(response, 200)
    data = assert_response_json(response, ["success", "message"])
    assert data["success"] is True
    return data


def mock_redis_client() -> Mock:
    """Create mock Redis client"""
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=1)
    mock_redis.exists = Mock(return_value=0)
    mock_redis.expire = Mock(return_value=True)
    return mock_redis


def mock_celery_app() -> Mock:
    """Create mock Celery app"""
    mock_celery = Mock()
    mock_celery.send_task = Mock(return_value=Mock())
    return mock_celery


def generate_test_document() -> Dict[str, Any]:
    """Generate test document for RAG testing"""
    return {
        "id": str(uuid.uuid4()),
        "content": fake.text(max_nb_chars=500),
        "title": fake.sentence(),
        "source": fake.domain_name(),
        "type": fake.random.choice(['document', 'article', 'manual', 'guide']),
        "metadata": {
            "author": fake.name(),
            "created_at": fake.date_time_this_year().isoformat(),
            "language": "en",
        }
    }


def assert_rag_response(response) -> Dict[str, Any]:
    """Assert RAG response structure"""
    data = assert_response_json(response, ["results", "query", "total_results"])
    assert isinstance(data["results"], list)
    assert data["query"] is not None
    assert data["total_results"] >= 0
    return data