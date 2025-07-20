"""JWT and refresh token management."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository

__all__ = [
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
]

# Token constants
REFRESH_TOKEN_EXPIRE_DAYS = 30
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a new JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (defaults to settings value)

    Returns:
        Encoded JWT token
    """
    settings = get_settings()
    to_encode = data.copy()

    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now_utc})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token to decode

    Returns:
        Email from token if valid, None otherwise
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            return None
        return str(email)
    except JWTError:
        return None


async def create_refresh_token(db: AsyncSession, user_id: int) -> str:
    """
    Create, store, and return a new refresh token.

    Args:
        db: Async database session
        user_id: The user's ID

    Returns:
        The generated refresh token string

    Raises:
        ValueError: If user_id is not a positive integer
    """
    # Validate user_id parameter
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer")

    token = secrets.token_urlsafe(64)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token_obj = RefreshToken(
        token=token, user_id=user_id, expires_at=expires_at
    )

    refresh_token_repo = RefreshTokenRepository()
    await refresh_token_repo.create(db, refresh_token_obj)

    return token


async def get_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    """
    Retrieve a refresh token from the database.

    Args:
        db: Async database session
        token: The refresh token string

    Returns:
        The RefreshToken object or None if not found
    """
    refresh_token_repo = RefreshTokenRepository()
    return await refresh_token_repo.get_by_token(db, token)


async def revoke_refresh_token(db: AsyncSession, token: str) -> None:
    """
    Revoke a refresh token by setting its `revoked_at` timestamp.

    Args:
        db: Async database session
        token: The refresh token string to revoke
    """
    token_obj = await get_refresh_token(db, token)
    if token_obj:
        token_obj.revoked_at = datetime.now(timezone.utc)
        refresh_token_repo = RefreshTokenRepository()
        await refresh_token_repo.update(db, token_obj)


async def rotate_refresh_token(
    db: AsyncSession, old_token: str, user: User
) -> Optional[str]:
    """
    Revoke an old refresh token and issue a new one.

    Args:
        db: Async database session
        old_token: The refresh token string to revoke
        user: The user object

    Returns:
        The new refresh token string, or None if rotation fails
    """
    await revoke_refresh_token(db, old_token)
    if user.id is None:
        return None
    return await create_refresh_token(db, user.id)


def create_csrf_token() -> str:
    """
    Generate a CSRF token for double-submit cookie protection.

    Returns:
        Random CSRF token
    """
    return secrets.token_urlsafe(32)


def validate_csrf_token(token_from_header: str, token_from_cookie: str) -> bool:
    """
    Validate CSRF token from header against the one from the cookie.

    Args:
        token_from_header: CSRF token from the X-CSRF-Token header
        token_from_cookie: CSRF token from the csrf_token cookie

    Returns:
        True if tokens are valid and match, False otherwise
    """
    if not token_from_header or not token_from_cookie:
        return False
    return secrets.compare_digest(token_from_header, token_from_cookie)
