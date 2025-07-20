"""
Unit tests for the auth_pak module.

Tests the enhanced authentication functions with Personal API Key (PAK) support.
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.models.api_key import ApiKey
from app.security.auth_pak import decode_access_token_enhanced, is_pak_token
from app.utils.jwt_pak import create_api_key_token
from app.utils.rsa_keys import clear_key_cache


class TestAuthPAK:
    """Test PAK authentication functions."""

    def setup_method(self):
        """Clear key cache before each test."""
        clear_key_cache()

    def teardown_method(self):
        """Clear key cache after each test."""
        clear_key_cache()

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_create_api_key_token_success(self):
        """Test successful API key token creation."""
        subject = "test@example.com"
        jti = str(uuid4())
        scopes = ["*"]

        # Create token without expiration
        token = create_api_key_token(subject, jti, scopes)

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token contains expected parts (header.payload.signature)
        parts = token.split(".")
        assert len(parts) == 3

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_create_api_key_token_with_expiration(self):
        """Test API key token creation with expiration."""
        subject = "test@example.com"
        jti = str(uuid4())
        scopes = ["read", "write"]
        expires_delta = timedelta(hours=1)

        token = create_api_key_token(subject, jti, scopes, expires_delta)

        # Verify token is created
        assert isinstance(token, str)
        assert len(token) > 0

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_create_api_key_token_with_scopes(self):
        """Test API key token creation with specific scopes."""
        subject = "test@example.com"
        jti = str(uuid4())
        scopes = ["read", "write", "admin"]

        token = create_api_key_token(subject, jti, scopes)

        # Verify token is created
        assert isinstance(token, str)
        assert len(token) > 0

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_create_api_key_token_invalid_key(self):
        """Test API key token creation with invalid key."""
        with patch("app.utils.jwt_pak.get_private_key") as mock_get_key:
            mock_get_key.side_effect = RuntimeError("Key loading failed")

            with pytest.raises(RuntimeError, match="Failed to create API key token"):
                create_api_key_token("test@example.com", str(uuid4()), ["*"])

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_decode_access_token_enhanced_session_token(self):
        """Test decoding session tokens (HS256)."""
        from app.security.auth import create_access_token
        from app.tests.mocks import create_mock_db_session

        # Create a real session token with HS256 algorithm
        session_token = create_access_token({"sub": "test@example.com"})

        async for db_mock in create_mock_db_session():
            result = await decode_access_token_enhanced(session_token, db_mock)
            assert result == ("test@example.com", False)

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_decode_access_token_enhanced_pak_token_success(self):
        """Test successful PAK token decoding."""
        from app.tests.mocks import create_mock_db_session

        # Create a test PAK token
        subject = "test@example.com"
        jti = str(uuid4())
        scopes = ["*"]
        token = create_api_key_token(subject, jti, scopes)

        # Create mock API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=jti,
            token_hash="test_hash",
            label="Test Key",
            scopes=scopes,
            created_at=datetime.now(timezone.utc),
            expires_at=None,
            last_used_at=None,
            revoked_at=None,
        )

        async for db_mock in create_mock_db_session():
            # Mock the session token decoder to fail
            with patch(
                "app.security.auth_pak.decode_session_token"
            ) as mock_session_decode:
                mock_session_decode.return_value = None

                # Mock the PAK verification functions
                with patch(
                    "app.security.auth_pak.verify_api_key_by_hash"
                ) as mock_verify:
                    mock_verify.return_value = api_key

                    with patch(
                        "app.security.auth_pak.update_api_key_last_used"
                    ) as mock_update:
                        mock_update.return_value = None

                        result = await decode_access_token_enhanced(token, db_mock)

                        assert result == (subject, True)
                        mock_verify.assert_called_once()
                        mock_update.assert_called_once_with(db_mock, api_key)

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_decode_access_token_enhanced_pak_token_revoked(self):
        """Test PAK token decoding with revoked token."""
        from app.tests.mocks import create_mock_db_session

        # Create a test PAK token
        subject = "test@example.com"
        jti = str(uuid4())
        scopes = ["*"]
        token = create_api_key_token(subject, jti, scopes)

        async for db_mock in create_mock_db_session():
            # Mock the session token decoder to fail
            with patch(
                "app.security.auth_pak.decode_session_token"
            ) as mock_session_decode:
                mock_session_decode.return_value = None

                # Mock the PAK verification to return None (revoked/expired)
                with patch(
                    "app.security.auth_pak.verify_api_key_by_hash"
                ) as mock_verify:
                    mock_verify.return_value = None

                    result = await decode_access_token_enhanced(token, db_mock)

                    assert result == (None, False)
                    mock_verify.assert_called_once()

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_decode_access_token_enhanced_invalid_token(self):
        """Test decoding invalid token."""
        from app.tests.mocks import create_mock_db_session

        async for db_mock in create_mock_db_session():
            # Mock the session token decoder to fail
            with patch(
                "app.security.auth_pak.decode_session_token"
            ) as mock_session_decode:
                mock_session_decode.return_value = None

                result = await decode_access_token_enhanced("invalid_token", db_mock)

                assert result == (None, False)

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_decode_access_token_enhanced_no_database(self):
        """Test PAK token decoding without database session."""
        # Create a test PAK token
        subject = "test@example.com"
        jti = str(uuid4())
        scopes = ["*"]
        token = create_api_key_token(subject, jti, scopes)

        # Mock the session token decoder to fail
        with patch("app.security.auth_pak.decode_session_token") as mock_session_decode:
            mock_session_decode.return_value = None

            # No database session provided
            result = await decode_access_token_enhanced(token, None)

            assert result == (None, False)

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_is_pak_token_success(self):
        """Test is_pak_token with valid PAK token."""
        # Create a test PAK token
        subject = "test@example.com"
        jti = str(uuid4())
        scopes = ["*"]
        token = create_api_key_token(subject, jti, scopes)

        result = await is_pak_token(token)

        assert result is True

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_is_pak_token_invalid(self):
        """Test is_pak_token with invalid token."""
        result = await is_pak_token("invalid_token")

        assert result is False

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_is_pak_token_session_token(self):
        """Test is_pak_token with session token."""
        # This would be a session token, not a PAK token
        result = await is_pak_token("session.token.here")

        assert result is False

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_token_structure_validation(self):
        """Test that created tokens have the correct structure."""
        from app.utils.jwt_pak import verify_api_jwt

        subject = "test@example.com"
        jti = str(uuid4())
        scopes = ["read", "write"]

        token = create_api_key_token(subject, jti, scopes)

        # Verify token structure
        payload = verify_api_jwt(token)

        assert payload is not None
        assert payload["sub"] == subject
        assert payload["jti"] == jti
        assert payload["type"] == "api_key"
        assert payload["scopes"] == scopes
        assert "iat" in payload

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_token_expiration_validation(self):
        """Test that tokens with expiration are properly validated."""
        from app.utils.jwt_pak import verify_api_jwt

        subject = "test@example.com"
        jti = str(uuid4())
        scopes = ["*"]
        expires_delta = timedelta(hours=1)

        token = create_api_key_token(subject, jti, scopes, expires_delta)

        # Verify token structure includes expiration
        payload = verify_api_jwt(token)

        assert payload is not None
        assert "exp" in payload

        # Verify expiration is in the future
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp_time > datetime.now(timezone.utc)
