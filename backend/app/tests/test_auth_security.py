"""
Unit tests for authentication security utilities and user service.

These tests cover:
- Password hashing and verification
- JWT access token creation and decoding (including expiration handling)
- Authentication cookie helpers
- CSRF token generation
- User service create_user functionality
"""

from datetime import timedelta

import pytest
from fastapi import Response

from app.schemas.user import UserCreate
from app.security import auth as auth_utils
from app.services.user import create_user

# ---------------------------------------------------------------------------
# Password hashing & verification
# ---------------------------------------------------------------------------


def test_password_hashing_and_verification():
    """Hashing a password and verifying it should round-trip correctly."""
    password = "Strong-Password-123!"
    hashed = auth_utils.get_password_hash(password)

    # The same password matches
    assert auth_utils.verify_password(password, hashed) is True

    # A different password does not match
    assert auth_utils.verify_password("wrong-password", hashed) is False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def test_access_token_creation_and_decoding():
    """A freshly created token should decode back to the original subject."""
    email = "user@example.com"
    token = auth_utils.create_access_token({"sub": email})

    decoded_email = auth_utils.decode_access_token(token)
    assert decoded_email == email


def test_access_token_expired_token_returns_none():
    """Decoding an expired token should return None."""
    email = "expired@example.com"

    # Create a token that is already expired
    token = auth_utils.create_access_token(
        {"sub": email}, expires_delta=timedelta(seconds=-1)
    )

    decoded = auth_utils.decode_access_token(token)
    assert decoded is None


# ---------------------------------------------------------------------------
# Cookie helpers
# ---------------------------------------------------------------------------


def test_create_and_clear_auth_cookies():
    """Auth cookies should be set and cleared with correct names/flags."""
    response = Response()
    token = "dummy-token"

    # Create cookies
    auth_utils.create_auth_cookies(response, token)
    set_cookie_header = response.headers.get("set-cookie")

    # Ensure the cookie header contains expected attributes
    assert "access_token=" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
    assert "SameSite=lax" in set_cookie_header

    # Clear cookies on a new response (to avoid header merge complexity)
    clear_response = Response()
    auth_utils.clear_auth_cookies(clear_response)
    clear_cookie_header = clear_response.headers.get("set-cookie")

    # After clearing, the cookie should be deleted (Max-Age=0 or expires)
    assert "access_token=" in clear_cookie_header
    assert (
        "Max-Age=0" in clear_cookie_header or "expires=" in clear_cookie_header.lower()
    )


# ---------------------------------------------------------------------------
# CSRF helpers
# ---------------------------------------------------------------------------


def test_csrf_token_generation_is_random():
    """Two generated CSRF tokens should be unique and non-empty."""
    t1 = auth_utils.create_csrf_token()
    t2 = auth_utils.create_csrf_token()

    assert t1 != t2
    assert len(t1) >= 10
    assert len(t2) >= 10


# ---------------------------------------------------------------------------
# User service
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_user_hashes_password(mock_db_session):
    """create_user should hash the password before storing and add the user to the DB."""
    user_create = UserCreate(email="newuser@example.com", password="MySecretPwd123!")

    user = await create_user(mock_db_session, user_create)

    # Email should be preserved
    assert user.email == user_create.email

    # Password must be hashed and verify correctly
    assert user.hashed_password != user_create.password
    assert auth_utils.verify_password(user_create.password, user.hashed_password)

    # DB add & commit should have been called
    mock_db_session.add.assert_called_once_with(user)
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(user)
