"""
Test script for the comprehensive error handling system

This script tests various error scenarios to ensure the error handling
system works correctly with proper logging, correlation IDs, and
bilingual error messages.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add the apps/api directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from utils.error_handling import (
    create_http_exception, create_validation_error, create_not_found_error,
    create_database_error, create_external_service_error, FieldError,
    ErrorCategory, ErrorSeverity
)
from utils.validation import (
    ProjectValidator, DocumentValidator, UserValidator, Validator
)
from services.error_logging_service import (
    error_logging_service, create_error_context
)
from utils.error_recovery import get_recovery_guide, get_recovery_steps

def test_validation_errors():
    """Test validation error handling"""
    print("🧪 Testing Validation Errors...")
    
    # Test project validation
    invalid_project_data = {
        "name": "",  # Too short
        "client_name": "A",  # Too short
        "status": "invalid_status",  # Invalid choice
        "budget_planned": -100,  # Negative value
        "start_date": "invalid-date"  # Invalid date format
    }
    
    try:
        errors = ProjectValidator.validate_project_data(invalid_project_data)
        print(f"✅ Project validation found {len(errors)} errors:")
        for error in errors:
            print(f"   - {error.field}: {error.message} ({error.message_he})")
    except Exception as e:
        print(f"❌ Project validation test failed: {e}")
    
    # Test document validation
    try:
        errors = DocumentValidator.validate_document_upload(
            filename="test.exe",  # Invalid file type
            file_size=15 * 1024 * 1024,  # Too large (15MB)
            mime_type="application/x-executable"
        )
        print(f"✅ Document validation found {len(errors)} errors:")
        for error in errors:
            print(f"   - {error.field}: {error.message} ({error.message_he})")
    except Exception as e:
        print(f"❌ Document validation test failed: {e}")
    
    # Test user validation
    invalid_user_data = {
        "email": "invalid-email",
        "password": "123",  # Too short
        "full_name": "A",  # Too short
        "phone": "invalid-phone"
    }
    
    try:
        errors = UserValidator.validate_user_registration(invalid_user_data)
        print(f"✅ User validation found {len(errors)} errors:")
        for error in errors:
            print(f"   - {error.field}: {error.message} ({error.message_he})")
    except Exception as e:
        print(f"❌ User validation test failed: {e}")

def test_http_exceptions():
    """Test HTTP exception creation"""
    print("\n🧪 Testing HTTP Exceptions...")
    
    try:
        # Test not found error
        not_found_exc = create_not_found_error("project")
        print(f"✅ Not found error: {not_found_exc.status_code} - {not_found_exc.detail['message']}")
        
        # Test database error
        db_error_exc = create_database_error("creating project")
        print(f"✅ Database error: {db_error_exc.status_code} - {db_error_exc.detail['message']}")
        
        # Test external service error
        service_error_exc = create_external_service_error("Trello API")
        print(f"✅ External service error: {service_error_exc.status_code} - {service_error_exc.detail['message']}")
        
        # Test validation error with field details
        field_errors = [
            FieldError(
                field="email",
                message="Invalid email format",
                message_he="פורמט אימייל לא תקין",
                code="invalid_email",
                value="invalid-email"
            )
        ]
        validation_exc = create_validation_error(field_errors)
        print(f"✅ Validation error: {validation_exc.status_code} - {len(validation_exc.detail['field_errors'])} field errors")
        
    except Exception as e:
        print(f"❌ HTTP exception test failed: {e}")

def test_error_logging():
    """Test error logging service"""
    print("\n🧪 Testing Error Logging...")
    
    try:
        # Create error context
        context = create_error_context(
            endpoint="/api/projects",
            method="POST",
            user_id="test-user-123",
            ip_address="127.0.0.1"
        )
        
        # Test various error logging methods
        correlation_id1 = error_logging_service.log_validation_error(
            field_errors=[{
                "field": "name",
                "message": "Name is required",
                "code": "required"
            }],
            context=context
        )
        print(f"✅ Validation error logged with correlation ID: {correlation_id1}")
        
        correlation_id2 = error_logging_service.log_database_error(
            operation="creating project",
            exception=Exception("Connection timeout"),
            context=context
        )
        print(f"✅ Database error logged with correlation ID: {correlation_id2}")
        
        correlation_id3 = error_logging_service.log_external_service_error(
            service_name="Trello API",
            operation="creating board",
            exception=Exception("API rate limit exceeded"),
            context=context,
            recovery_attempted=True,
            recovery_successful=False
        )
        print(f"✅ External service error logged with correlation ID: {correlation_id3}")
        
    except Exception as e:
        print(f"❌ Error logging test failed: {e}")

def test_error_recovery():
    """Test error recovery guidance"""
    print("\n🧪 Testing Error Recovery...")
    
    try:
        # Test recovery guides for different error types
        error_codes = [
            "DATABASE_CONNECTION_ERROR",
            "FILE_TOO_LARGE",
            "TRELLO_API_ERROR",
            "VALIDATION_ERROR"
        ]
        
        for error_code in error_codes:
            guide = get_recovery_guide(error_code)
            if guide:
                print(f"✅ Recovery guide for {error_code}:")
                print(f"   Title: {guide.title} ({guide.title_he})")
                print(f"   Steps: {len(guide.user_steps)} user steps")
                if guide.technical_steps:
                    print(f"   Technical steps: {len(guide.technical_steps)}")
                
                # Test getting recovery steps
                steps = get_recovery_steps(error_code, include_technical=True)
                print(f"   Total recovery steps: {len(steps)}")
            else:
                print(f"❌ No recovery guide found for {error_code}")
                
    except Exception as e:
        print(f"❌ Error recovery test failed: {e}")

def test_bilingual_support():
    """Test bilingual error message support"""
    print("\n🧪 Testing Bilingual Support...")
    
    try:
        # Test Hebrew error messages
        field_error = FieldError(
            field="name",
            message="Name is required",
            message_he="שם הוא שדה חובה",
            code="required"
        )
        
        print(f"✅ Bilingual field error:")
        print(f"   English: {field_error.message}")
        print(f"   Hebrew: {field_error.message_he}")
        
        # Test validation with Hebrew messages
        errors = ProjectValidator.validate_project_data({"name": ""})
        if errors:
            error = errors[0]
            print(f"✅ Project validation bilingual:")
            print(f"   English: {error.message}")
            print(f"   Hebrew: {error.message_he}")
        
    except Exception as e:
        print(f"❌ Bilingual support test failed: {e}")

def test_error_response_format():
    """Test standardized error response format"""
    print("\n🧪 Testing Error Response Format...")
    
    try:
        # Create a validation error and check its format
        field_errors = [
            FieldError(
                field="email",
                message="Invalid email format",
                message_he="פורמט אימייל לא תקין",
                code="invalid_email"
            )
        ]
        
        validation_exc = create_validation_error(field_errors)
        error_detail = validation_exc.detail
        
        # Check required fields in error response
        required_fields = [
            "success", "error", "correlation_id", "timestamp",
            "status_code", "error_code", "category", "severity",
            "message", "field_errors"
        ]
        
        missing_fields = [field for field in required_fields if field not in error_detail]
        
        if not missing_fields:
            print("✅ Error response format is complete")
            print(f"   Correlation ID: {error_detail['correlation_id']}")
            print(f"   Error code: {error_detail['error_code']}")
            print(f"   Category: {error_detail['category']}")
            print(f"   Severity: {error_detail['severity']}")
            print(f"   Field errors: {len(error_detail['field_errors'])}")
        else:
            print(f"❌ Missing fields in error response: {missing_fields}")
            
    except Exception as e:
        print(f"❌ Error response format test failed: {e}")

def main():
    """Run all error handling tests"""
    print("🚀 Starting Error Handling System Tests\n")
    
    test_validation_errors()
    test_http_exceptions()
    test_error_logging()
    test_error_recovery()
    test_bilingual_support()
    test_error_response_format()
    
    print("\n✨ Error Handling System Tests Completed!")

if __name__ == "__main__":
    main()