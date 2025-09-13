"""Authentication utilities for API endpoints."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

# Simple bearer token authentication (to be enhanced later)
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> int:
    """
    Get current user ID from authentication token.

    For now, returns a default user ID (1) for development.
    This will be enhanced with proper JWT authentication later.

    Args:
        credentials: Bearer token credentials

    Returns:
        User ID
    """
    # TODO: Implement proper JWT validation
    # For development, return default user ID
    return 1


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> HTTPAuthorizationCredentials:
    """
    Require authentication for protected endpoints.

    Args:
        credentials: Bearer token credentials

    Returns:
        Validated credentials

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: Validate JWT token
    return credentials