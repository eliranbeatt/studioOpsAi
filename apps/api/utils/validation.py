"""
Validation Utilities for StudioOps API

This module provides comprehensive validation utilities with bilingual error messages
and field-specific validation logic.
"""

import re
import uuid
from typing import List, Optional, Any, Dict, Union
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from email_validator import validate_email, EmailNotValidError

from utils.error_handling import FieldError, create_validation_error

class ValidationError(Exception):
    """Custom validation error with field details"""
    
    def __init__(self, field_errors: List[FieldError]):
        self.field_errors = field_errors
        super().__init__(f"Validation failed for {len(field_errors)} fields")

class Validator:
    """Comprehensive validation utility"""
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> Optional[FieldError]:
        """Validate that a field is not empty"""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return FieldError(
                field=field_name,
                message=f"{field_name} is required",
                message_he=f"{field_name} הוא שדה חובה",
                code="required",
                value=value
            )
        return None
    
    @staticmethod
    def validate_string_length(
        value: str, 
        field_name: str, 
        min_length: int = None, 
        max_length: int = None
    ) -> Optional[FieldError]:
        """Validate string length"""
        if not isinstance(value, str):
            return FieldError(
                field=field_name,
                message=f"{field_name} must be a string",
                message_he=f"{field_name} חייב להיות מחרוזת",
                code="invalid_type",
                value=value
            )
        
        length = len(value.strip())
        
        if min_length is not None and length < min_length:
            return FieldError(
                field=field_name,
                message=f"{field_name} must be at least {min_length} characters long",
                message_he=f"{field_name} חייב להיות באורך של לפחות {min_length} תווים",
                code="too_short",
                value=value
            )
        
        if max_length is not None and length > max_length:
            return FieldError(
                field=field_name,
                message=f"{field_name} must be no more than {max_length} characters long",
                message_he=f"{field_name} חייב להיות באורך של לא יותר מ-{max_length} תווים",
                code="too_long",
                value=value
            )
        
        return None
    
    @staticmethod
    def validate_email(value: str, field_name: str) -> Optional[FieldError]:
        """Validate email format"""
        if not value:
            return None
        
        try:
            validate_email(value)
            return None
        except EmailNotValidError:
            return FieldError(
                field=field_name,
                message=f"{field_name} must be a valid email address",
                message_he=f"{field_name} חייב להיות כתובת אימייל תקינה",
                code="invalid_email",
                value=value
            )
    
    @staticmethod
    def validate_uuid(value: str, field_name: str) -> Optional[FieldError]:
        """Validate UUID format"""
        if not value:
            return None
        
        try:
            uuid.UUID(str(value))
            return None
        except (ValueError, TypeError):
            return FieldError(
                field=field_name,
                message=f"{field_name} must be a valid UUID",
                message_he=f"{field_name} חייב להיות UUID תקין",
                code="invalid_uuid",
                value=value
            )
    
    @staticmethod
    def validate_numeric_range(
        value: Union[int, float, Decimal], 
        field_name: str, 
        min_value: Union[int, float, Decimal] = None, 
        max_value: Union[int, float, Decimal] = None
    ) -> Optional[FieldError]:
        """Validate numeric range"""
        if value is None:
            return None
        
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            return FieldError(
                field=field_name,
                message=f"{field_name} must be a valid number",
                message_he=f"{field_name} חייב להיות מספר תקין",
                code="invalid_number",
                value=value
            )
        
        if min_value is not None and numeric_value < min_value:
            return FieldError(
                field=field_name,
                message=f"{field_name} must be at least {min_value}",
                message_he=f"{field_name} חייב להיות לפחות {min_value}",
                code="too_small",
                value=value
            )
        
        if max_value is not None and numeric_value > max_value:
            return FieldError(
                field=field_name,
                message=f"{field_name} must be no more than {max_value}",
                message_he=f"{field_name} חייב להיות לא יותר מ-{max_value}",
                code="too_large",
                value=value
            )
        
        return None
    
    @staticmethod
    def validate_date_format(value: str, field_name: str) -> Optional[FieldError]:
        """Validate date format (ISO 8601)"""
        if not value:
            return None
        
        try:
            datetime.fromisoformat(value.replace('Z', '+00:00'))
            return None
        except ValueError:
            return FieldError(
                field=field_name,
                message=f"{field_name} must be a valid date in ISO format (YYYY-MM-DD)",
                message_he=f"{field_name} חייב להיות תאריך תקין בפורמט ISO (YYYY-MM-DD)",
                code="invalid_date",
                value=value
            )
    
    @staticmethod
    def validate_choice(
        value: Any, 
        field_name: str, 
        choices: List[Any], 
        choice_labels: Dict[Any, str] = None
    ) -> Optional[FieldError]:
        """Validate that value is one of allowed choices"""
        if value is None:
            return None
        
        if value not in choices:
            choices_str = ", ".join(str(c) for c in choices)
            return FieldError(
                field=field_name,
                message=f"{field_name} must be one of: {choices_str}",
                message_he=f"{field_name} חייב להיות אחד מ: {choices_str}",
                code="invalid_choice",
                value=value
            )
        
        return None
    
    @staticmethod
    def validate_phone_number(value: str, field_name: str) -> Optional[FieldError]:
        """Validate phone number format (Israeli format)"""
        if not value:
            return None
        
        # Remove spaces, dashes, and parentheses
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        
        # Israeli phone number patterns
        patterns = [
            r'^05\d{8}$',  # Mobile: 05X-XXXXXXX
            r'^0[2-4,8-9]\d{7}$',  # Landline: 0X-XXXXXXX
            r'^\+9725\d{8}$',  # International mobile: +972-5X-XXXXXXX
            r'^\+972[2-4,8-9]\d{7}$'  # International landline: +972-X-XXXXXXX
        ]
        
        if not any(re.match(pattern, cleaned) for pattern in patterns):
            return FieldError(
                field=field_name,
                message=f"{field_name} must be a valid Israeli phone number",
                message_he=f"{field_name} חייב להיות מספר טלפון ישראלי תקין",
                code="invalid_phone",
                value=value
            )
        
        return None
    
    @staticmethod
    def validate_file_size(
        file_size: int, 
        field_name: str, 
        max_size_mb: int = 10
    ) -> Optional[FieldError]:
        """Validate file size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return FieldError(
                field=field_name,
                message=f"File size must not exceed {max_size_mb}MB",
                message_he=f"גודל הקובץ לא יכול לעלות על {max_size_mb}MB",
                code="file_too_large",
                value=file_size
            )
        
        return None
    
    @staticmethod
    def validate_file_type(
        filename: str, 
        field_name: str, 
        allowed_extensions: List[str]
    ) -> Optional[FieldError]:
        """Validate file type by extension"""
        if not filename:
            return None
        
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if extension not in [ext.lower() for ext in allowed_extensions]:
            allowed_str = ", ".join(allowed_extensions)
            return FieldError(
                field=field_name,
                message=f"File type must be one of: {allowed_str}",
                message_he=f"סוג הקובץ חייב להיות אחד מ: {allowed_str}",
                code="invalid_file_type",
                value=filename
            )
        
        return None

class ProjectValidator:
    """Specific validation for project-related data"""
    
    @staticmethod
    def validate_project_data(data: Dict[str, Any]) -> List[FieldError]:
        """Validate project creation/update data"""
        errors = []
        
        # Required fields
        if error := Validator.validate_required(data.get('name'), 'name'):
            errors.append(error)
        
        if error := Validator.validate_required(data.get('client_name'), 'client_name'):
            errors.append(error)
        
        # String length validations
        if data.get('name'):
            if error := Validator.validate_string_length(data['name'], 'name', min_length=2, max_length=200):
                errors.append(error)
        
        if data.get('client_name'):
            if error := Validator.validate_string_length(data['client_name'], 'client_name', min_length=2, max_length=200):
                errors.append(error)
        
        # Status validation
        valid_statuses = ['draft', 'active', 'completed', 'cancelled', 'on_hold']
        if data.get('status'):
            if error := Validator.validate_choice(data['status'], 'status', valid_statuses):
                errors.append(error)
        
        # Budget validations
        if data.get('budget_planned'):
            if error := Validator.validate_numeric_range(data['budget_planned'], 'budget_planned', min_value=0):
                errors.append(error)
        
        if data.get('budget_actual'):
            if error := Validator.validate_numeric_range(data['budget_actual'], 'budget_actual', min_value=0):
                errors.append(error)
        
        # Date validations
        if data.get('start_date'):
            if error := Validator.validate_date_format(data['start_date'], 'start_date'):
                errors.append(error)
        
        if data.get('due_date'):
            if error := Validator.validate_date_format(data['due_date'], 'due_date'):
                errors.append(error)
        
        return errors

class DocumentValidator:
    """Specific validation for document-related data"""
    
    @staticmethod
    def validate_document_upload(
        filename: str, 
        file_size: int, 
        mime_type: str = None
    ) -> List[FieldError]:
        """Validate document upload parameters"""
        errors = []
        
        # File name validation
        if error := Validator.validate_required(filename, 'filename'):
            errors.append(error)
        
        # File size validation (10MB max)
        if error := Validator.validate_file_size(file_size, 'file', max_size_mb=10):
            errors.append(error)
        
        # File type validation
        allowed_extensions = ['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif']
        if error := Validator.validate_file_type(filename, 'file', allowed_extensions):
            errors.append(error)
        
        return errors

class UserValidator:
    """Specific validation for user-related data"""
    
    @staticmethod
    def validate_user_registration(data: Dict[str, Any]) -> List[FieldError]:
        """Validate user registration data"""
        errors = []
        
        # Required fields
        if error := Validator.validate_required(data.get('email'), 'email'):
            errors.append(error)
        
        if error := Validator.validate_required(data.get('password'), 'password'):
            errors.append(error)
        
        if error := Validator.validate_required(data.get('full_name'), 'full_name'):
            errors.append(error)
        
        # Email validation
        if data.get('email'):
            if error := Validator.validate_email(data['email'], 'email'):
                errors.append(error)
        
        # Password validation
        if data.get('password'):
            if error := Validator.validate_string_length(data['password'], 'password', min_length=8):
                errors.append(error)
        
        # Name validation
        if data.get('full_name'):
            if error := Validator.validate_string_length(data['full_name'], 'full_name', min_length=2, max_length=100):
                errors.append(error)
        
        # Phone validation (optional)
        if data.get('phone'):
            if error := Validator.validate_phone_number(data['phone'], 'phone'):
                errors.append(error)
        
        return errors

def validate_and_raise(validation_func, *args, **kwargs):
    """Helper function to validate and raise HTTPException if errors found"""
    errors = validation_func(*args, **kwargs)
    if errors:
        raise create_validation_error(errors)
    return True