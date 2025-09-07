"""Authentication service with JWT tokens and password hashing"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2

from packages.schemas.auth import UserCreate, UserInDB, LoginRequest, Token, APIKeyCreate, APIKey

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7

# HTTP Bearer scheme
bearer_scheme = HTTPBearer()

class AuthService:
    """Service for authentication and user management"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database connection failed: {e}"
            )
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, user_id: UUID) -> str:
        """Create refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email from database"""
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at
                FROM users WHERE email = %s
                """,
                (email,)
            )
            row = cursor.fetchone()
            if row:
                return UserInDB(
                    id=row[0],
                    email=row[1],
                    full_name=row[2],
                    hashed_password=row[3],
                    is_active=row[4],
                    is_superuser=row[5],
                    created_at=row[6],
                    updated_at=row[7]
                )
            return None
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        """Get user by ID from database"""
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, email, full_name, hashed_password, is_active, is_superuser, created_at, updated_at
                FROM users WHERE id = %s
                """,
                (str(user_id),)
            )
            row = cursor.fetchone()
            if row:
                return UserInDB(
                    id=row[0],
                    email=row[1],
                    full_name=row[2],
                    hashed_password=row[3],
                    is_active=row[4],
                    is_superuser=row[5],
                    created_at=row[6],
                    updated_at=row[7]
                )
            return None
        finally:
            conn.close()
    
    def create_user(self, user_create: UserCreate) -> UserInDB:
        """Create new user"""
        # Check if user already exists
        existing_user = self.get_user_by_email(user_create.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Hash password
        hashed_password = self.get_password_hash(user_create.password)
        
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, full_name, hashed_password)
                VALUES (%s, %s, %s)
                RETURNING id, created_at, updated_at
                """,
                (user_create.email, user_create.full_name, hashed_password)
            )
            
            result = cursor.fetchone()
            conn.commit()
            
            return UserInDB(
                id=result[0],
                email=user_create.email,
                full_name=user_create.full_name,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False,
                created_at=result[1],
                updated_at=result[2]
            )
        except psycopg2.Error as e:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {e}"
            )
        finally:
            conn.close()
    
    def authenticate_user(self, login_request: LoginRequest) -> Optional[UserInDB]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(login_request.email)
        if not user:
            return None
        if not self.verify_password(login_request.password, user.hashed_password):
            return None
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        return user
    
    def login(self, login_request: LoginRequest) -> Token:
        """Login user and return tokens"""
        user = self.authenticate_user(login_request)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        access_token = self.create_access_token({"sub": str(user.id)})
        refresh_token = self.create_refresh_token(user.id)
        
        # Store refresh token in database
        self._store_refresh_token(user.id, refresh_token)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token
        )
    
    def _store_refresh_token(self, user_id: UUID, refresh_token: str):
        """Store refresh token in database"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token_hash = self.get_password_hash(refresh_token)
        
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_sessions (user_id, refresh_token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (str(user_id), refresh_token_hash, expires_at)
            )
            conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error storing refresh token: {e}"
            )
        finally:
            conn.close()
    
    def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        # Verify refresh token
        try:
            payload = self.verify_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            user_id = UUID(payload["sub"])
            
            # Verify refresh token exists in database
            if not self._verify_refresh_token(user_id, refresh_token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Create new access token
            access_token = self.create_access_token({"sub": str(user_id)})
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token refresh failed: {e}"
            )
    
    def _verify_refresh_token(self, user_id: UUID, refresh_token: str) -> bool:
        """Verify refresh token exists in database"""
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT refresh_token_hash FROM user_sessions 
                WHERE user_id = %s AND expires_at > NOW()
                """,
                (str(user_id),)
            )
            
            for row in cursor.fetchall():
                if self.verify_password(refresh_token, row[0]):
                    return True
            return False
        finally:
            conn.close()
    
    def create_api_key(self, user_id: UUID, api_key_create: APIKeyCreate) -> APIKey:
        """Create API key for user"""
        # Generate random API key
        api_key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = self.get_password_hash(api_key)
        
        expires_at = None
        if api_key_create.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=api_key_create.expires_in_days)
        
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO api_keys (user_id, key_hash, name, expires_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (str(user_id), key_hash, api_key_create.name, expires_at)
            )
            
            result = cursor.fetchone()
            conn.commit()
            
            return APIKey(
                id=result[0],
                user_id=user_id,
                name=api_key_create.name,
                key=api_key,  # Only returned once
                expires_at=expires_at,
                is_active=True,
                created_at=result[1],
                last_used_at=None
            )
        except psycopg2.Error as e:
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating API key: {e}"
            )
        finally:
            conn.close()
    
    def verify_api_key(self, api_key: str) -> Optional[UserInDB]:
        """Verify API key and return user"""
        conn = self.get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT ak.id, ak.user_id, ak.key_hash, ak.name, ak.expires_at, ak.is_active,
                       u.email, u.full_name, u.is_active as user_active, u.is_superuser
                FROM api_keys ak
                JOIN users u ON ak.user_id = u.id
                WHERE ak.is_active = TRUE AND u.is_active = TRUE
                """
            )
            
            for row in cursor.fetchall():
                key_id, user_id, key_hash, name, expires_at, is_active, email, full_name, user_active, is_superuser = row
                
                # Check if expired
                if expires_at and expires_at < datetime.now(timezone.utc):
                    continue
                
                # Verify key
                if self.verify_password(api_key, key_hash):
                    # Update last used timestamp
                    cursor.execute(
                        "UPDATE api_keys SET last_used_at = NOW() WHERE id = %s",
                        (key_id,)
                    )
                    conn.commit()
                    
                    return UserInDB(
                        id=user_id,
                        email=email,
                        full_name=full_name,
                        hashed_password="",  # Not needed for API key auth
                        is_active=user_active,
                        is_superuser=is_superuser,
                        created_at=datetime.now(),  # Placeholder
                        updated_at=datetime.now()   # Placeholder
                    )
            
            return None
        finally:
            conn.close()

# Global instance
auth_service = AuthService()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> UserInDB:
    """Dependency to get current user from JWT token"""
    token = credentials.credentials
    
    # Try JWT token first
    try:
        payload = auth_service.verify_token(token)
        user_id = UUID(payload["sub"])
        user = auth_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        return user
    except (HTTPException, jwt.InvalidTokenError):
        pass
    
    # Try API key
    user = auth_service.verify_api_key(token)
    if user:
        return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )