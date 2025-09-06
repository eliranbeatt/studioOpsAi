"""Comprehensive tests for observability service with Langfuse integration"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import os
import uuid

from services.observability_service import ObservabilityService, observability_service

def test_observability_service_initialization():
    """Test ObservabilityService initialization"""
    service = ObservabilityService()
    
    # Should be initialized but disabled without proper credentials
    assert service.enabled is False
    assert service.langfuse is None

def test_initialize_langfuse_with_credentials():
    """Test Langfuse initialization with proper credentials"""
    service = ObservabilityService()
    
    with patch.dict(os.environ, {
        'LANGFUSE_PUBLIC_KEY': 'test_public_key',
        'LANGFUSE_SECRET_KEY': 'test_secret_key',
        'LANGFUSE_HOST': 'http://localhost:3000'
    }):
        with patch('services.observability_service.Langfuse') as mock_langfuse:
            mock_instance = Mock()
            mock_langfuse.return_value = mock_instance
            
            result = service._initialize_langfuse()
            
            assert result is mock_instance
            mock_langfuse.assert_called_once_with(
                public_key='test_public_key',
                secret_key='test_secret_key',
                host='http://localhost:3000'
            )

def test_initialize_langfuse_without_credentials():
    """Test Langfuse initialization without credentials"""
    service = ObservabilityService()
    
    # Clear any existing environment variables
    with patch.dict(os.environ, {}, clear=True):
        with patch('services.observability_service.logger') as mock_logger:
            result = service._initialize_langfuse()
            
            assert result is None
            mock_logger.warning.assert_called_once_with(
                "Langfuse credentials not found. Observability will be disabled."
            )

def test_initialize_langfuse_with_error():
    """Test Langfuse initialization with error"""
    service = ObservabilityService()
    
    with patch.dict(os.environ, {
        'LANGFUSE_PUBLIC_KEY': 'test_public_key',
        'LANGFUSE_SECRET_KEY': 'test_secret_key'
    }):
        with patch('services.observability_service.Langfuse', side_effect=Exception("Connection error")):
            with patch('services.observability_service.logger') as mock_logger:
                result = service._initialize_langfuse()
                
                assert result is None
                mock_logger.error.assert_called_once_with(
                    "Failed to initialize Langfuse: Connection error"
                )

def test_create_trace_disabled():
    """Test trace creation when service is disabled"""
    service = ObservabilityService()
    service.enabled = False
    
    result = service.create_trace("test_trace", "user123", "session456", {"key": "value"})
    
    assert result is None

def test_create_trace_enabled():
    """Test trace creation when service is enabled"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    service.langfuse.create_trace_id.return_value = "trace_123"
    
    result = service.create_trace(
        name="test_trace",
        user_id="user123",
        session_id="session456",
        metadata={"key": "value"}
    )
    
    assert result == "trace_123"
    service.langfuse.update_current_trace.assert_called_once_with(
        name="test_trace",
        user_id="user123",
        session_id="session456",
        metadata={"key": "value"}
    )

def test_create_trace_with_error():
    """Test trace creation with error"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    service.langfuse.create_trace_id.side_effect = Exception("Trace error")
    
    with patch('services.observability_service.logger') as mock_logger:
        result = service.create_trace("test_trace")
        
        assert result is None
        mock_logger.error.assert_called_once_with("Failed to create trace: Trace error")

def test_create_span_disabled():
    """Test span creation when service is disabled"""
    service = ObservabilityService()
    service.enabled = False
    
    result = service.create_span("trace_123", "test_span", {"key": "value"})
    
    assert result is None

def test_create_span_enabled():
    """Test span creation when service is enabled"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    mock_span = Mock()
    mock_span.id = "span_456"
    service.langfuse.start_span.return_value = mock_span
    
    start_time = datetime.now(timezone.utc)
    end_time = datetime.now(timezone.utc)
    
    result = service.create_span(
        trace_id="trace_123",
        name="test_span",
        metadata={"key": "value"},
        start_time=start_time,
        end_time=end_time
    )
    
    assert result == "span_456"
    service.langfuse.start_span.assert_called_once_with(
        name="test_span",
        metadata={"key": "value"},
        start_time=start_time,
        end_time=end_time
    )

