"""Authentication schemas and models"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)

class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None

class User(UserBase):
    """User response model"""
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserInDB(User):
    """User model with hashed password for database"""
    hashed_password: str

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """Authentication token model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class Session(BaseModel):
    """User session model"""
    id: UUID
    user_id: UUID
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime

class APIKeyCreate(BaseModel):
    """API key creation model"""
    name: str = Field(..., min_length=1, max_length=255)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)

class APIKey(BaseModel):
    """API key response model"""
    id: UUID
    user_id: UUID
    name: str
    key: str  # Only returned once during creation
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

class APIKeyInDB(BaseModel):
    """API key model for database"""
    id: UUID
    user_id: UUID
    key_hash: str
    name: str
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]

class Role(BaseModel):
    """User role model"""
    id: UUID
    name: str
    description: Optional[str]

class ProjectPermission(BaseModel):
    """Project permission model"""
    id: UUID
    user_id: UUID
    project_id: UUID
    can_view: bool
    can_edit: bool
    can_delete: bool
    can_manage_users: bool
    created_at: datetime
    updated_at: datetime

class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v