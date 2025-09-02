"""Authentication router for user registration, login, and token management"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
import psycopg2
import os
from uuid import UUID

from packages.schemas.auth import (
    UserCreate, User, LoginRequest, Token, APIKeyCreate, APIKey, 
    PasswordResetRequest, PasswordResetConfirm
)
from ..services.auth_service import auth_service, get_current_user
from packages.schemas.auth import UserInDB

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_create: UserCreate):
    """Register a new user"""
    try:
        user = auth_service.create_user(user_create)
        return User(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {e}"
        )

@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest):
    """Login user and return access/refresh tokens"""
    try:
        return auth_service.login(login_request)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {e}"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        return auth_service.refresh_token(refresh_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {e}"
        )

@router.post("/logout")
async def logout(
    current_user: UserInDB = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """Logout user by invalidating refresh token"""
    token = credentials.credentials
    
    # For JWT tokens, we can't invalidate them individually, 
    # but we can remove any associated refresh tokens
    try:
        conn = auth_service.get_db_connection()
        cursor = conn.cursor()
        
        # Delete user's refresh tokens
        cursor.execute(
            "DELETE FROM user_sessions WHERE user_id = %s",
            (str(current_user.id),)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {e}"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """Get current user information"""
    return User(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

@router.post("/api-keys", response_model=APIKey, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_create: APIKeyCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """Create a new API key for the current user"""
    try:
        return auth_service.create_api_key(current_user.id, api_key_create)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating API key: {e}"
        )

@router.get("/api-keys", response_model=List[APIKey])
async def get_api_keys(current_user: UserInDB = Depends(get_current_user)):
    """Get all API keys for the current user (without the actual key values)"""
    try:
        conn = auth_service.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, user_id, name, expires_at, is_active, created_at, last_used_at
            FROM api_keys WHERE user_id = %s ORDER BY created_at DESC
            """,
            (str(current_user.id),)
        )
        
        api_keys = []
        for row in cursor.fetchall():
            api_keys.append(APIKey(
                id=row[0],
                user_id=row[1],
                name=row[2],
                key="",  # Never return the actual key
                expires_at=row[3],
                is_active=row[4],
                created_at=row[5],
                last_used_at=row[6]
            ))
        
        cursor.close()
        conn.close()
        
        return api_keys
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching API keys: {e}"
        )

@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: UUID,
    current_user: UserInDB = Depends(get_current_user)
):
    """Delete an API key"""
    try:
        conn = auth_service.get_db_connection()
        cursor = conn.cursor()
        
        # Verify the API key belongs to the current user
        cursor.execute(
            "SELECT id FROM api_keys WHERE id = %s AND user_id = %s",
            (str(api_key_id), str(current_user.id))
        )
        
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        # Delete the API key
        cursor.execute(
            "DELETE FROM api_keys WHERE id = %s",
            (str(api_key_id),)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "API key deleted successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting API key: {e}"
        )

@router.post("/password-reset/request")
async def request_password_reset(request: PasswordResetRequest):
    """Request password reset (sends email with reset token)"""
    # In a real implementation, this would send an email with a reset link
    # For now, we'll just return a success message
    
    user = auth_service.get_user_by_email(request.email)
    if user:
        # Generate reset token and store it (implementation would go here)
        pass
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(confirm: PasswordResetConfirm):
    """Confirm password reset with token"""
    # In a real implementation, this would verify the reset token
    # and update the user's password
    
    # Placeholder implementation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset functionality not yet implemented"
    )

@router.get("/health")
async def auth_health():
    """Authentication service health check"""
    try:
        conn = auth_service.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "service": "auth"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication service unhealthy: {e}"
        )