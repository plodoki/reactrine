"""
Enhanced authentication functions with Personal API Key (PAK) support.

This module extends the existing authentication system to support both:
1. Session tokens (HS256 signed with SECRET_KEY) - for cookie-based auth
2. Personal API Keys (RS256 signed with RSA keys) - for header-based auth
"""

from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.security.auth import decode_access_token as decode_session_token
from app.services.api_key import update_api_key_last_used, verify_api_key_by_hash
from app.utils.jwt_pak import compute_token_hash, verify_api_jwt


async def decode_access_token_enhanced(
    token: str, db: Optional[AsyncSession] = None
) -> Tuple[Optional[str], bool]:
    """
    Enhanced token decoder that handles both session tokens and PAK tokens.

    Security: Checks JWT header algorithm first to prevent algorithm confusion attacks.

    Args:
        token: JWT token to decode
        db: Database session (required for PAK verification)

    Returns:
        Tuple of (email, is_pak_token)
        - email: User email if token is valid, None otherwise
        - is_pak_token: True if this was a PAK token, False if session token
    """
    from jose import jwt
    from jose.exceptions import JWTError

    try:
        # First, inspect the JWT header to determine the algorithm
        # This prevents algorithm confusion attacks
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")

        if algorithm is None:
            return None, False

        # Route to appropriate verification based on algorithm in header
        if algorithm == "HS256":
            # Session token verification
            email = decode_session_token(token)
            if email is not None:
                return email, False  # Valid session token
            else:
                return None, False  # Invalid session token

        elif algorithm == "RS256":
            # PAK token verification
            if db is None:
                # Cannot verify PAK without database access
                return None, False

            try:
                # Verify JWT signature and structure
                payload = verify_api_jwt(token)
                if payload is None:
                    return None, False

                # Extract required claims
                email = payload.get("sub")
                jti = payload.get("jti")

                if not email or not jti:
                    return None, False

                # Compute token hash for database lookup
                token_hash = compute_token_hash(token)

                # Verify token is in database and not revoked
                api_key = await verify_api_key_by_hash(db, token_hash, jti)
                if api_key is None:
                    return None, False

                # Update last used timestamp (async, non-blocking)
                await update_api_key_last_used(db, api_key)

                return email, True  # Valid PAK token

            except Exception:
                # Any error in PAK verification
                return None, False
        else:
            # Reject tokens with unexpected algorithms
            return None, False

    except JWTError:
        # Token is malformed or header cannot be parsed
        return None, False
    except Exception:
        # Any other error
        return None, False


async def is_pak_token(token: str) -> bool:
    """
    Quick check to determine if a token is a PAK token without full verification.

    Args:
        token: JWT token to check

    Returns:
        True if token appears to be a PAK token
    """
    try:
        payload = verify_api_jwt(token)
        return payload is not None and payload.get("type") == "api_key"
    except Exception:
        return False
