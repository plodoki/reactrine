"""
Tests for JWKS (JSON Web Key Set) functionality.
"""

import os
from unittest.mock import patch

from app.utils.rsa_keys import (
    clear_key_cache,
    get_jwks,
    get_private_key,
    get_public_key,
)


class TestJWKS:
    """Test JWKS functionality."""

    def setup_method(self):
        """Clear key cache before each test."""
        clear_key_cache()

    def teardown_method(self):
        """Clear key cache after each test."""
        clear_key_cache()

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_get_private_key_test_environment(self):
        """Test that private key generation works in test environment."""
        private_key = get_private_key()
        assert private_key is not None
        assert private_key.key_size == 2048

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_get_public_key_test_environment(self):
        """Test that public key derivation works in test environment."""
        public_key = get_public_key()
        assert public_key is not None
        assert public_key.key_size == 2048

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_get_jwks_test_environment(self):
        """Test that JWKS generation works in test environment."""
        jwks = get_jwks()

        # Verify JWKS structure
        assert "keys" in jwks
        assert len(jwks["keys"]) == 1

        key = jwks["keys"][0]

        # Verify key properties
        assert key["kty"] == "RSA"  # Key type
        assert key["use"] == "sig"  # Key use
        assert key["alg"] == "RS256"  # Algorithm
        assert key["kid"] == "pak-key-1"  # Key ID

        # Verify RSA-specific fields
        assert "n" in key  # Modulus
        assert "e" in key  # Exponent

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_key_caching(self):
        """Test that keys are cached properly."""
        # First call should generate keys
        private_key_1 = get_private_key()
        public_key_1 = get_public_key()

        # Second call should return cached keys (same objects)
        private_key_2 = get_private_key()
        public_key_2 = get_public_key()

        assert private_key_1 is private_key_2
        assert public_key_1 is public_key_2

    @patch.dict(os.environ, {"ENVIRONMENT": "test"})
    def test_clear_key_cache(self):
        """Test that key cache can be cleared."""
        # Get keys to populate cache
        private_key_1 = get_private_key()
        public_key_1 = get_public_key()

        # Clear cache
        clear_key_cache()

        # Get keys again - should be different objects
        private_key_2 = get_private_key()
        public_key_2 = get_public_key()

        assert private_key_1 is not private_key_2
        assert public_key_1 is not public_key_2
