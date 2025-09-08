"""
Comprehensive Error Logging Service

This service provides structured error logging with correlation IDs,
context information, and integration with observability systems.
"""

import logging
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from services.observability_service import observability_service

class LogLevel(str, Enum):
    """Log levels for error categorization"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class ErrorContext:
    """Error context information"""
    correlation_id: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

@dataclass
class ErrorDetails:
    """Detailed error information"""
    error_code: str
    error_type: str
    message: str
    category: str
    severity: str
    stack_trace: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class ErrorLogEntry:
    """Complete error log entry"""
    context: ErrorContext
    details: ErrorDetails
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None
    recovery_actions: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "context": asdict(self.context),
            "details": asdict(self.details),
            "recovery_attempted": self.recovery_attempted,
            "recovery_successful": self.recovery_successful,
            "recovery_actions": self.recovery_actions
        }

class ErrorLoggingService:
    """Comprehensive error logging service"""
    
    def __init__(self):
        self.logger = logging.getLogger("studioops.errors")
        self.setup_logger()
        self._current_context: Optional[ErrorContext] = None
    
    def setup_logger(self):
        """Setup structured logging configuration"""
        # Create formatter for structured logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Ensure handler exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.setLevel(logging.INFO)
    
    @contextmanager
    def error_context(self, context: ErrorContext):
        """Context manager for setting error context"""
        previous_context = self._current_context
        self._current_context = context
        try:
            yield context
        finally:
            self._current_context = previous_context
    
    def log_error(
        self,
        error_code: str,
        error_type: str,
        message: str,
        category: str,
        severity: str,
        exception: Optional[Exception] = None,
        context: Optional[ErrorContext] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        recovery_attempted: bool = False,
        recovery_successful: Optional[bool] = None,
        recovery_actions: Optional[List[str]] = None
    ) -> str:
        """
        Log an error with comprehensive details
        
        Returns:
            correlation_id: Unique identifier for this error occurrence
        """
        
        # Use provided context or current context or create new one
        if context is None:
            context = self._current_context or ErrorContext(
                correlation_id=str(uuid.uuid4())
            )
        
        # Extract stack trace if exception provided
        stack_trace = None
        if exception:
            import traceback
            stack_trace = traceback.format_exc()
        
        # Create error details
        details = ErrorDetails(
            error_code=error_code,
            error_type=error_type,
            message=message,
            category=category,
            severity=severity,
            stack_trace=stack_trace,
            additional_data=additional_data
        )
        
        # Create complete log entry
        log_entry = ErrorLogEntry(
            context=context,
            details=details,
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful,
            recovery_actions=recovery_actions
        )
        
        # Log to standard logger
        self._log_to_standard_logger(log_entry)
        
        # Log to observability system if available
        self._log_to_observability(log_entry)
        
        # Store for analytics (could be database, metrics system, etc.)
        self._store_error_analytics(log_entry)
        
        return context.correlation_id
    
    def log_validation_error(
        self,
        field_errors: List[Dict[str, Any]],
        context: Optional[ErrorContext] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log validation errors with field details"""
        
        return self.log_error(
            error_code="VALIDATION_ERROR",
            error_type="ValidationError",
            message=f"Validation failed for {len(field_errors)} fields",
            category="validation",
            severity="medium",
            context=context,
            additional_data={
                "field_errors": field_errors,
                **(additional_data or {})
            }
        )
    
    def log_database_error(
        self,
        operation: str,
        exception: Exception,
        context: Optional[ErrorContext] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log database-related errors"""
        
        return self.log_error(
            error_code="DATABASE_ERROR",
            error_type=type(exception).__name__,
            message=f"Database error during {operation}: {str(exception)}",
            category="database",
            severity="high",
            exception=exception,
            context=context,
            additional_data={
                "operation": operation,
                **(additional_data or {})
            }
        )
    
    def log_external_service_error(
        self,
        service_name: str,
        operation: str,
        exception: Optional[Exception] = None,
        context: Optional[ErrorContext] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        recovery_attempted: bool = False,
        recovery_successful: Optional[bool] = None
    ) -> str:
        """Log external service errors"""
        
        return self.log_error(
            error_code="EXTERNAL_SERVICE_ERROR",
            error_type=type(exception).__name__ if exception else "ServiceError",
            message=f"External service error - {service_name} during {operation}",
            category="external_service",
            severity="medium",
            exception=exception,
            context=context,
            additional_data={
                "service_name": service_name,
                "operation": operation,
                **(additional_data or {})
            },
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful
        )
    
    def log_file_operation_error(
        self,
        operation: str,
        filename: str,
        exception: Exception,
        context: Optional[ErrorContext] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log file operation errors"""
        
        return self.log_error(
            error_code="FILE_OPERATION_ERROR",
            error_type=type(exception).__name__,
            message=f"File operation error during {operation} of {filename}",
            category="file_operation",
            severity="medium",
            exception=exception,
            context=context,
            additional_data={
                "operation": operation,
                "filename": filename,
                **(additional_data or {})
            }
        )
    
    def log_authentication_error(
        self,
        reason: str,
        context: Optional[ErrorContext] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log authentication errors"""
        
        return self.log_error(
            error_code="AUTHENTICATION_ERROR",
            error_type="AuthenticationError",
            message=f"Authentication failed: {reason}",
            category="authentication",
            severity="medium",
            context=context,
            additional_data={
                "reason": reason,
                **(additional_data or {})
            }
        )
    
    def _log_to_standard_logger(self, log_entry: ErrorLogEntry):
        """Log to standard Python logger"""
        
        # Determine log level based on severity
        severity_to_level = {
            "low": logging.INFO,
            "medium": logging.WARNING,
            "high": logging.ERROR,
            "critical": logging.CRITICAL
        }
        
        level = severity_to_level.get(log_entry.details.severity, logging.ERROR)
        
        # Create structured log message
        log_data = {
            "correlation_id": log_entry.context.correlation_id,
            "error_code": log_entry.details.error_code,
            "category": log_entry.details.category,
            "error_message": log_entry.details.message  # Renamed to avoid conflict
        }
        
        if log_entry.context.endpoint:
            log_data["endpoint"] = log_entry.context.endpoint
        
        if log_entry.context.user_id:
            log_data["user_id"] = log_entry.context.user_id
        
        # Log with structured data
        self.logger.log(
            level,
            f"Error occurred: {log_entry.details.message}",
            extra=log_data
        )
    
    def _log_to_observability(self, log_entry: ErrorLogEntry):
        """Log to observability system (Langfuse)"""
        
        if not observability_service.enabled:
            return
        
        try:
            # Create observability event
            observability_service.trace_error(
                name=f"error_{log_entry.details.error_code.lower()}",
                error_code=log_entry.details.error_code,
                error_message=log_entry.details.message,
                correlation_id=log_entry.context.correlation_id,
                metadata={
                    "category": log_entry.details.category,
                    "severity": log_entry.details.severity,
                    "error_type": log_entry.details.error_type,
                    "endpoint": log_entry.context.endpoint,
                    "method": log_entry.context.method,
                    "user_id": log_entry.context.user_id,
                    "recovery_attempted": log_entry.recovery_attempted,
                    "recovery_successful": log_entry.recovery_successful,
                    **(log_entry.details.additional_data or {})
                }
            )
        except Exception as e:
            # Don't let observability errors break the main flow
            self.logger.warning(f"Failed to log to observability system: {e}")
    
    def _store_error_analytics(self, log_entry: ErrorLogEntry):
        """Store error data for analytics (could be database, metrics, etc.)"""
        
        # For now, just log to a separate analytics logger
        analytics_logger = logging.getLogger("studioops.analytics.errors")
        
        try:
            analytics_data = {
                "timestamp": log_entry.context.timestamp.isoformat(),
                "correlation_id": log_entry.context.correlation_id,
                "error_code": log_entry.details.error_code,
                "category": log_entry.details.category,
                "severity": log_entry.details.severity,
                "endpoint": log_entry.context.endpoint,
                "method": log_entry.context.method,
                "user_id": log_entry.context.user_id,
                "recovery_attempted": log_entry.recovery_attempted,
                "recovery_successful": log_entry.recovery_successful
            }
            
            analytics_logger.info(
                "Error analytics",
                extra={"analytics_data": json.dumps(analytics_data)}
            )
        except Exception as e:
            # Don't let analytics errors break the main flow
            self.logger.warning(f"Failed to store error analytics: {e}")
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period"""
        
        # This would typically query a database or metrics system
        # For now, return a placeholder structure
        return {
            "time_period_hours": hours,
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "most_common_errors": [],
            "recovery_success_rate": 0.0,
            "note": "Error statistics not yet implemented - would require database storage"
        }

# Global instance
error_logging_service = ErrorLoggingService()

def create_error_context(
    correlation_id: str = None,
    request_id: str = None,
    user_id: str = None,
    session_id: str = None,
    endpoint: str = None,
    method: str = None,
    ip_address: str = None,
    user_agent: str = None
) -> ErrorContext:
    """Helper function to create error context"""
    
    return ErrorContext(
        correlation_id=correlation_id or str(uuid.uuid4()),
        request_id=request_id,
        user_id=user_id,
        session_id=session_id,
        endpoint=endpoint,
        method=method,
        ip_address=ip_address,
        user_agent=user_agent
    )