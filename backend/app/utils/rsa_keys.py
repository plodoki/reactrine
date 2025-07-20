"""
RSA key management utilities for Personal API Keys (PAKs).

This module handles reading RSA key pairs from the secrets directory
and provides utilities for JWT signing and verification.
"""

import os
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk
from jose.constants import ALGORITHMS

from app.utils.secrets import read_secret

# Cache for loaded keys to avoid file I/O on every request
_private_key_cache: Optional[rsa.RSAPrivateKey] = None
_public_key_cache: Optional[rsa.RSAPublicKey] = None


def get_private_key() -> rsa.RSAPrivateKey:
    """
    Get the RSA private key for signing PAK tokens.

    Returns:
        RSA private key for signing

    Raises:
        ValueError: If private key file is not found or invalid
        RuntimeError: If key cannot be loaded
    """
    global _private_key_cache

    if _private_key_cache is not None:
        return _private_key_cache

    # For test environment, allow a default test key
    if os.getenv("ENVIRONMENT") == "test":
        # Generate a simple test key in memory
        test_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        _private_key_cache = test_key
        return test_key

    # Read from secrets
    private_key_pem = read_secret("pak_private_key")
    if not private_key_pem:
        raise ValueError(
            "PAK private key not found. Run 'python scripts/generate-pak-keypair.py' "
            "to generate the RSA key pair, or ensure 'pak_private_key.txt' exists "
            "in the secrets/ directory."
        )

    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"), password=None
        )

        if not isinstance(private_key, rsa.RSAPrivateKey):
            raise ValueError("Private key must be an RSA key")

        _private_key_cache = private_key
        return private_key

    except (OSError, PermissionError) as e:
        raise RuntimeError(f"File access error loading PAK private key: {e}") from e
    except ValueError as e:
        raise RuntimeError(f"Invalid PAK private key format: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to load PAK private key: {e}") from e


def get_public_key() -> rsa.RSAPublicKey:
    """
    Get the RSA public key for verifying PAK tokens.

    Returns:
        RSA public key for verification

    Raises:
        ValueError: If public key file is not found or invalid
        RuntimeError: If key cannot be loaded
    """
    global _public_key_cache

    if _public_key_cache is not None:
        return _public_key_cache

    # For test environment, derive from private key
    if os.getenv("ENVIRONMENT") == "test":
        private_key = get_private_key()
        public_key = private_key.public_key()
        _public_key_cache = public_key
        return public_key

    # Read from secrets
    public_key_pem = read_secret("pak_public_key")
    if not public_key_pem:
        raise ValueError(
            "PAK public key not found. Run 'python scripts/generate-pak-keypair.py' "
            "to generate the RSA key pair, or ensure 'pak_public_key.txt' exists "
            "in the secrets/ directory."
        )

    try:
        public_key_generic = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8")
        )

        if not isinstance(public_key_generic, rsa.RSAPublicKey):
            raise ValueError("Public key must be an RSA key")

        _public_key_cache = public_key_generic
        return public_key_generic

    except (OSError, PermissionError) as e:
        raise RuntimeError(f"File access error loading PAK public key: {e}") from e
    except ValueError as e:
        raise RuntimeError(f"Invalid PAK public key format: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to load PAK public key: {e}") from e


def get_jwks() -> Dict[str, Any]:
    """
    Get the JSON Web Key Set (JWKS) for the public key.

    This is used for the /.well-known/jwks.json endpoint to publish
    the public key for token verification.

    Returns:
        JWKS dictionary containing the public key
    """
    public_key = get_public_key()

    # Convert RSA key to PEM format for jwk.construct
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Convert to JWK format
    jwk_dict = jwk.construct(public_key_pem, algorithm=ALGORITHMS.RS256).to_dict()

    # Add key ID and use
    jwk_dict["kid"] = "pak-key-1"  # Key ID for rotation support
    jwk_dict["use"] = "sig"  # Key is used for signatures
    jwk_dict["alg"] = "RS256"  # Algorithm

    return {"keys": [jwk_dict]}


def clear_key_cache() -> None:
    """
    Clear the key cache. Useful for tests or key rotation.
    """
    global _private_key_cache, _public_key_cache
    _private_key_cache = None
    _public_key_cache = None
