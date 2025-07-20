"""Core authentication functionality."""

from passlib.context import CryptContext

# Import all functionality from new modules for backward compatibility
from .cookies import (
    clear_auth_cookies,
    create_auth_cookies,
    create_auth_cookies_with_csrf,
    set_refresh_token_cookie,
)
from .tokens import (
    REFRESH_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    decode_access_token,
    get_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
    validate_csrf_token,
)

__all__ = [
    # Password hashing
    "verify_password",
    "get_password_hash",
    # JWT and refresh tokens (re-exported from tokens module)
    "create_access_token",
    "decode_access_token",
    "create_refresh_token",
    "get_refresh_token",
    "revoke_refresh_token",
    "rotate_refresh_token",
    "create_csrf_token",
    "validate_csrf_token",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "REFRESH_TOKEN_COOKIE_NAME",
    # Cookie management (re-exported from cookies module)
    "set_refresh_token_cookie",
    "create_auth_cookies",
    "create_auth_cookies_with_csrf",
    "clear_auth_cookies",
]

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password

    Returns:
        The hashed password
    """
    return pwd_context.hash(password)
