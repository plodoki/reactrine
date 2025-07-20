"""
Unit tests for authentication API functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from app.api.deps import get_current_user_token
from app.core.config import Settings
from app.security.auth import create_csrf_token, get_password_hash, verify_password


def test_password_hashing_and_verification():
    """Test password hashing and verification functions."""
    password = "Test-Password-123!"
    hashed = get_password_hash(password)

    # The same password matches
    assert verify_password(password, hashed) is True

    # A different password does not match
    assert verify_password("wrong-password", hashed) is False


def test_csrf_token_generation():
    """Test CSRF token generation creates unique tokens."""
    token1 = create_csrf_token()
    token2 = create_csrf_token()

    assert token1 != token2
    assert len(token1) > 10
    assert len(token2) > 10


@pytest.mark.asyncio
async def test_csrf_validation_success():
    """Test CSRF validation passes when header matches cookie."""

    # Mock request with matching CSRF token
    request = MagicMock(spec=Request)
    request.cookies = {"csrf_token": "test-token", "access_token": "jwt-token"}
    request.headers = {"X-CSRF-Token": "test-token"}
    request.method = "POST"

    # Should return the access token
    token = await get_current_user_token(request, None)
    assert token == "jwt-token"


@pytest.mark.asyncio
async def test_csrf_validation_failure():
    """Test CSRF validation fails when header doesn't match cookie."""

    # Mock request with mismatched CSRF token
    request = MagicMock(spec=Request)
    request.cookies = {"csrf_token": "token1", "access_token": "jwt-token"}
    request.headers = {"X-CSRF-Token": "token2"}  # Different token
    request.method = "POST"

    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_token(request, None)

    assert exc_info.value.status_code == 403
    assert "CSRF" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_csrf_validation_skipped_for_get():
    """Test CSRF validation is skipped for GET requests."""

    # Mock request with mismatched CSRF token but GET method
    request = MagicMock(spec=Request)
    request.cookies = {"csrf_token": "token1", "access_token": "jwt-token"}
    request.headers = {"X-CSRF-Token": "token2"}  # Different token
    request.method = "GET"  # Safe method

    # Should return the access token (CSRF check skipped)
    token = await get_current_user_token(request, None)
    assert token == "jwt-token"


@pytest.mark.asyncio
async def test_csrf_validation_skipped_when_no_cookie():
    """Test CSRF validation is skipped when no CSRF cookie is present."""

    # Mock request without CSRF cookie
    request = MagicMock(spec=Request)
    request.cookies = {"access_token": "jwt-token"}  # No csrf_token
    request.headers = {}
    request.method = "POST"

    # Should return the access token (CSRF check skipped)
    token = await get_current_user_token(request, None)
    assert token == "jwt-token"


def test_settings_allow_registration():
    """Test that settings can control registration."""
    settings_allow = Settings(ALLOW_REGISTRATION=True, SECRET_KEY="test")
    settings_block = Settings(ALLOW_REGISTRATION=False, SECRET_KEY="test")

    assert settings_allow.ALLOW_REGISTRATION is True
    assert settings_block.ALLOW_REGISTRATION is False


def test_settings_registration_message():
    """Test that settings can provide custom registration message."""
    custom_message = "Custom registration disabled message"
    settings = Settings(
        ALLOW_REGISTRATION=False,
        SECRET_KEY="test",
        REGISTRATION_DISABLED_MESSAGE=custom_message,
    )

    assert settings.REGISTRATION_DISABLED_MESSAGE == custom_message


@pytest.mark.asyncio
async def test_refresh_token_generates_csrf_token():
    """Test that refresh endpoint generates a new CSRF token."""
    from datetime import datetime, timedelta, timezone

    from app.api.v1.endpoints.auth import refresh_access_token
    from app.models.refresh_token import RefreshToken
    from app.models.user import User

    # Create mock user
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.is_active = True

    # Create mock refresh token
    mock_refresh_token = MagicMock(spec=RefreshToken)
    mock_refresh_token.user = mock_user
    mock_refresh_token.is_revoked = False
    mock_refresh_token.is_expired = False
    mock_refresh_token.expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Mock database session
    mock_db = AsyncMock()

    # Mock response object
    mock_response = MagicMock()
    mock_response.set_cookie = MagicMock()

    # Mock the dependencies
    with (
        patch(
            "app.api.v1.endpoints.auth.get_refresh_token",
            return_value=mock_refresh_token,
        ),
        patch(
            "app.api.v1.endpoints.auth.rotate_refresh_token",
            return_value="new_refresh_token",
        ),
        patch(
            "app.api.v1.endpoints.auth.create_access_token",
            return_value="new_access_token",
        ),
        patch("app.api.v1.endpoints.auth.create_auth_cookies"),
        patch("app.api.v1.endpoints.auth.set_refresh_token_cookie"),
        patch(
            "app.api.v1.endpoints.auth.create_csrf_token", return_value="csrf_token_123"
        ) as mock_create_csrf,
        patch("app.api.v1.endpoints.auth.get_settings") as mock_get_settings,
    ):

        # Mock settings
        mock_settings = MagicMock()
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.ENVIRONMENT = "development"
        mock_get_settings.return_value = mock_settings

        # Call the refresh endpoint
        result = await refresh_access_token(
            response=mock_response, refresh_token="old_refresh_token", db=mock_db
        )

        # Verify the result
        assert result == {"message": "Access token refreshed successfully."}

        # Verify that CSRF token was created
        mock_create_csrf.assert_called_once()

        # Verify that CSRF token cookie was set
        mock_response.set_cookie.assert_called_with(
            key="csrf_token",
            value="csrf_token_123",
            max_age=30 * 60,  # ACCESS_TOKEN_EXPIRE_MINUTES * 60
            httponly=False,
            secure=False,  # development environment
            samesite="lax",
        )
