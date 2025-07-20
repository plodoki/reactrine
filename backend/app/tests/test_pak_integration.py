"""
Integration tests for PAK (Personal Access Key) authentication.

These tests verify the complete PAK authentication flow including token creation,
verification, and integration with the API key service.
"""

import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.models.api_key import ApiKey
from app.models.user import User
from app.security.auth_pak import decode_access_token_enhanced
from app.utils.jwt_pak import compute_token_hash, create_api_key_token
from app.utils.rsa_keys import clear_key_cache


class TestPAKIntegration:
    """Test PAK authentication integration."""

    def setup_method(self):
        """Clear key cache before each test."""
        clear_key_cache()

    def teardown_method(self):
        """Clear key cache after each test."""
        clear_key_cache()

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_pak_token_authentication_flow(self):
        """Test complete PAK token authentication flow."""
        from app.tests.mocks import create_mock_db_session

        # Create a test user
        user = User(
            id=1,
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Generate JTI and create PAK token using new function
        jti = str(uuid4())
        token = create_api_key_token(user.email, jti, ["*"], None)
        token_hash = compute_token_hash(token)

        # Create a test API key
        api_key = ApiKey(
            id=1,
            user_id=1,
            jti=jti,
            token_hash=token_hash,
            label="Test Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            expires_at=None,  # No expiry
            last_used_at=None,
            revoked_at=None,
        )

        async for db_mock in create_mock_db_session():
            # Mock the service functions
            async def mock_get_api_key_by_jti(db, jti_param):
                if jti_param == api_key.jti:
                    return api_key
                return None

            async def mock_verify_api_key_by_hash(db, hash_param, jti_param):
                if hash_param == api_key.token_hash and jti_param == api_key.jti:
                    return api_key
                return None

            async def mock_update_last_used(db, key):
                # Simulate updating last_used_at
                key.last_used_at = datetime.now(timezone.utc)

            # Patch the service functions
            with (
                patch(
                    "app.security.auth_pak.verify_api_key_by_hash",
                    mock_verify_api_key_by_hash,
                ),
                patch(
                    "app.security.auth_pak.update_api_key_last_used",
                    mock_update_last_used,
                ),
            ):

                # Test token decoding
                email, is_pak = await decode_access_token_enhanced(token, db_mock)

                # Verify results
                assert email == user.email
                assert is_pak is True

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_session_token_still_works(self):
        """Test that regular session tokens still work."""
        from app.security.auth import create_access_token
        from app.tests.mocks import create_mock_db_session

        # Create a regular session token
        email = "session@example.com"
        session_token = create_access_token({"sub": email})

        async for db_mock in create_mock_db_session():
            # Test token decoding
            decoded_email, is_pak = await decode_access_token_enhanced(
                session_token, db_mock
            )

            # Verify results
            assert decoded_email == email
            assert is_pak is False  # Not a PAK token

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self):
        """Test that invalid tokens return None."""
        from app.tests.mocks import create_mock_db_session

        invalid_token = "invalid.jwt.token"

        async for db_mock in create_mock_db_session():
            # Test token decoding
            email, is_pak = await decode_access_token_enhanced(invalid_token, db_mock)

            # Verify results
            assert email is None
            assert is_pak is False

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_revoked_pak_token_fails(self):
        """Test that revoked PAK tokens are rejected."""
        from app.tests.mocks import create_mock_db_session

        # Create user and API key
        user_email = "revoked@example.com"
        jti = str(uuid4())
        token = create_api_key_token(user_email, jti, ["*"], None)

        # Token corresponds to a revoked API key (simulated)

        async for db_mock in create_mock_db_session():
            # Mock service to return revoked key
            async def mock_verify_revoked_key(db, hash_param, jti_param):
                # The verify function should return None for revoked keys
                return None

            with patch(
                "app.security.auth_pak.verify_api_key_by_hash", mock_verify_revoked_key
            ):
                # Test token decoding
                email, is_pak = await decode_access_token_enhanced(token, db_mock)

                # Verify results - should fail
                assert email is None
                assert is_pak is False

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_api_key_service_integration(self):
        """Test integration with the API key service."""
        from app.services.api_key import create_api_key_simple
        from app.tests.mocks import create_mock_db_session

        # Create a test user
        user = User(
            id=1,
            email="service@example.com",
            hashed_password="hashed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        async for db_mock in create_mock_db_session():
            # Mock database operations
            db_mock.add = Mock(return_value=None)  # Synchronous method
            db_mock.commit = AsyncMock(return_value=None)
            db_mock.refresh = AsyncMock(return_value=None)

            # Create API key using the service
            api_key, token = await create_api_key_simple(
                db=db_mock, user=user, label="Integration Test Key", expires_in_days=30
            )

            # Verify the API key was created correctly
            assert api_key.user_id == user.id
            assert api_key.label == "Integration Test Key"
            assert api_key.scopes == ["*"]
            assert api_key.jti is not None
            assert api_key.token_hash is not None
            assert api_key.expires_at is not None

            # Verify the token is valid
            assert isinstance(token, str)
            parts = token.split(".")
            assert len(parts) == 3  # JWT format

            # Verify token hash matches
            expected_hash = compute_token_hash(token)
            assert api_key.token_hash == expected_hash

            # Verify database operations were called
            db_mock.add.assert_called_once()
            db_mock.commit.assert_called_once()
            db_mock.refresh.assert_called_once()
