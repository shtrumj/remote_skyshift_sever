"""
Customer Authentication Module for Remote Agent Manager
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from Scripts.database import db_manager

# Security
security = HTTPBearer()

logger = logging.getLogger(__name__)


class Customer(BaseModel):
    id: str
    uuid: str
    name: str
    address: Optional[str] = None
    api_key: Optional[str] = None
    api_key_created_at: Optional[str] = None
    api_key_last_used: Optional[str] = None
    is_active: bool = True
    created_at: str
    updated_at: str


class CustomerAPIKey(BaseModel):
    customer_uuid: str
    api_key: str


async def get_current_customer(request: Request) -> Optional[Customer]:
    """Get current customer from API key"""
    logger.info(
        f"🔍 get_current_customer called from {request.client.host if request.client else 'unknown'}"
    )
    logger.info(f"🔍 Request URL: {request.url}")
    logger.info(f"🔍 Request headers: {dict(request.headers)}")

    api_key = None

    # Try to get API key from Authorization header
    auth_header = request.headers.get("Authorization")
    logger.info(f"🔍 Authorization header: {auth_header}")
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header.split(" ")[1]
        logger.info(f"🔍 API key from Authorization header: {api_key[:20]}...")

    # Try to get API key from X-API-Key header
    if not api_key:
        api_key = request.headers.get("X-API-Key")
        logger.info(
            f"🔍 API key from X-API-Key header: {api_key[:20] if api_key else 'None'}..."
        )

    if not api_key:
        logger.error("❌ No API key found in headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"🔍 Verifying API key: {api_key[:20]}...")

    # Get customer from database
    customer_data = db_manager.get_customer_by_api_key(api_key)
    if customer_data is None:
        logger.error("❌ Invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not customer_data.get("is_active", True):
        logger.error(f"❌ Customer account is inactive: {customer_data['uuid']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"✅ Customer authenticated successfully: {customer_data['name']}")
    return Customer(**customer_data)


async def get_current_customer_dependency(request: Request) -> Customer:
    """Dependency function to get current customer"""
    return await get_current_customer(request)


async def get_current_active_customer(
    current_customer: Customer = Depends(get_current_customer_dependency),
) -> Customer:
    """Get current active customer"""
    if not current_customer.is_active:
        raise HTTPException(status_code=400, detail="Inactive customer account")
    return current_customer
