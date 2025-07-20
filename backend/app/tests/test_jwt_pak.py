"""
Tests for PAK JWT utilities.
"""

import os
from datetime import timedelta
from unittest.mock import patch

from app.utils.jwt_pak import (
    compute_token_hash,
    create_api_jwt,
    decode_api_jwt_unsafe,
    extract_jti_from_token,
    verify_api_jwt,
)
from app.utils.rsa_keys import clear_key_cache


class TestJWTPAK:
    """Test PAK JWT functionality."""

    def setup_method(self):
        """Clear key cache before each test."""
        clear_key_cache()

    def teardown_method(self):
        """Clear key cache after each test."""
        clear_key_cache()

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_create_api_jwt_without_expiry(self):
        """Test creating API JWT without expiration."""
        email = "test@example.com"

        token, jti, token_hash = create_api_jwt(email)

        # Verify return values
        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(jti, str)
        assert len(jti) == 36  # UUID4 length
        assert isinstance(token_hash, str)
        assert len(token_hash) == 64  # SHA256 hex length

        # Verify token can be decoded
        payload = decode_api_jwt_unsafe(token)
        assert payload is not None
        assert payload["sub"] == email
        assert payload["jti"] == jti
        assert payload["type"] == "api_key"
        assert "iat" in payload
        assert "exp" not in payload  # No expiry

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_create_api_jwt_with_expiry(self):
        """Test creating API JWT with expiration."""
        email = "test@example.com"
        expires_delta = timedelta(days=30)

        token, jti, token_hash = create_api_jwt(email, expires_delta)

        # Verify token can be decoded
        payload = decode_api_jwt_unsafe(token)
        assert payload is not None
        assert payload["sub"] == email
        assert payload["jti"] == jti
        assert payload["type"] == "api_key"
        assert "iat" in payload
        assert "exp" in payload  # Has expiry

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_verify_api_jwt_valid_token(self):
        """Test verifying a valid API JWT."""
        email = "test@example.com"

        token, jti, _ = create_api_jwt(email)

        # Verify token
        payload = verify_api_jwt(token)
        assert payload is not None
        assert payload["sub"] == email
        assert payload["jti"] == jti
        assert payload["type"] == "api_key"

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_verify_api_jwt_invalid_token(self):
        """Test verifying an invalid JWT."""
        invalid_token = "invalid.jwt.token"

        payload = verify_api_jwt(invalid_token)
        assert payload is None

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_verify_api_jwt_wrong_type(self):
        """Test that non-API key tokens are rejected."""
        # Create a regular session-style token (without RSA signing)
        from jose import jwt

        claims = {
            "sub": "test@example.com",
            "type": "session",  # Wrong type
            "jti": "some-jti",
        }

        # Sign with a dummy key (this won't verify with our RSA key anyway)
        token = jwt.encode(claims, "dummy-secret", algorithm="HS256")

        payload = verify_api_jwt(token)
        assert payload is None

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_decode_api_jwt_unsafe(self):
        """Test unsafe decoding of JWT."""
        email = "test@example.com"

        token, jti, _ = create_api_jwt(email)

        # Decode without verification
        payload = decode_api_jwt_unsafe(token)
        assert payload is not None
        assert payload["sub"] == email
        assert payload["jti"] == jti
        assert payload["type"] == "api_key"

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_compute_token_hash(self):
        """Test token hash computation."""
        email = "test@example.com"

        token, _, expected_hash = create_api_jwt(email)

        # Compute hash manually
        computed_hash = compute_token_hash(token)
        assert computed_hash == expected_hash
        assert len(computed_hash) == 64  # SHA256 hex length

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_extract_jti_from_token(self):
        """Test JTI extraction from token."""
        email = "test@example.com"

        token, expected_jti, _ = create_api_jwt(email)

        # Extract JTI
        extracted_jti = extract_jti_from_token(token)
        assert extracted_jti == expected_jti

    def test_extract_jti_from_invalid_token(self):
        """Test JTI extraction from invalid token."""
        invalid_token = "invalid.jwt.token"

        jti = extract_jti_from_token(invalid_token)
        assert jti is None

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_token_uniqueness(self):
        """Test that each created token is unique."""
        email = "test@example.com"

        token1, jti1, hash1 = create_api_jwt(email)
        token2, jti2, hash2 = create_api_jwt(email)

        # All values should be different
        assert token1 != token2
        assert jti1 != jti2
        assert hash1 != hash2
