"""
JWKS (JSON Web Key Set) endpoint for Personal API Keys.

This endpoint provides the public key information needed to verify
PAK (Personal API Key) tokens using the RS256 algorithm.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.utils.rsa_keys import get_jwks

router = APIRouter()

# Initialize logger
logger = get_logger(__name__)


@router.get("/.well-known/jwks.json", response_model=Dict[str, Any])
async def get_jwks_endpoint() -> Dict[str, Any]:
    """
    Get the JSON Web Key Set (JWKS) for PAK token verification.

    This endpoint provides the public key information needed to verify
    Personal API Key (PAK) tokens. The keys are in JWK format and include
    the necessary metadata for RS256 signature verification.

    Returns:
        JWKS dictionary containing public key information

    Raises:
        HTTPException: If the key cannot be loaded or converted
    """
    try:
        return get_jwks()
    except FileNotFoundError as e:
        logger.error(f"JWKS key file not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWKS key configuration is missing",
        )
    except ValueError as e:
        logger.error(f"Invalid JWKS key format: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWKS key format is invalid",
        )
    except OSError as e:
        logger.error(f"File system error loading JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to access JWKS key file",
        )
