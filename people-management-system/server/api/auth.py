"""
API Authentication and Authorization Utilities.

This module provides API key authentication, client tracking,
and authorization utilities for the People Management System API.
"""

import hashlib
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from fastapi import HTTPException, Header, Request, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from ..core.config import get_settings
from .responses import create_unauthorized_response, create_forbidden_response

# Configure logging
logger = logging.getLogger(__name__)

# API Key header security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyData(BaseModel):
    """API key metadata and permissions."""
    
    key_id: str = Field(..., description="Unique key identifier")
    name: str = Field(..., description="Human-readable key name")
    hashed_key: str = Field(..., description="Hashed API key value")
    client_name: str = Field(..., description="Client application name")
    permissions: Set[str] = Field(default_factory=set, description="Granted permissions")
    rate_limit_override: Optional[int] = Field(None, description="Custom rate limit per minute") 
    is_active: bool = Field(True, description="Whether the key is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Key creation time")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    expires_at: Optional[datetime] = Field(None, description="Key expiration time")
    usage_count: int = Field(0, description="Total usage count")
    ip_whitelist: Optional[List[str]] = Field(None, description="Allowed IP addresses")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional metadata")


class APIClientInfo(BaseModel):
    """Client information extracted from API key."""
    
    key_id: str
    client_name: str
    permissions: Set[str]
    rate_limit: Optional[int] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class APIKeyManager:
    """Manages API keys and authentication."""
    
    def __init__(self):
        self.api_keys: Dict[str, APIKeyData] = {}
        self._load_default_keys()
    
    def _load_default_keys(self):
        """Load default API keys for development and testing."""
        settings = get_settings()
        
        # Create a default admin key for development
        if settings.debug:
            admin_key = "dev-admin-key-12345"
            self.api_keys[admin_key] = APIKeyData(
                key_id="dev-admin",
                name="Development Admin Key",
                hashed_key=self._hash_key(admin_key),
                client_name="Development Client",
                permissions={"read", "write", "admin"},
                is_active=True,
                metadata={"environment": "development"}
            )
            
            # Create a read-only key
            readonly_key = "dev-readonly-key-67890"
            self.api_keys[readonly_key] = APIKeyData(
                key_id="dev-readonly",
                name="Development Read-Only Key",
                hashed_key=self._hash_key(readonly_key),
                client_name="Read-Only Client",
                permissions={"read"},
                rate_limit_override=120,  # Higher limit for read-only
                is_active=True,
                metadata={"environment": "development", "type": "readonly"}
            )
            
            logger.info("Loaded development API keys")
    
    def _hash_key(self, key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def generate_api_key(
        self,
        client_name: str,
        permissions: Set[str],
        name: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        rate_limit_override: Optional[int] = None,
        ip_whitelist: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> tuple[str, str]:
        """
        Generate a new API key.
        
        Returns:
            Tuple of (api_key, key_id)
        """
        # Generate secure random key
        api_key = f"pmapi_{secrets.token_urlsafe(32)}"
        key_id = f"key_{secrets.token_hex(8)}"
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create key data
        key_data = APIKeyData(
            key_id=key_id,
            name=name or f"API Key for {client_name}",
            hashed_key=self._hash_key(api_key),
            client_name=client_name,
            permissions=permissions,
            rate_limit_override=rate_limit_override,
            expires_at=expires_at,
            ip_whitelist=ip_whitelist,
            metadata=metadata or {}
        )
        
        # Store the key
        self.api_keys[api_key] = key_data
        
        logger.info(f"Generated new API key for client: {client_name}")
        return api_key, key_id
    
    def validate_api_key(
        self,
        api_key: str,
        client_ip: Optional[str] = None,
        required_permissions: Optional[Set[str]] = None
    ) -> Optional[APIClientInfo]:
        """
        Validate an API key and return client info.
        
        Args:
            api_key: The API key to validate
            client_ip: Client IP address for whitelist checking
            required_permissions: Required permissions for this operation
            
        Returns:
            APIClientInfo if valid, None if invalid
        """
        if not api_key or api_key not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key]
        
        # Check if key is active
        if not key_data.is_active:
            logger.warning(f"Inactive API key used: {key_data.key_id}")
            return None
        
        # Check expiration
        if key_data.expires_at and datetime.utcnow() > key_data.expires_at:
            logger.warning(f"Expired API key used: {key_data.key_id}")
            return None
        
        # Check IP whitelist
        if key_data.ip_whitelist and client_ip:
            if client_ip not in key_data.ip_whitelist:
                logger.warning(f"API key used from unauthorized IP: {client_ip}")
                return None
        
        # Check permissions
        if required_permissions and not required_permissions.issubset(key_data.permissions):
            logger.warning(f"Insufficient permissions for key: {key_data.key_id}")
            return None
        
        # Update usage statistics
        key_data.last_used_at = datetime.utcnow()
        key_data.usage_count += 1
        
        # Return client info
        return APIClientInfo(
            key_id=key_data.key_id,
            client_name=key_data.client_name,
            permissions=key_data.permissions,
            rate_limit=key_data.rate_limit_override,
            metadata=key_data.metadata
        )
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            self.api_keys[api_key].is_active = False
            logger.info(f"Revoked API key: {self.api_keys[api_key].key_id}")
            return True
        return False
    
    def list_api_keys(self) -> List[Dict[str, any]]:
        """List all API keys (without exposing the actual keys)."""
        return [
            {
                "key_id": key_data.key_id,
                "name": key_data.name,
                "client_name": key_data.client_name,
                "permissions": list(key_data.permissions),
                "is_active": key_data.is_active,
                "created_at": key_data.created_at.isoformat(),
                "last_used_at": key_data.last_used_at.isoformat() if key_data.last_used_at else None,
                "expires_at": key_data.expires_at.isoformat() if key_data.expires_at else None,
                "usage_count": key_data.usage_count,
                "metadata": key_data.metadata
            }
            for key_data in self.api_keys.values()
        ]
    
    def get_key_stats(self, api_key: str) -> Optional[Dict[str, any]]:
        """Get statistics for a specific API key."""
        if api_key not in self.api_keys:
            return None
        
        key_data = self.api_keys[api_key]
        return {
            "key_id": key_data.key_id,
            "usage_count": key_data.usage_count,
            "last_used_at": key_data.last_used_at.isoformat() if key_data.last_used_at else None,
            "created_at": key_data.created_at.isoformat(),
            "is_active": key_data.is_active
        }


# Global API key manager instance
api_key_manager = APIKeyManager()


# Dependency functions for FastAPI

async def get_api_key_optional(
    request: Request,
    x_api_key: Optional[str] = Header(None)
) -> Optional[APIClientInfo]:
    """
    Optional API key dependency that doesn't raise errors.
    
    Returns client info if valid API key provided, None otherwise.
    """
    if not x_api_key:
        return None
    
    client_ip = request.client.host if request.client else None
    client_info = api_key_manager.validate_api_key(x_api_key, client_ip)
    
    # Add client info to request state for logging
    if client_info:
        request.state.api_client = client_info
        logger.debug(f"Authenticated API client: {client_info.client_name}")
    
    return client_info


async def get_api_key_required(
    request: Request,
    x_api_key: Optional[str] = Header(None)
) -> APIClientInfo:
    """
    Required API key dependency that raises 401 if no valid key provided.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    client_ip = request.client.host if request.client else None
    client_info = api_key_manager.validate_api_key(x_api_key, client_ip)
    
    if not client_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    # Add client info to request state
    request.state.api_client = client_info
    logger.debug(f"Authenticated API client: {client_info.client_name}")
    
    return client_info


def require_permissions(*required_permissions: str):
    """
    Decorator factory for requiring specific permissions.
    
    Usage:
        @require_permissions("read", "write")
        async def my_endpoint():
            pass
    """
    def dependency(client_info: APIClientInfo = get_api_key_required):
        required_perms = set(required_permissions)
        if not required_perms.issubset(client_info.permissions):
            missing_perms = required_perms - client_info.permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_perms)}"
            )
        return client_info
    
    return dependency


async def get_admin_api_key(
    client_info: APIClientInfo = get_api_key_required
) -> APIClientInfo:
    """Dependency that requires admin permissions."""
    if "admin" not in client_info.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    return client_info


# Utility functions

def get_client_info_from_request(request: Request) -> Optional[APIClientInfo]:
    """Extract client info from request state."""
    return getattr(request.state, 'api_client', None)


def is_authenticated_request(request: Request) -> bool:
    """Check if request is authenticated with valid API key."""
    return hasattr(request.state, 'api_client') and request.state.api_client is not None


def get_client_rate_limit(request: Request) -> Optional[int]:
    """Get custom rate limit for authenticated client."""
    client_info = get_client_info_from_request(request)
    return client_info.rate_limit if client_info else None


def create_api_key_for_client(
    client_name: str,
    permissions: List[str],
    expires_in_days: int = 365,
    **kwargs
) -> Dict[str, str]:
    """
    Convenience function to create an API key for a client.
    
    Returns:
        Dictionary with api_key and key_id
    """
    api_key, key_id = api_key_manager.generate_api_key(
        client_name=client_name,
        permissions=set(permissions),
        expires_in_days=expires_in_days,
        **kwargs
    )
    
    return {
        "api_key": api_key,
        "key_id": key_id,
        "client_name": client_name,
        "permissions": permissions,
        "expires_in_days": expires_in_days
    }


# API key management endpoints helpers

def validate_key_permissions(permissions: List[str]) -> Set[str]:
    """Validate and normalize permissions."""
    valid_permissions = {"read", "write", "admin", "statistics"}
    provided_permissions = set(permissions)
    
    invalid_permissions = provided_permissions - valid_permissions
    if invalid_permissions:
        raise ValueError(f"Invalid permissions: {', '.join(invalid_permissions)}")
    
    return provided_permissions


def format_api_key_info(api_key_data: APIKeyData, include_key: bool = False) -> Dict[str, any]:
    """Format API key data for API responses."""
    data = {
        "key_id": api_key_data.key_id,
        "name": api_key_data.name,
        "client_name": api_key_data.client_name,
        "permissions": list(api_key_data.permissions),
        "is_active": api_key_data.is_active,
        "created_at": api_key_data.created_at.isoformat(),
        "last_used_at": api_key_data.last_used_at.isoformat() if api_key_data.last_used_at else None,
        "expires_at": api_key_data.expires_at.isoformat() if api_key_data.expires_at else None,
        "usage_count": api_key_data.usage_count,
        "rate_limit_override": api_key_data.rate_limit_override,
        "ip_whitelist": api_key_data.ip_whitelist,
        "metadata": api_key_data.metadata
    }
    
    return data


# Export public interface
__all__ = [
    # Classes
    "APIKeyData",
    "APIClientInfo", 
    "APIKeyManager",
    
    # Manager instance
    "api_key_manager",
    
    # Dependencies
    "get_api_key_optional",
    "get_api_key_required",
    "require_permissions",
    "get_admin_api_key",
    
    # Utilities
    "get_client_info_from_request",
    "is_authenticated_request",
    "get_client_rate_limit",
    "create_api_key_for_client",
    "validate_key_permissions",
    "format_api_key_info"
]