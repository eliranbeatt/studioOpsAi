"""
Global Error Handling Middleware

This middleware catches all unhandled exceptions and converts them to
standardized error responses with proper logging and correlation IDs.
"""

import uuid
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.error_handling import (
    ErrorHandler, ErrorCategory, ErrorSeverity, FieldError,
    StandardErrorResponse, create_validation_error
)
from services.error_logging_service import (
    error_logging_service, create_error_context, ErrorContext
)

logger = logging.getLogger(__name__)

class GlobalErrorMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    def __init__(self, app, include_stack_trace: bool = False):
        super().__init__(app)
        self.error_handler = ErrorHandler(include_stack_trace=include_stack_trace)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any exceptions"""
        
        # Generate correlation ID for this request
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Create error context for this request
        error_context = create_error_context(
            correlation_id=correlation_id,
            endpoint=request.url.path,
            method=request.method,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        # Set error context for logging
        with error_logging_service.error_context(error_context):
            try:
                response = await call_next(request)
                return response
                
            except HTTPException as e:
                # Handle FastAPI HTTPExceptions
                return await self._handle_http_exception(e, error_context, request)
                
            except RequestValidationError as e:
                # Handle Pydantic validation errors
                return await self._handle_validation_error(e, error_context, request)
                
            except IntegrityError as e:
                # Handle database integrity errors
                return await self._handle_database_integrity_error(e, error_context, request)
                
            except OperationalError as e:
                # Handle database operational errors
                return await self._handle_database_operational_error(e, error_context, request)
                
            except Exception as e:
                # Handle all other unexpected exceptions
                return await self._handle_unexpected_error(e, error_context, request)
    
    async def _handle_http_exception(
        self, 
        exception: HTTPException, 
        error_context: ErrorContext, 
        request: Request
    ) -> JSONResponse:
        """Handle FastAPI HTTPException"""
        
        # Check if the detail is already a standardized error response
        if isinstance(exception.detail, dict) and "correlation_id" in exception.detail:
            # Already standardized, just return it
            return JSONResponse(
                status_code=exception.status_code,
                content=exception.detail
            )
        
        # Convert to standardized format
        category = self._determine_category_from_status(exception.status_code)
        severity = self._determine_severity_from_status(exception.status_code)
        
        # Log the error
        error_logging_service.log_error(
            error_code=f"HTTP_{exception.status_code}",
            error_type="HTTPException",
            message=str(exception.detail),
            category=category.value,
            severity=severity.value,
            context=error_context
        )
        
        error_response = self.error_handler.create_error_response(
            status_code=exception.status_code,
            error_code=f"HTTP_{exception.status_code}",
            category=category,
            severity=severity,
            message_en=str(exception.detail),
            correlation_id=error_context.correlation_id,
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return JSONResponse(
            status_code=exception.status_code,
            content=error_response.dict()
        )
    
    async def _handle_validation_error(
        self, 
        exception: RequestValidationError, 
        error_context: ErrorContext, 
        request: Request
    ) -> JSONResponse:
        """Handle Pydantic validation errors"""
        
        field_errors = []
        for error in exception.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            field_errors.append(FieldError(
                field=field_path,
                message=error["msg"],
                message_he=self._translate_validation_error(error["msg"]),
                code=error["type"],
                value=error.get("input")
            ))
        
        # Log validation error
        error_logging_service.log_validation_error(
            field_errors=[fe.dict() for fe in field_errors],
            context=error_context
        )
        
        error_response = self.error_handler.create_error_response(
            status_code=422,
            error_code="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            message_key="VALIDATION_ERROR",
            field_errors=field_errors,
            correlation_id=error_context.correlation_id,
            request_id=getattr(request.state, 'request_id', None),
            exception=exception
        )
        
        return JSONResponse(
            status_code=422,
            content=error_response.dict()
        )
    
    async def _handle_database_integrity_error(
        self, 
        exception: IntegrityError, 
        error_context: ErrorContext, 
        request: Request
    ) -> JSONResponse:
        """Handle database integrity constraint errors"""
        
        error_message = str(exception.orig) if hasattr(exception, 'orig') else str(exception)
        
        # Try to provide more specific error messages
        if "foreign key constraint" in error_message.lower():
            message_en = "The operation violates database relationships. Please check referenced data."
            message_he = "הפעולה מפרה את קשרי מסד הנתונים. אנא בדוק את הנתונים המקושרים."
        elif "unique constraint" in error_message.lower():
            message_en = "A record with this information already exists."
            message_he = "רשומה עם מידע זה כבר קיימת."
        elif "not null constraint" in error_message.lower():
            message_en = "Required fields are missing."
            message_he = "שדות חובה חסרים."
        else:
            message_en = "The operation violates database constraints."
            message_he = "הפעולה מפרה את אילוצי מסד הנתונים."
        
        # Log database integrity error
        error_logging_service.log_database_error(
            operation="database constraint validation",
            exception=exception,
            context=error_context
        )
        
        error_response = self.error_handler.create_error_response(
            status_code=400,
            error_code="DATABASE_CONSTRAINT_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.MEDIUM,
            message_en=message_en,
            message_he=message_he,
            details={"constraint_error": error_message},
            correlation_id=error_context.correlation_id,
            request_id=getattr(request.state, 'request_id', None),
            exception=exception
        )
        
        return JSONResponse(
            status_code=400,
            content=error_response.dict()
        )
    
    async def _handle_database_operational_error(
        self, 
        exception: OperationalError, 
        error_context: ErrorContext, 
        request: Request
    ) -> JSONResponse:
        """Handle database operational errors"""
        
        # Log database operational error
        error_logging_service.log_database_error(
            operation="database connection/operation",
            exception=exception,
            context=error_context
        )
        
        error_response = self.error_handler.create_error_response(
            status_code=503,
            error_code="DATABASE_OPERATIONAL_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            message_key="DATABASE_CONNECTION_ERROR",
            details={"error": str(exception)},
            correlation_id=error_context.correlation_id,
            request_id=getattr(request.state, 'request_id', None),
            exception=exception
        )
        
        return JSONResponse(
            status_code=503,
            content=error_response.dict()
        )
    
    async def _handle_unexpected_error(
        self, 
        exception: Exception, 
        error_context: ErrorContext, 
        request: Request
    ) -> JSONResponse:
        """Handle unexpected errors"""
        
        # Log unexpected error
        error_logging_service.log_error(
            error_code="INTERNAL_SERVER_ERROR",
            error_type=type(exception).__name__,
            message=f"Unexpected error: {str(exception)}",
            category="system",
            severity="critical",
            exception=exception,
            context=error_context
        )
        
        error_response = self.error_handler.create_error_response(
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            message_key="INTERNAL_SERVER_ERROR",
            correlation_id=error_context.correlation_id,
            request_id=getattr(request.state, 'request_id', None),
            exception=exception
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )
    
    def _determine_category_from_status(self, status_code: int) -> ErrorCategory:
        """Determine error category from HTTP status code"""
        if status_code == 400:
            return ErrorCategory.VALIDATION
        elif status_code == 401:
            return ErrorCategory.AUTHENTICATION
        elif status_code == 403:
            return ErrorCategory.AUTHORIZATION
        elif status_code == 404:
            return ErrorCategory.NOT_FOUND
        elif status_code == 409:
            return ErrorCategory.CONFLICT
        elif status_code >= 500:
            return ErrorCategory.SYSTEM
        else:
            return ErrorCategory.SYSTEM
    
    def _determine_severity_from_status(self, status_code: int) -> ErrorSeverity:
        """Determine error severity from HTTP status code"""
        if status_code >= 500:
            return ErrorSeverity.HIGH
        elif status_code in [400, 401, 403, 409]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _translate_validation_error(self, error_msg: str) -> str:
        """Translate common validation error messages to Hebrew"""
        translations = {
            "field required": "שדה חובה",
            "ensure this value is greater than": "ודא שהערך גדול מ",
            "ensure this value is less than": "ודא שהערך קטן מ",
            "string too short": "מחרוזת קצרה מדי",
            "string too long": "מחרוזת ארוכה מדי",
            "invalid email format": "פורמט אימייל לא תקין",
            "value is not a valid": "הערך אינו תקין",
            "invalid uuid": "UUID לא תקין"
        }
        
        for en_msg, he_msg in translations.items():
            if en_msg in error_msg.lower():
                return he_msg
        
        return error_msg  # Return original if no translation found

# Exception handler functions for specific use cases
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException specifically"""
    middleware = GlobalErrorMiddleware(None)
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    error_context = create_error_context(
        correlation_id=correlation_id,
        endpoint=request.url.path,
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return await middleware._handle_http_exception(exc, error_context, request)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle RequestValidationError specifically"""
    middleware = GlobalErrorMiddleware(None)
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    error_context = create_error_context(
        correlation_id=correlation_id,
        endpoint=request.url.path,
        method=request.method,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return await middleware._handle_validation_error(exc, error_context, request)