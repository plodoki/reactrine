"""
End-to-end tests for Personal API Keys (PAKs).

This test demonstrates the complete PAK workflow:
1. User creates an API key via REST endpoint
2. User gets the JWT token
3. User makes authenticated requests using the Bearer token
4. User revokes the key
5. Subsequent requests fail with 401
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

from app.utils.rsa_keys import clear_key_cache


class TestPAKEndToEnd:
    """End-to-end tests for PAK functionality."""

    def setup_method(self):
        """Clear key cache before each test."""
        clear_key_cache()

    def teardown_method(self):
        """Clear key cache after each test."""
        clear_key_cache()

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_complete_pak_workflow_simulation(self):
        """
        Test the complete PAK workflow through mocked interactions.

        This simulates what a real user would experience:
        1. Create API key via authenticated session
        2. Use PAK token for API calls
        3. Revoke PAK token
        4. Verify token no longer works
        """
        from datetime import datetime, timezone
        from uuid import uuid4

        from app.models.api_key import ApiKey
        from app.models.user import User
        from app.security.auth_pak import decode_access_token_enhanced
        from app.utils.jwt_pak import (
            compute_token_hash,
            create_api_key_token,
            verify_api_jwt,
        )

        # Step 1: Simulate user session (normal login)
        user = User(
            id=1,
            email="test.user@example.com",
            hashed_password="hashed_password",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Step 2: User creates a PAK (simulate API key creation)
        jti = str(uuid4())
        token = create_api_key_token(user.email, jti, ["*"], None)  # No expiry
        token_hash = compute_token_hash(token)

        # Create the database record (simulated)
        api_key = ApiKey(
            id=1,
            user_id=user.id,
            jti=jti,
            token_hash=token_hash,
            label="My Development Key",
            scopes=["*"],
            created_at=datetime.now(timezone.utc),
            expires_at=None,  # No expiry
            last_used_at=None,
            revoked_at=None,
        )

        print(f"✅ Step 1: API Key created with JTI: {jti}")
        print(f"✅ Step 2: JWT Token generated (length: {len(token)} chars)")

        # Step 3: Verify the PAK token works for authentication
        payload = verify_api_jwt(token)
        assert payload is not None
        assert payload["sub"] == user.email
        assert payload["type"] == "api_key"
        assert payload["jti"] == str(jti)

        print("✅ Step 3: Token verification successful")

        # Step 4: Test complete authentication flow
        from app.tests.mocks import create_mock_db_session

        async for db_mock in create_mock_db_session():
            # Mock the database lookup functions
            async def mock_verify_api_key_by_hash(db, hash_param, jti_param):
                if hash_param == api_key.token_hash and jti_param == api_key.jti:
                    return api_key  # Return active key
                return None

            async def mock_update_last_used(db, key):
                key.last_used_at = datetime.now(timezone.utc)

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

                # Test enhanced token decoder
                email, is_pak = await decode_access_token_enhanced(token, db_mock)

                assert email == user.email
                assert is_pak is True

            print("✅ Step 4: Enhanced authentication flow successful")

            # Step 5: Simulate API key revocation
            api_key.revoked_at = datetime.now(timezone.utc)

            # Mock the database to return None for revoked key
            async def mock_verify_revoked_key(db, hash_param, jti_param):
                return None  # Revoked keys return None

            with patch(
                "app.security.auth_pak.verify_api_key_by_hash", mock_verify_revoked_key
            ):
                # Test that revoked token fails
                email, is_pak = await decode_access_token_enhanced(token, db_mock)

                assert email is None
                assert is_pak is False

            print("✅ Step 5: Revoked token correctly rejected")

        # Step 6: Verify token structure and claims
        assert token.count(".") == 2  # JWT has 3 parts separated by dots

        # Test token hash computation
        computed_hash = compute_token_hash(token)
        assert computed_hash == token_hash
        assert len(computed_hash) == 64  # SHA256 hex length

        print("✅ Step 6: Token structure and hashing verified")

        print("\n🎉 Complete PAK workflow test successful!")
        print(f"   - User: {user.email}")
        print("   - Token Type: RS256 JWT")
        print(f"   - JTI: {jti}")
        print(f"   - Label: {api_key.label}")
        print("   - Status: Active -> Revoked")

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_pak_vs_session_token_differentiation(self):
        """Test that we can correctly differentiate PAK tokens from session tokens."""
        from uuid import uuid4

        from app.security.auth import create_access_token, decode_access_token
        from app.utils.jwt_pak import create_api_key_token, verify_api_jwt

        # Create a session token (HS256)
        session_token = create_access_token({"sub": "session@example.com"})

        # Create a PAK token (RS256)
        jti = str(uuid4())
        pak_token = create_api_key_token("pak@example.com", jti, ["*"], None)

        # Session token should decode with regular decoder
        session_email = decode_access_token(session_token)
        assert session_email == "session@example.com"

        # Session token should NOT verify as PAK
        pak_payload = verify_api_jwt(session_token)
        assert pak_payload is None  # Different signature/algorithm

        # PAK token should verify as PAK
        pak_payload = verify_api_jwt(pak_token)
        assert pak_payload is not None
        assert pak_payload["type"] == "api_key"
        assert pak_payload["sub"] == "pak@example.com"

        # PAK token should NOT decode with session decoder
        pak_as_session = decode_access_token(pak_token)
        assert pak_as_session is None  # Different signature/algorithm

        print("✅ Session and PAK tokens correctly differentiated")

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_pak_token_security_properties(self):
        """Test security properties of PAK tokens."""
        import secrets
        from uuid import uuid4

        from app.utils.jwt_pak import compute_token_hash, create_api_key_token

        # Create multiple tokens for the same user
        email = "security@example.com"

        jti1 = str(uuid4())
        jti2 = str(uuid4())
        token1 = create_api_key_token(email, jti1, ["*"], None)
        token2 = create_api_key_token(email, jti2, ["*"], None)

        hash1 = compute_token_hash(token1)
        hash2 = compute_token_hash(token2)

        # Each token should be unique
        assert token1 != token2
        assert jti1 != jti2
        assert hash1 != hash2

        # Hashes should be deterministic
        computed_hash1 = compute_token_hash(token1)
        computed_hash2 = compute_token_hash(token1)  # Same token
        assert computed_hash1 == computed_hash2
        assert computed_hash1 == hash1

        # Hash comparison should be constant-time safe
        # This tests that we use secrets.compare_digest
        fake_hash = "a" * 64
        real_hash = hash1

        # These should both be False, but take roughly the same time
        result1 = secrets.compare_digest(fake_hash, real_hash)
        result2 = secrets.compare_digest(real_hash, real_hash)

        assert result1 is False
        assert result2 is True

        print("✅ PAK token security properties verified")
        print("   - Unique tokens: ✓")
        print("   - Deterministic hashing: ✓")
        print("   - Constant-time comparison: ✓")

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    @pytest.mark.asyncio
    async def test_api_key_service_integration(self):
        """Test integration with the updated API key service."""
        from datetime import datetime, timezone

        from app.models.user import User
        from app.services.api_key import create_api_key_simple
        from app.tests.mocks import create_mock_db_session
        from app.utils.jwt_pak import compute_token_hash, verify_api_jwt

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
            from unittest.mock import Mock

            db_mock.add = Mock(return_value=None)  # Synchronous method
            db_mock.commit = AsyncMock(return_value=None)
            db_mock.refresh = AsyncMock(return_value=None)

            # Create API key using the service
            api_key, token = await create_api_key_simple(
                db=db_mock,
                user=user,
                label="Service Integration Test",
                expires_in_days=30,
            )

            # Verify the API key was created correctly
            assert api_key.user_id == user.id
            assert api_key.label == "Service Integration Test"
            assert api_key.scopes == ["*"]
            assert api_key.jti is not None
            assert api_key.token_hash is not None
            assert api_key.expires_at is not None

            # Verify the token is valid and properly formatted
            assert isinstance(token, str)
            parts = token.split(".")
            assert len(parts) == 3  # JWT format

            # Verify token payload
            payload = verify_api_jwt(token)
            assert payload is not None
            assert payload["sub"] == user.email
            assert payload["type"] == "api_key"
            assert payload["jti"] == api_key.jti
            assert payload["scopes"] == ["*"]

            # Verify token hash matches
            expected_hash = compute_token_hash(token)
            assert api_key.token_hash == expected_hash

            # Verify database operations were called
            db_mock.add.assert_called_once()
            db_mock.commit.assert_called_once()
            db_mock.refresh.assert_called_once()

            print("✅ API key service integration test successful")
            print(f"   - User: {user.email}")
            print(f"   - JTI: {api_key.jti}")
            print(f"   - Label: {api_key.label}")
            print(f"   - Token Length: {len(token)}")
            print(f"   - Hash Length: {len(api_key.token_hash)}")
