"""Cookie management for authentication and security."""

from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User

from .tokens import REFRESH_TOKEN_COOKIE_NAME, create_csrf_token, create_refresh_token

__all__ = [
    "set_refresh_token_cookie",
    "create_auth_cookies",
    "create_auth_cookies_with_csrf",
    "clear_auth_cookies",
]


def set_refresh_token_cookie(response: Response, token: str) -> None:
    """
    Set the refresh token in a secure, HttpOnly cookie.

    Args:
        response: FastAPI response object
        token: The refresh token string
    """
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=token,
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )


def create_auth_cookies(response: Response, token: str) -> None:
    """
    Set HttpOnly authentication cookies with secure attributes.

    Args:
        response: FastAPI response object
        token: JWT token to store in cookies
    """
    settings = get_settings()
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )


async def create_auth_cookies_with_csrf(
    response: Response, access_token: str, db: AsyncSession, user: User
) -> str:
    """
    Set both authentication and CSRF cookies with secure attributes.

    Args:
        response: FastAPI response object
        access_token: JWT token to store in cookies
        db: Async database session
        user: The authenticated user object

    Returns:
        Generated CSRF token
    """
    settings = get_settings()

    # Set the main authentication cookie
    create_auth_cookies(response, access_token)

    # Generate and set refresh token
    if user.id is not None:
        refresh_token = await create_refresh_token(db, user.id)
        set_refresh_token_cookie(response, refresh_token)

    # Generate and set CSRF token
    csrf_token = create_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=False,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )

    return csrf_token


def clear_auth_cookies(response: Response) -> None:
    """
    Clear all authentication cookies from the response.

    Args:
        response: FastAPI response object
    """
    settings = get_settings()
    response.delete_cookie(
        "access_token",
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )
    response.delete_cookie(
        "csrf_token",
        httponly=False,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )
    response.delete_cookie(
        REFRESH_TOKEN_COOKIE_NAME,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )
