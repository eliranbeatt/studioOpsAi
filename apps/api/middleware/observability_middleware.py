"""FastAPI middleware for automatic observability and tracing"""

import time
from typing import Callable
from uuid import uuid4
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..services.observability_service import observability_service

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic request tracing and observability"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not observability_service.enabled:
            return await call_next(request)
        
        # Generate trace ID
        trace_id = str(uuid4())
        
        # Extract user info from request (if available)
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = str(request.state.user.id)
        
        # Create trace for this request
        observability_service.create_trace(
            name=f"{request.method} {request.url.path}",
            user_id=user_id,
            session_id=request.headers.get('x-session-id'),
            metadata={
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'headers': {k: v for k, v in request.headers.items() 
                          if k.lower() not in ['authorization', 'cookie']}
            }
        )
        
        # Store trace ID in request state
        request.state.trace_id = trace_id
        
        # Measure request processing time
        start_time = time.time()
        
        try:
            response = await call_next(request)
            processing_time = (time.time() - start_time) * 1000  # ms
            
            # Track successful request
            observability_service.create_span(
                trace_id=trace_id,
                name="request_processing",
                metadata={
                    'status_code': response.status_code,
                    'processing_time_ms': processing_time,
                    'response_headers': dict(response.headers)
                }
            )
            
            return response
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000  # ms
            
            # Track error
            observability_service.track_error(
                trace_id=trace_id,
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    'processing_time_ms': processing_time,
                    'method': request.method,
                    'path': request.url.path
                }
            )
            
            raise
        
        finally:
            # Ensure events are flushed
            observability_service.flush()

class ObservableAPIRoute(APIRoute):
    """Custom APIRoute that automatically adds observability to endpoint handlers"""
    
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request) -> Response:
            if not observability_service.enabled:
                return await original_route_handler(request)
            
            trace_id = getattr(request.state, 'trace_id', None)
            if not trace_id:
                return await original_route_handler(request)
            
            # Extract operation context
            operation_name = f"{self.methods} {self.path}"
            
            # Track endpoint execution
            span_id = observability_service.create_span(
                trace_id=trace_id,
                name=operation_name,
                metadata={
                    'endpoint': self.name,
                    'path_params': request.path_params,
                    'route_path': self.path
                }
            )
            
            try:
                response = await original_route_handler(request)
                
                # Update span with response info
                if span_id:
                    observability_service.create_span(
                        trace_id=trace_id,
                        name=operation_name,
                        metadata={
                            'status_code': response.status_code,
                            'endpoint': self.name,
                            'completed': True
                        }
                    )
                
                return response
                
            except Exception as e:
                # Track endpoint error
                observability_service.track_error(
                    trace_id=trace_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    context={
                        'endpoint': self.name,
                        'operation': operation_name
                    }
                )
                raise
            
        return custom_route_handler