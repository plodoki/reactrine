"""
JWT utilities for Personal API Keys (PAKs).

This module provides functions for creating and verifying RS256-signed JWT tokens
that serve as Personal API Keys. These tokens are separate from the regular
HS256 session tokens used for cookie-based authentication.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from jose import JWTError, jwt
from jose.constants import ALGORITHMS

from app.utils.rsa_keys import get_private_key, get_public_key


def create_api_key_token(
    subject: str, jti: str, scopes: list[str], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a Personal API Key (PAK) JWT token using RS256 algorithm.

    Args:
        subject: User email/identifier for the token
        jti: JWT ID (unique identifier) for the token
        scopes: List of scopes for the token (e.g., ["*"] for full access)
        expires_delta: Optional expiration time delta

    Returns:
        JWT token string signed with RS256

    Raises:
        RuntimeError: If token creation fails
    """
    try:
        # Prepare token claims
        now_utc = datetime.now(timezone.utc)
        claims = {
            "sub": subject,  # Subject (user email)
            "jti": jti,  # JWT ID for revocation (use provided JTI)
            "type": "api_key",  # Token type to distinguish from session tokens
            "iat": now_utc,  # Issued at
            "scopes": scopes,  # Token scopes
        }

        # Add expiration if specified
        if expires_delta:
            claims["exp"] = now_utc + expires_delta

        # Get private key for signing
        private_key = get_private_key()

        # Convert private key to PEM format for jose library
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Create JWT token
        token = jwt.encode(
            claims,
            private_key_pem,
            algorithm=ALGORITHMS.RS256,
            headers={"kid": "pak-key-1"},  # Key ID for rotation support
        )

        return token

    except ValueError as e:
        raise RuntimeError(f"Invalid token configuration: {e}") from e
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Key access error creating API key token: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to create API key token: {e}") from e


def create_api_jwt(
    email: str, expires_delta: Optional[timedelta] = None
) -> tuple[str, str, str]:
    """
    Create a Personal API Key (PAK) JWT token.

    Args:
        email: User email to include in the token
        expires_delta: Token expiration time (optional for no-expiry tokens)

    Returns:
        Tuple of (jwt_token, jti, token_hash)
        - jwt_token: The signed JWT string
        - jti: The unique token identifier
        - token_hash: SHA256 hash of the token for database storage

    Raises:
        RuntimeError: If key loading or token creation fails
    """
    try:
        # Generate unique token identifier
        jti = str(uuid4())

        # Prepare token claims
        now_utc = datetime.now(timezone.utc)
        claims = {
            "sub": email,  # Subject (user email)
            "jti": jti,  # JWT ID for revocation
            "type": "api_key",  # Token type to distinguish from session tokens
            "iat": now_utc,  # Issued at
        }

        # Add expiration if specified
        if expires_delta:
            claims["exp"] = now_utc + expires_delta

        # Get private key for signing
        private_key = get_private_key()

        # Convert private key to PEM format for jose library
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Create JWT token
        token = jwt.encode(
            claims,
            private_key_pem,
            algorithm=ALGORITHMS.RS256,
            headers={"kid": "pak-key-1"},  # Key ID for rotation support
        )

        # Generate token hash for database storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        return token, jti, token_hash

    except ValueError as e:
        raise RuntimeError(f"Invalid JWT configuration: {e}") from e
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Key access error creating API JWT: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to create API JWT: {e}") from e


def verify_api_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a Personal API Key (PAK) JWT token.

    Args:
        token: The JWT token string to verify

    Returns:
        Decoded token payload if valid, None otherwise

    Notes:
        This function only verifies the token signature and structure.
        Additional checks (revocation, database lookup) must be done separately.
    """
    try:
        # Get public key for verification
        public_key = get_public_key()

        # Convert public key to PEM format for jose library
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Decode and verify token
        payload = jwt.decode(
            token,
            public_key_pem,
            algorithms=[ALGORITHMS.RS256],
            options={"verify_exp": True, "verify_iat": True},
        )

        # Verify this is an API key token
        if payload.get("type") != "api_key":
            return None

        # Verify required claims
        if not payload.get("sub") or not payload.get("jti"):
            return None

        return payload

    except JWTError:
        # Invalid token, expired, or verification failed
        return None
    except ValueError:
        # Invalid token format or claims
        return None
    except Exception:
        # Other errors (key loading, etc.)
        return None


def decode_api_jwt_unsafe(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a PAK JWT token without verification (for debugging/inspection).

    Args:
        token: The JWT token string to decode

    Returns:
        Decoded token payload if parseable, None otherwise

    Warning:
        This function does NOT verify the token signature.
        Only use for debugging or when verification is not needed.
    """
    try:
        # Decode without verification
        payload = jwt.decode(
            token,
            key="",  # Empty key since we're not verifying
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_iat": False,
            },
        )
        return payload
    except JWTError:
        return None


def compute_token_hash(token: str) -> str:
    """
    Compute SHA256 hash of a JWT token for database storage.

    Args:
        token: The JWT token string

    Returns:
        Hexadecimal SHA256 hash
    """
    return hashlib.sha256(token.encode()).hexdigest()


def extract_jti_from_token(token: str) -> Optional[str]:
    """
    Extract the JTI (JWT ID) from a token without verification.

    Args:
        token: The JWT token string

    Returns:
        JTI value if present, None otherwise
    """
    payload = decode_api_jwt_unsafe(token)
    if payload:
        return payload.get("jti")
    return None
