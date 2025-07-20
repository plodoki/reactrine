"""
Dependency injection functions for FastAPI.

This module contains dependency functions that can be injected into API endpoints
to provide common functionality like database sessions, authentication, etc.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db_session
from app.models.user import User
from app.security.auth_pak import decode_access_token_enhanced
from app.services.user import get_user_by_email_with_role

logger = get_logger(__name__)

# Security scheme for JWT token authentication
security = HTTPBearer(auto_error=False)


# Note: The local 'get_db_session' function was removed from this file.
# It is now imported directly from 'app.db.session' to ensure a single,
# consistent implementation for database session management across the application.


async def get_current_user_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    Dependency that extracts the JWT token from cookies or Authorization header.

    Prioritizes cookie-based authentication for web clients while maintaining
    header-based authentication for API clients.

    Args:
        request: FastAPI request object for accessing cookies
        credentials: HTTP authorization credentials from the request header.

    Returns:
        Optional[str]: The JWT token if present, None otherwise.

    Raises:
        HTTPException: If the token format is invalid.
    """
    # First try to get token from HttpOnly cookie
    token = request.cookies.get("access_token")

    # -------------------------------------------------------------
    # CSRF double-submit validation (only if a csrf_token cookie is
    # present; before the token is set this validation should be a no-op)
    # -------------------------------------------------------------
    csrf_cookie = request.cookies.get("csrf_token")
    # Only enforce CSRF for state-changing requests (POST/PUT/PATCH/DELETE)
    if csrf_cookie is not None and request.method.upper() not in {
        "GET",
        "HEAD",
        "OPTIONS",
    }:
        header_token = request.headers.get("X-CSRF-Token")

        if header_token is None or header_token != csrf_cookie:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing CSRF token",
            )

    if token:
        return token

    # Fallback to Authorization header for API clients
    if not credentials:
        return None

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Expected 'Bearer'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


async def get_current_user(
    token: Optional[str] = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Dependency that gets the current authenticated user with role loaded.

    This function validates the JWT token, extracts user information,
    and fetches the user from the database with role information.

    Args:
        token: JWT token from cookies or Authorization header.
        db: Database session.

    Returns:
        User: The current authenticated user with role loaded.

    Raises:
        HTTPException: If the token is invalid or user not found.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode and validate JWT token (supports both session tokens and PAK tokens)
    email, _ = await decode_access_token_enhanced(token, db)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database with role loaded
    user: Optional[User] = await get_user_by_email_with_role(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that ensures the current user is active.

    Args:
        current_user: The current authenticated user.

    Returns:
        User: The current active user.

    Raises:
        HTTPException: If the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account"
        )

    return current_user


async def get_optional_current_user(
    token: Optional[str] = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    """
    Dependency that optionally gets the current user with role loaded.

    Args:
        token: JWT token from cookies or Authorization header.
        db: Database session.

    Returns:
        Optional[User]: The current user with role if authenticated, None otherwise.
    """
    if not token:
        return None

    try:
        # Decode and validate JWT token (supports both session tokens and PAK tokens)
        email, _ = await decode_access_token_enhanced(token, db)
        if email is None:
            logger.debug("Invalid token in optional authentication")
            return None

        # Fetch user from database with role loaded
        user: Optional[User] = await get_user_by_email_with_role(db, email)
        if user is None:
            logger.debug(f"User not found for email: {email}")
            return None

        return user
    except HTTPException:
        # Re-raise HTTPExceptions without modification
        raise
    except ValueError as e:
        logger.warning(f"Optional authentication failed - invalid token: {e}")
        return None
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None
