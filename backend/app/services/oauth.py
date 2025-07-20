"""OAuth service for handling external authentication providers."""

import time
from typing import Optional

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.logging import get_logger
from app.utils.error_handling import raise_bad_request_error, raise_unauthorized_error

logger = get_logger(__name__)


class GoogleUserInfo(BaseModel):
    """Google user information returned from token verification."""

    email: str
    email_verified: bool
    name: Optional[str] = None
    picture: Optional[str] = None


class OAuthService:
    """Service for handling OAuth operations with external providers."""

    def __init__(self, timeout: int = 10) -> None:
        """Initialize OAuth service with optional timeout configuration."""
        self.timeout = timeout

    async def verify_google_token(self, token: str, client_id: str) -> GoogleUserInfo:
        """
        Verify Google OAuth token and return user information.

        Args:
            token: The Google ID token to verify
            client_id: Expected OAuth client ID for audience validation

        Returns:
            GoogleUserInfo: Verified user information from Google

        Raises:
            HTTPException: If token verification fails
        """
        logger.info("Verifying Google OAuth token", extra={"client_id": client_id})

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/tokeninfo", data={"id_token": token}
                )
                response.raise_for_status()
                token_data = response.json()

                # Validate token audience
                if token_data.get("aud") != client_id:
                    logger.warning(
                        "Google token audience mismatch",
                        extra={
                            "expected_client_id": client_id,
                            "actual_audience": token_data.get("aud"),
                        },
                    )
                    raise_unauthorized_error("Invalid Google token audience")

                # Validate token expiration
                current_time = int(time.time())
                token_exp = int(token_data.get("exp", 0))
                if token_exp < current_time:
                    logger.warning(
                        "Google token expired",
                        extra={"token_exp": token_exp, "current_time": current_time},
                    )
                    raise_unauthorized_error("Google token has expired")

                # Extract and validate user information
                user_info = GoogleUserInfo(
                    email=token_data.get("email", ""),
                    email_verified=token_data.get("email_verified", False),
                    name=token_data.get("name"),
                    picture=token_data.get("picture"),
                )

                # Validate email is present and verified
                if not user_info.email or not user_info.email_verified:
                    logger.warning(
                        "Google token missing or unverified email",
                        extra={
                            "has_email": bool(user_info.email),
                            "email_verified": user_info.email_verified,
                        },
                    )
                    raise_bad_request_error("Invalid or unverified Google account")

                logger.info(
                    "Google token verified successfully",
                    extra={"email": user_info.email},
                )

                return user_info

        except HTTPException:
            # Re-raise HTTPExceptions without modification
            raise
        except httpx.RequestError as e:
            logger.error(
                "Network error verifying Google token",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify Google token: Network error",
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error verifying Google token",
                extra={"status_code": e.response.status_code, "error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to verify Google token: Service error",
            )
        except ValueError as e:
            logger.error(
                "Validation error verifying Google token",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token format",
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error verifying Google token",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token verification failed",
            ) from e


# Service instance for dependency injection
oauth_service = OAuthService()


def get_oauth_service() -> OAuthService:
    """Dependency injection function for OAuth service."""
    return oauth_service