def test_create_span_with_error():
    """Test span creation with error"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    service.langfuse.start_span.side_effect = Exception("Span error")
    
    with patch('services.observability_service.logger') as mock_logger:
        result = service.create_span("trace_123", "test_span")
        
        assert result is None
        mock_logger.error.assert_called_once_with("Failed to create span: Span error")

def test_create_generation_disabled():
    """Test generation creation when service is disabled"""
    service = ObservabilityService()
    service.enabled = False
    
    result = service.create_generation(
        trace_id="trace_123",
        name="test_generation",
        input={"prompt": "test"},
        output={"response": "test response"},
        metadata={"key": "value"},
        model="gpt-4",
        model_parameters={"temperature": 0.7}
    )
    
    assert result is None

def test_create_generation_enabled():
    """Test generation creation when service is enabled"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    mock_generation = Mock()
    mock_generation.id = "gen_789"
    service.langfuse.start_generation.return_value = mock_generation
    
    result = service.create_generation(
        trace_id="trace_123",
        name="test_generation",
        input={"prompt": "test"},
        output={"response": "test response"},
        metadata={"key": "value"},
        model="gpt-4",
        model_parameters={"temperature": 0.7}
    )
    
    assert result == "gen_789"
    service.langfuse.start_generation.assert_called_once_with(
        name="test_generation",
        input={"prompt": "test"},
        output={"response": "test response"},
        metadata={"key": "value"},
        model="gpt-4",
        model_parameters={"temperature": 0.7}
    )

def test_create_generation_with_error():
    """Test generation creation with error"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    service.langfuse.start_generation.side_effect = Exception("Generation error")
    
    with patch('services.observability_service.logger') as mock_logger:
        result = service.create_generation(
            trace_id="trace_123",
            name="test_generation",
            input={"prompt": "test"},
            output={"response": "test response"}
        )
        
        assert result is None
        mock_logger.error.assert_called_once_with("Failed to create generation: Generation error")

def test_create_event_disabled():
    """Test event creation when service is disabled"""
    service = ObservabilityService()
    service.enabled = False
    
    result = service.create_event("trace_123", "test_event", {"key": "value"})
    
    assert result is None

def test_create_event_enabled():
    """Test event creation when service is enabled"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    mock_event = Mock()
    mock_event.id = "event_101"
    service.langfuse.create_event.return_value = mock_event
    
    result = service.create_event(
        trace_id="trace_123",
        name="test_event",
        metadata={"key": "value"}
    )
    
    assert result == "event_101"
    service.langfuse.create_event.assert_called_once_with(
        name="test_event",
        metadata={"key": "value"}
    )

