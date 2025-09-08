"""
Comprehensive Error Handling System for StudioOps API

This module provides standardized error handling with:
- Consistent error response format
- Hebrew/English bilingual support
- Correlation IDs for tracking
- Field-level validation errors
- Recovery guidance
"""

import uuid
import logging
import traceback
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(str, Enum):
    """Error categories for better classification"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    FILE_OPERATION = "file_operation"
    SYSTEM = "system"

class FieldError(BaseModel):
    """Individual field validation error"""
    field: str = Field(..., description="Field name that has the error")
    message: str = Field(..., description="Error message for the field")
    message_he: Optional[str] = Field(None, description="Hebrew error message")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")
    value: Optional[Any] = Field(None, description="Invalid value that caused the error")

class RecoveryAction(BaseModel):
    """Suggested recovery action for the error"""
    action: str = Field(..., description="Action identifier")
    title: str = Field(..., description="Action title in English")
    title_he: Optional[str] = Field(None, description="Action title in Hebrew")
    description: str = Field(..., description="Action description in English")
    description_he: Optional[str] = Field(None, description="Action description in Hebrew")
    url: Optional[str] = Field(None, description="URL for the recovery action")

class StandardErrorResponse(BaseModel):
    """Standardized error response format"""
    success: bool = Field(False, description="Always false for errors")
    error: bool = Field(True, description="Always true for errors")
    correlation_id: str = Field(..., description="Unique correlation ID for tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    # Error details
    status_code: int = Field(..., description="HTTP status code")
    error_code: str = Field(..., description="Application-specific error code")
    category: ErrorCategory = Field(..., description="Error category")
    severity: ErrorSeverity = Field(..., description="Error severity")
    
    # Messages
    message: str = Field(..., description="Error message in English")
    message_he: Optional[str] = Field(None, description="Error message in Hebrew")
    
    # Detailed information
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    field_errors: Optional[List[FieldError]] = Field(None, description="Field-specific validation errors")
    
    # Recovery guidance
    recovery_actions: Optional[List[RecoveryAction]] = Field(None, description="Suggested recovery actions")
    
    # Technical details (only in development)
    stack_trace: Optional[str] = Field(None, description="Stack trace for debugging")
    request_id: Optional[str] = Field(None, description="Request ID for correlation")

class ErrorMessages:
    """Bilingual error messages"""
    
    # Common errors
    INTERNAL_SERVER_ERROR = {
        "en": "An internal server error occurred. Please try again later.",
        "he": "אירעה שגיאת שרת פנימית. אנא נסה שוב מאוחר יותר."
    }
    
    NOT_FOUND = {
        "en": "The requested resource was not found.",
        "he": "המשאב המבוקש לא נמצא."
    }
    
    VALIDATION_ERROR = {
        "en": "The provided data is invalid. Please check the highlighted fields.",
        "he": "הנתונים שסופקו אינם תקינים. אנא בדוק את השדות המסומנים."
    }
    
    UNAUTHORIZED = {
        "en": "Authentication is required to access this resource.",
        "he": "נדרש אימות כדי לגשת למשאב זה."
    }
    
    FORBIDDEN = {
        "en": "You don't have permission to access this resource.",
        "he": "אין לך הרשאה לגשת למשאב זה."
    }
    
    CONFLICT = {
        "en": "The request conflicts with the current state of the resource.",
        "he": "הבקשה מתנגשת עם המצב הנוכחי של המשאב."
    }
    
    # Database errors
    DATABASE_CONNECTION_ERROR = {
        "en": "Unable to connect to the database. Please try again later.",
        "he": "לא ניתן להתחבר למסד הנתונים. אנא נסה שוב מאוחר יותר."
    }
    
    DATABASE_CONSTRAINT_ERROR = {
        "en": "The operation violates database constraints.",
        "he": "הפעולה מפרה את אילוצי מסד הנתונים."
    }
    
    # File operation errors
    FILE_TOO_LARGE = {
        "en": "The uploaded file is too large. Maximum size is {max_size}MB.",
        "he": "הקובץ שהועלה גדול מדי. הגודל המקסימלי הוא {max_size}MB."
    }
    
    FILE_TYPE_NOT_ALLOWED = {
        "en": "File type not allowed. Supported types: {allowed_types}",
        "he": "סוג קובץ לא מורשה. סוגים נתמכים: {allowed_types}"
    }
    
    FILE_UPLOAD_FAILED = {
        "en": "File upload failed. Please try again.",
        "he": "העלאת הקובץ נכשלה. אנא נסה שוב."
    }
    
    # External service errors
    EXTERNAL_SERVICE_UNAVAILABLE = {
        "en": "External service is temporarily unavailable. Please try again later.",
        "he": "שירות חיצוני אינו זמין זמנית. אנא נסה שוב מאוחר יותר."
    }
    
    TRELLO_API_ERROR = {
        "en": "Trello integration is currently unavailable. Using mock data.",
        "he": "אינטגרציית Trello אינה זמינה כרגע. משתמש בנתונים מדומים."
    }
    
    AI_SERVICE_ERROR = {
        "en": "AI service is temporarily unavailable. Using enhanced responses.",
        "he": "שירות הבינה המלאכותית אינו זמין זמנית. משתמש בתגובות משופרות."
    }

class RecoveryActions:
    """Common recovery actions"""
    
    @staticmethod
    def retry_action() -> RecoveryAction:
        return RecoveryAction(
            action="retry",
            title="Try Again",
            title_he="נסה שוב",
            description="Retry the operation after a few moments",
            description_he="נסה שוב את הפעולה לאחר כמה רגעים"
        )
    
    @staticmethod
    def contact_support() -> RecoveryAction:
        return RecoveryAction(
            action="contact_support",
            title="Contact Support",
            title_he="צור קשר עם התמיכה",
            description="Contact technical support for assistance",
            description_he="צור קשר עם התמיכה הטכנית לקבלת עזרה",
            url="/support"
        )
    
    @staticmethod
    def check_connection() -> RecoveryAction:
        return RecoveryAction(
            action="check_connection",
            title="Check Connection",
            title_he="בדוק חיבור",
            description="Check your internet connection and try again",
            description_he="בדוק את החיבור לאינטרנט ונסה שוב"
        )
    
    @staticmethod
    def validate_input() -> RecoveryAction:
        return RecoveryAction(
            action="validate_input",
            title="Check Input",
            title_he="בדוק קלט",
            description="Review and correct the highlighted fields",
            description_he="בדוק ותקן את השדות המסומנים"
        )

class ErrorHandler:
    """Central error handling utility"""
    
    def __init__(self, include_stack_trace: bool = False):
        self.include_stack_trace = include_stack_trace
    
    def create_error_response(
        self,
        status_code: int,
        error_code: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        message_key: str = None,
        message_en: str = None,
        message_he: str = None,
        details: Dict[str, Any] = None,
        field_errors: List[FieldError] = None,
        recovery_actions: List[RecoveryAction] = None,
        correlation_id: str = None,
        request_id: str = None,
        exception: Exception = None,
        **message_params
    ) -> StandardErrorResponse:
        """Create a standardized error response"""
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Get message from predefined messages or use provided ones
        if message_key and hasattr(ErrorMessages, message_key):
            messages = getattr(ErrorMessages, message_key)
            message_en = messages["en"].format(**message_params) if message_params else messages["en"]
            message_he = messages["he"].format(**message_params) if message_params else messages["he"]
        
        if not message_en:
            message_en = "An error occurred"
        
        # Add stack trace in development
        stack_trace = None
        if self.include_stack_trace and exception:
            stack_trace = traceback.format_exc()
        
        # Default recovery actions based on category
        if not recovery_actions:
            recovery_actions = self._get_default_recovery_actions(category, status_code)
        
        error_response = StandardErrorResponse(
            correlation_id=correlation_id,
            status_code=status_code,
            error_code=error_code,
            category=category,
            severity=severity,
            message=message_en,
            message_he=message_he,
            details=details,
            field_errors=field_errors,
            recovery_actions=recovery_actions,
            stack_trace=stack_trace,
            request_id=request_id
        )
        
        # Log the error
        self._log_error(error_response, exception)
        
        return error_response
    
    def _get_default_recovery_actions(self, category: ErrorCategory, status_code: int) -> List[RecoveryAction]:
        """Get default recovery actions based on error category"""
        actions = []
        
        if category == ErrorCategory.VALIDATION:
            actions.append(RecoveryActions.validate_input())
        elif category == ErrorCategory.EXTERNAL_SERVICE:
            actions.extend([
                RecoveryActions.retry_action(),
                RecoveryActions.check_connection()
            ])
        elif status_code >= 500:
            actions.extend([
                RecoveryActions.retry_action(),
                RecoveryActions.contact_support()
            ])
        elif category == ErrorCategory.NOT_FOUND:
            actions.append(RecoveryActions.retry_action())
        
        return actions
    
    def _log_error(self, error_response: StandardErrorResponse, exception: Exception = None):
        """Log error with appropriate level based on severity"""
        log_data = {
            "correlation_id": error_response.correlation_id,
            "error_code": error_response.error_code,
            "category": error_response.category,
            "status_code": error_response.status_code,
            "error_message": error_response.message  # Renamed to avoid conflict
        }
        
        if error_response.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error occurred", extra=log_data, exc_info=exception)
        elif error_response.severity == ErrorSeverity.HIGH:
            logger.error("High severity error occurred", extra=log_data, exc_info=exception)
        elif error_response.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error occurred", extra=log_data)
        else:
            logger.info("Low severity error occurred", extra=log_data)

# Global error handler instance
error_handler = ErrorHandler(include_stack_trace=True)  # Set to False in production

def create_http_exception(
    status_code: int,
    error_code: str,
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    message_key: str = None,
    message_en: str = None,
    message_he: str = None,
    details: Dict[str, Any] = None,
    field_errors: List[FieldError] = None,
    recovery_actions: List[RecoveryAction] = None,
    **message_params
) -> HTTPException:
    """Create an HTTPException with standardized error response"""
    
    error_response = error_handler.create_error_response(
        status_code=status_code,
        error_code=error_code,
        category=category,
        severity=severity,
        message_key=message_key,
        message_en=message_en,
        message_he=message_he,
        details=details,
        field_errors=field_errors,
        recovery_actions=recovery_actions,
        **message_params
    )
    
    return HTTPException(
        status_code=status_code,
        detail=error_response.dict()
    )

def create_validation_error(field_errors: List[FieldError]) -> HTTPException:
    """Create a validation error with field-specific details"""
    return create_http_exception(
        status_code=422,
        error_code="VALIDATION_ERROR",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        message_key="VALIDATION_ERROR",
        field_errors=field_errors
    )

def create_not_found_error(resource_type: str = "resource") -> HTTPException:
    """Create a not found error"""
    return create_http_exception(
        status_code=404,
        error_code="NOT_FOUND",
        category=ErrorCategory.NOT_FOUND,
        severity=ErrorSeverity.LOW,
        message_key="NOT_FOUND",
        details={"resource_type": resource_type}
    )

def create_database_error(operation: str = "database operation") -> HTTPException:
    """Create a database error"""
    return create_http_exception(
        status_code=500,
        error_code="DATABASE_ERROR",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.HIGH,
        message_key="DATABASE_CONNECTION_ERROR",
        details={"operation": operation}
    )

def create_external_service_error(service_name: str) -> HTTPException:
    """Create an external service error"""
    return create_http_exception(
        status_code=503,
        error_code="EXTERNAL_SERVICE_ERROR",
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.MEDIUM,
        message_key="EXTERNAL_SERVICE_UNAVAILABLE",
        details={"service": service_name}
    )