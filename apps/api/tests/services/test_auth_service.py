"""Comprehensive tests for authentication service"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
import jwt
import uuid
from fastapi import HTTPException, status

from services.auth_service import AuthService, pwd_context
from packages.schemas.auth import UserCreate, LoginRequest, APIKeyCreate

def test_auth_service_initialization():
    """Test AuthService initialization"""
    service = AuthService()
    assert service.db_url is not None
    assert "postgresql://" in service.db_url

def test_verify_password():
    """Test password verification"""
    service = AuthService()
    
    # Test correct password
    plain_password = "testpassword123"
    hashed_password = pwd_context.hash(plain_password)
    assert service.verify_password(plain_password, hashed_password) is True
    
    # Test incorrect password
    assert service.verify_password("wrongpassword", hashed_password) is False

def test_get_password_hash():
    """Test password hashing"""
    service = AuthService()
    password = "testpassword123"
    hashed = service.get_password_hash(password)
    
    assert hashed is not None
    assert len(hashed) > 0
    assert hashed != password
    assert pwd_context.verify(password, hashed) is True

def test_create_access_token():
    """Test JWT access token creation"""
    service = AuthService()
    
    # Test with default expiration
    data = {"sub": "test_user_id"}
    token = service.create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Test with custom expiration
    custom_delta = timedelta(minutes=30)
    token_custom = service.create_access_token(data, custom_delta)
    assert token_custom is not None
    assert token_custom != token

def test_create_refresh_token():
    """Test refresh token creation"""
    service = AuthService()
    user_id = uuid.uuid4()
    
    token = service.create_refresh_token(user_id)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Verify token content
    payload = jwt.decode(token, "your-super-secret-jwt-key-change-in-production", algorithms=["HS256"])
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"

def test_verify_token_valid():
    """Test valid token verification"""
    service = AuthService()
    
    # Create a valid token
    data = {"sub": "test_user_id", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    token = jwt.encode(data, "your-super-secret-jwt-key-change-in-production", algorithm="HS256")
    
    payload = service.verify_token(token)
    assert payload["sub"] == "test_user_id"

def test_verify_token_expired():
    """Test expired token verification"""
    service = AuthService()
    
    # Create an expired token
    data = {"sub": "test_user_id", "exp": datetime.now(timezone.utc) - timedelta(minutes=30)}
    token = jwt.encode(data, "your-super-secret-jwt-key-change-in-production", algorithm="HS256")
    
    with pytest.raises(HTTPException) as exc_info:
        service.verify_token(token)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in exc_info.value.detail.lower()

def test_verify_token_invalid():
    """Test invalid token verification"""
    service = AuthService()
    
    with pytest.raises(HTTPException) as exc_info:
        service.verify_token("invalid.token.here")
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid" in exc_info.value.detail.lower()

def test_authenticate_user_success():
    """Test successful user authentication"""
    service = AuthService()
    
    # Mock user data
    mock_user = Mock()
    mock_user.hashed_password = pwd_context.hash("testpassword123")
    mock_user.is_active = True
    
    with patch.object(service, 'get_user_by_email', return_value=mock_user):
        login_request = LoginRequest(email="test@example.com", password="testpassword123")
        result = service.authenticate_user(login_request)
        
        assert result is mock_user

def test_authenticate_user_wrong_password():
    """Test authentication with wrong password"""
    service = AuthService()
    
    mock_user = Mock()
    mock_user.hashed_password = pwd_context.hash("correctpassword")
    mock_user.is_active = True
    
    with patch.object(service, 'get_user_by_email', return_value=mock_user):
        login_request = LoginRequest(email="test@example.com", password="wrongpassword")
        result = service.authenticate_user(login_request)
        
        assert result is None

def test_authenticate_user_inactive():
    """Test authentication with inactive user"""
    service = AuthService()
    
    mock_user = Mock()
    mock_user.hashed_password = pwd_context.hash("testpassword123")
    mock_user.is_active = False
    
    with patch.object(service, 'get_user_by_email', return_value=mock_user):
        login_request = LoginRequest(email="test@example.com", password="testpassword123")
        
        with pytest.raises(HTTPException) as exc_info:
            service.authenticate_user(login_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "deactivated" in exc_info.value.detail.lower()

def test_login_success():
    """Test successful login"""
    service = AuthService()
    
    mock_user = Mock()
    mock_user.id = uuid.uuid4()
    mock_user.hashed_password = pwd_context.hash("testpassword123")
    mock_user.is_active = True
    
    with patch.object(service, 'authenticate_user', return_value=mock_user):
        with patch.object(service, '_store_refresh_token'):
            login_request = LoginRequest(email="test@example.com", password="testpassword123")
            result = service.login(login_request)
            
            assert result.access_token is not None
            assert result.token_type == "bearer"
            assert result.refresh_token is not None
            assert result.expires_in == 60 * 24 * 60  # 24 hours in seconds

def test_login_failure():
    """Test failed login"""
    service = AuthService()
    
    with patch.object(service, 'authenticate_user', return_value=None):
        login_request = LoginRequest(email="test@example.com", password="wrongpassword")
        
        with pytest.raises(HTTPException) as exc_info:
            service.login(login_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in exc_info.value.detail.lower()

def test_refresh_token_success():
    """Test successful token refresh"""
    service = AuthService()
    user_id = uuid.uuid4()
    
    # Create a valid refresh token
    refresh_token = service.create_refresh_token(user_id)
    
    with patch.object(service, '_verify_refresh_token', return_value=True):
        result = service.refresh_token(refresh_token)
        
        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.expires_in == 60 * 24 * 60
        assert result.refresh_token is None  # No new refresh token on refresh

def test_refresh_token_invalid():
    """Test refresh with invalid token"""
    service = AuthService()
    
    with patch.object(service, '_verify_refresh_token', return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            service.refresh_token("invalid.refresh.token")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in exc_info.value.detail.lower()

def test_create_api_key():
    """Test API key creation"""
    service = AuthService()
    user_id = uuid.uuid4()
    api_key_create = APIKeyCreate(name="test-key", expires_in_days=30)
    
    with patch.object(service, 'get_db_connection') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [uuid.uuid4(), datetime.now()]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = service.create_api_key(user_id, api_key_create)
        
        assert result is not None
        assert result.user_id == user_id
        assert result.name == "test-key"
        assert result.key.startswith("sk_")
        assert len(result.key) > 32  # Should be reasonably long

def test_verify_api_key_valid():
    """Test valid API key verification"""
    service = AuthService()
    
    # Create a test API key
    api_key = "sk_test_valid_api_key_123"
    hashed_key = pwd_context.hash(api_key)
    
    mock_user = Mock()
    mock_user.id = uuid.uuid4()
    mock_user.email = "test@example.com"
    mock_user.full_name = "Test User"
    mock_user.is_active = True
    mock_user.is_superuser = False
    
    with patch.object(service, 'get_db_connection') as mock_conn:
        mock_cursor = Mock()
        # Mock database result with valid API key
        mock_cursor.fetchall.return_value = [
            [uuid.uuid4(), mock_user.id, hashed_key, "test-key", None, True, 
             "test@example.com", "Test User", True, False]
        ]
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = service.verify_api_key(api_key)
        
        assert result is not None
        assert result.email == "test@example.com"
        assert result.is_active is True

def test_verify_api_key_invalid():
    """Test invalid API key verification"""
    service = AuthService()
    
    with patch.object(service, 'get_db_connection') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []  # No matching API keys
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = service.verify_api_key("invalid_api_key")
        
        assert result is None

def test_get_current_user_jwt():
    """Test getting current user from JWT token"""
    from services.auth_service import get_current_user, bearer_scheme
    
    user_id = uuid.uuid4()
    
    # Create a valid JWT token
    token = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
        "your-super-secret-jwt-key-change-in-production",
        algorithm="HS256"
    )
    
    mock_credentials = Mock()
    mock_credentials.credentials = token
    
    mock_user = Mock()
    mock_user.is_active = True
    
    with patch.object(AuthService, 'get_user_by_id', return_value=mock_user):
        result = get_current_user(mock_credentials)
        
        assert result is mock_user

def test_get_current_user_api_key():
    """Test getting current user from API key"""
    from services.auth_service import get_current_user, bearer_scheme
    
    mock_credentials = Mock()
    mock_credentials.credentials = "valid_api_key"
    
    mock_user = Mock()
    mock_user.is_active = True
    
    # Mock JWT verification to fail (so it falls back to API key)
    with patch.object(AuthService, 'verify_token', side_effect=HTTPException(status_code=401, detail="Invalid token")):
        with patch.object(AuthService, 'verify_api_key', return_value=mock_user):
            result = get_current_user(mock_credentials)
            
            assert result is mock_user

def test_get_current_user_invalid():
    """Test getting current user with invalid credentials"""
    from services.auth_service import get_current_user, bearer_scheme
    
    mock_credentials = Mock()
    mock_credentials.credentials = "invalid_credentials"
    
    # Mock both JWT and API key verification to fail
    with patch.object(AuthService, 'verify_token', side_effect=HTTPException(status_code=401, detail="Invalid token")):
        with patch.object(AuthService, 'verify_api_key', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(mock_credentials)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "invalid" in exc_info.value.detail.lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])