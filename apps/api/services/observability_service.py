"""Observability service with Langfuse integration for tracing and monitoring"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import json

from langfuse import Langfuse
from langfuse.model import CreateTrace, CreateSpan, CreateGeneration, CreateEvent
from langfuse.decorators import observe, langfuse_context

logger = logging.getLogger(__name__)

class ObservabilityService:
    """Service for observability and monitoring with Langfuse"""
    
    def __init__(self):
        self.langfuse = self._initialize_langfuse()
        self.enabled = self.langfuse is not None
        
    def _initialize_langfuse(self) -> Optional[Langfuse]:
        """Initialize Langfuse client with environment variables"""
        try:
            public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
            secret_key = os.getenv('LANGFUSE_SECRET_KEY')
            host = os.getenv('LANGFUSE_HOST', 'http://localhost:3000')
            
            if not public_key or not secret_key:
                logger.warning("Langfuse credentials not found. Observability will be disabled.")
                return None
                
            return Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}")
            return None
    
    def create_trace(self, 
                    name: str, 
                    user_id: Optional[str] = None,
                    session_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a new trace for tracking operations"""
        if not self.enabled:
            return None
            
        try:
            trace = self.langfuse.trace(CreateTrace(
                name=name,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {}
            ))
            return trace.id
        except Exception as e:
            logger.error(f"Failed to create trace: {e}")
            return None
    
    def create_span(self, 
                   trace_id: str,
                   name: str,
                   metadata: Optional[Dict[str, Any]] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> Optional[str]:
        """Create a span within a trace"""
        if not self.enabled:
            return None
            
        try:
            span = self.langfuse.span(CreateSpan(
                trace_id=trace_id,
                name=name,
                metadata=metadata or {},
                start_time=start_time,
                end_time=end_time
            ))
            return span.id
        except Exception as e:
            logger.error(f"Failed to create span: {e}")
            return None
    
    def create_generation(self,
                         trace_id: str,
                         name: str,
                         input: Any,
                         output: Any,
                         metadata: Optional[Dict[str, Any]] = None,
                         model: Optional[str] = None,
                         model_parameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a generation event for LLM calls"""
        if not self.enabled:
            return None
            
        try:
            generation = self.langfuse.generation(CreateGeneration(
                trace_id=trace_id,
                name=name,
                input=input,
                output=output,
                metadata=metadata or {},
                model=model,
                model_parameters=model_parameters or {}
            ))
            return generation.id
        except Exception as e:
            logger.error(f"Failed to create generation: {e}")
            return None
    
    def create_event(self,
                    trace_id: str,
                    name: str,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a custom event"""
        if not self.enabled:
            return None
            
        try:
            event = self.langfuse.event(CreateEvent(
                trace_id=trace_id,
                name=name,
                metadata=metadata or {}
            ))
            return event.id
        except Exception as e:
            logger.error(f"Failed to create event: {e}")
            return None
    
    def track_estimation(self,
                        trace_id: str,
                        estimation_type: str,
                        request: Dict[str, Any],
                        response: Dict[str, Any],
                        confidence: float,
                        duration_ms: float) -> Optional[str]:
        """Track estimation operations"""
        if not self.enabled:
            return None
            
        metadata = {
            'estimation_type': estimation_type,
            'request': request,
            'response': response,
            'confidence': confidence,
            'duration_ms': duration_ms
        }
        
        return self.create_span(
            trace_id=trace_id,
            name=f"{estimation_type}_estimation",
            metadata=metadata
        )
    
    def track_project_operation(self,
                              trace_id: str,
                              operation_type: str,
                              project_id: Optional[UUID],
                              user_id: Optional[str],
                              metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Track project-related operations"""
        if not self.enabled:
            return None
            
        op_metadata = {
            'operation_type': operation_type,
            'project_id': str(project_id) if project_id else None,
            'user_id': user_id
        }
        
        if metadata:
            op_metadata.update(metadata)
            
        return self.create_span(
            trace_id=trace_id,
            name=f"project_{operation_type}",
            metadata=op_metadata
        )
    
    def track_error(self,
                   trace_id: str,
                   error_type: str,
                   error_message: str,
                   stack_trace: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Track errors with context"""
        if not self.enabled:
            return None
            
        metadata = {
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'context': context or {}
        }
        
        return self.create_event(
            trace_id=trace_id,
            name="error_occurred",
            metadata=metadata
        )
    
    def flush(self):
        """Flush any pending events to Langfuse"""
        if self.enabled:
            try:
                self.langfuse.flush()
            except Exception as e:
                logger.error(f"Failed to flush Langfuse events: {e}")

# Global instance
observability_service = ObservabilityService()