def test_create_event_with_error():
    """Test event creation with error"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    service.langfuse.create_event.side_effect = Exception("Event error")
    
    with patch('services.observability_service.logger') as mock_logger:
        result = service.create_event("trace_123", "test_event")
        
        assert result is None
        mock_logger.error.assert_called_once_with("Failed to create event: Event error")

def test_track_estimation_disabled():
    """Test estimation tracking when service is disabled"""
    service = ObservabilityService()
    service.enabled = False
    
    result = service.track_estimation(
        trace_id="trace_123",
        estimation_type="shipping",
        request={"distance": 100},
        response={"cost": 50},
        confidence=0.8,
        duration_ms=150.5
    )
    
    assert result is None

def test_track_estimation_enabled():
    """Test estimation tracking when service is enabled"""
    service = ObservabilityService()
    service.enabled = True
    
    with patch.object(service, 'create_span') as mock_create_span:
        mock_create_span.return_value = "span_202"
        
        result = service.track_estimation(
            trace_id="trace_123",
            estimation_type="shipping",
            request={"distance": 100},
            response={"cost": 50},
            confidence=0.8,
            duration_ms=150.5
        )
        
        assert result == "span_202"
        mock_create_span.assert_called_once_with(
            trace_id="trace_123",
            name="shipping_estimation",
            metadata={
                'estimation_type': 'shipping',
                'request': {"distance": 100},
                'response': {"cost": 50},
                'confidence': 0.8,
                'duration_ms': 150.5
            }
        )

def test_track_project_operation_disabled():
    """Test project operation tracking when service is disabled"""
    service = ObservabilityService()
    service.enabled = False
    
    project_id = uuid.uuid4()
    result = service.track_project_operation(
        trace_id="trace_123",
        operation_type="create",
        project_id=project_id,
        user_id="user123",
        metadata={"key": "value"}
    )
    
    assert result is None

def test_track_project_operation_enabled():
    """Test project operation tracking when service is enabled"""
    service = ObservabilityService()
    service.enabled = True
    
    project_id = uuid.uuid4()
    with patch.object(service, 'create_span') as mock_create_span:
        mock_create_span.return_value = "span_303"
        
        result = service.track_project_operation(
            trace_id="trace_123",
            operation_type="create",
            project_id=project_id,
            user_id="user123",
            metadata={"key": "value"}
        )
        
        assert result == "span_303"
        mock_create_span.assert_called_once_with(
            trace_id="trace_123",
            name="project_create",
            metadata={
                'operation_type': 'create',
                'project_id': str(project_id),
                'user_id': 'user123',
                'key': 'value'
            }
        )

def test_track_error_disabled():
    """Test error tracking when service is disabled"""
    service = ObservabilityService()
    service.enabled = False
    
    result = service.track_error(
        trace_id="trace_123",
        error_type="ValueError",
        error_message="Invalid value",
        stack_trace="traceback...",
        context={"param": "test"}
    )
    
    assert result is None

def test_track_error_enabled():
    """Test error tracking when service is enabled"""
    service = ObservabilityService()
    service.enabled = True
    
    with patch.object(service, 'create_event') as mock_create_event:
        mock_create_event.return_value = "event_404"
        
        result = service.track_error(
            trace_id="trace_123",
            error_type="ValueError",
            error_message="Invalid value",
            stack_trace="traceback...",
            context={"param": "test"}
        )
        
        assert result == "event_404"
        mock_create_event.assert_called_once_with(
            trace_id="trace_123",
            name="error_occurred",
            metadata={
                'error_type': 'ValueError',
                'error_message': 'Invalid value',
                'stack_trace': 'traceback...',
                'context': {"param": "test"}
            }
        )

def test_get_current_trace_id_disabled():
    """Test getting current trace ID when service is disabled"""
    service = ObservabilityService()
    service.enabled = False
    
    result = service.get_current_trace_id()
    
    assert result is None

def test_get_current_trace_id_enabled():
    """Test getting current trace ID when service is enabled"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    mock_trace = Mock()
    mock_trace.id = "trace_505"
    service.langfuse.get_current_trace.return_value = mock_trace
    
    result = service.get_current_trace_id()
    
    assert result == "trace_505"
    service.langfuse.get_current_trace.assert_called_once()

def test_get_current_trace_id_no_current_trace():
    """Test getting current trace ID when no current trace exists"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    service.langfuse.get_current_trace.return_value = None
    
    result = service.get_current_trace_id()
    
    assert result is None

def test_get_current_trace_id_with_error():
    """Test getting current trace ID with error"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    service.langfuse.get_current_trace.side_effect = Exception("Trace error")
    
    with patch('services.observability_service.logger') as mock_logger:
        result = service.get_current_trace_id()
        
        assert result is None
        mock_logger.error.assert_called_once_with("Failed to get current trace ID: Trace error")

def test_flush_disabled():
    """Test flush when service is disabled"""
    service = ObservabilityService()
    service.enabled = False
    
    # Should not raise any errors
    service.flush()

def test_flush_enabled():
    """Test flush when service is enabled"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    
    service.flush()
    
    service.langfuse.flush.assert_called_once()

def test_flush_with_error():
    """Test flush with error"""
    service = ObservabilityService()
    service.enabled = True
    service.langfuse = Mock()
    service.langfuse.flush.side_effect = Exception("Flush error")
    
    with patch('services.observability_service.logger') as mock_logger:
        service.flush()
        
        mock_logger.error.assert_called_once_with("Failed to flush Langfuse events: Flush error")

def test_global_instance():
    """Test global observability service instance"""
    assert observability_service is not None
    assert isinstance(observability_service, ObservabilityService)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])