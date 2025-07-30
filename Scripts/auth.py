"""
Authentication Module for Remote Agent Manager
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security
security = HTTPBearer()


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    is_approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"🔍 Attempting to decode token: {token[:20]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"🔍 Token payload: {payload}")
        username: str = payload.get("sub")
        if username is None:
            logger.error("❌ No 'sub' field in token payload")
            return None
        token_data = TokenData(username=username)
        logger.info(f"✅ Token verified successfully for user: {username}")
        return token_data
    except jwt.PyJWTError as e:
        logger.error(f"❌ JWT decode error: {str(e)}")
        return None


async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from token (supports both Bearer token and cookie)"""
    import logging

    logger = logging.getLogger(__name__)

    logger.info(
        f"🔍 get_current_user called from {request.client.host if request.client else 'unknown'}"
    )
    logger.info(f"🔍 Request URL: {request.url}")
    logger.info(f"🔍 Request headers: {dict(request.headers)}")
    logger.info(f"🔍 Request cookies: {dict(request.cookies)}")

    token = None

    # Try to get token from Authorization header
    auth_header = request.headers.get("Authorization")
    logger.info(f"🔍 Authorization header: {auth_header}")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        logger.info(f"🔍 Token from Authorization header: {token[:20]}...")

    # If no token in header, try to get from cookie
    if not token:
        token = request.cookies.get("access_token")
        logger.info(f"🔍 Token from cookie: {token[:20] if token else 'None'}...")

    if not token:
        logger.error("❌ No token found in headers or cookies")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"🔍 Verifying token: {token[:20]}...")
    token_data = verify_token(token)
    if token_data is None:
        logger.error("❌ Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"🔍 Token verified for username: {token_data.username}")

    # Get user from database
    from Scripts.database import db_manager

    user_data = db_manager.get_user_by_username(token_data.username)
    if user_data is None:
        logger.error(f"❌ User not found in database: {token_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"✅ User authenticated successfully: {user_data['username']}")
    return User(**user_data)


async def get_current_user_dependency(request: Request) -> User:
    """Dependency function to get current user"""
    return await get_current_user(request)


async def get_current_active_user(
    current_user: User = Depends(get_current_user_dependency),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current admin user"""
    import logging

    logger = logging.getLogger(__name__)

    logger.info(f"🔍 Checking admin access for user: {current_user.username}")
    if not current_user.is_admin:
        logger.error(f"❌ Access denied - user {current_user.username} is not admin")
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info(f"✅ Admin access granted for user: {current_user.username}")
    return current_user


async def get_current_approved_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current approved user"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not yet approved by admin")
    return current_user
