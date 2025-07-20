"""
Simplified API Key service for testing.

This is a minimal implementation to get PAK working quickly.
Can be enhanced later with proper SQLAlchemy syntax.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.api_key import ApiKey
from app.models.user import User
from app.repositories.api_key import ApiKeyRepository
from app.schemas.api_key import ApiKeyInfo, ApiKeyList
from app.utils.error_handling import (
    raise_bad_request_error,
    raise_internal_server_error,
    raise_not_found_error,
    with_database_error_handling,
)
from app.utils.jwt_pak import create_api_key_token

# Initialize logger
logger = get_logger(__name__)


class ApiKeyService:
    """Service for managing Personal API Keys with business logic encapsulation."""

    MAX_ACTIVE_KEYS_PER_USER = 20

    def __init__(self) -> None:
        """Initialize the ApiKeyService with repository."""
        self.api_key_repo = ApiKeyRepository()

    @with_database_error_handling(
        operation="retrieving user API keys",
        custom_message="Failed to retrieve API keys",
        rollback=False,
    )
    async def list_user_keys(self, db: AsyncSession, user_id: int) -> ApiKeyList:
        """
        List all API keys for a user, sorted by creation date.

        Args:
            db: Database session
            user_id: ID of the user

        Returns:
            ApiKeyList with user's keys sorted by creation date (newest first)

        Raises:
            HTTPException: If database error occurs
        """
        user_keys = await self.api_key_repo.get_by_user_id(db, user_id)

        # Sort by created_at descending (newest first)
        sorted_keys = sorted(user_keys, key=lambda k: k.created_at, reverse=True)

        return ApiKeyList(
            keys=[ApiKeyInfo.model_validate(key) for key in sorted_keys],
            total=len(sorted_keys),
        )

    @with_database_error_handling(
        operation="validating user API key limit",
        custom_message="Failed to validate API key limit",
        rollback=False,
    )
    async def validate_user_key_limit(self, db: AsyncSession, user_id: int) -> None:
        """
        Validate that user hasn't exceeded the maximum number of active API keys.

        Args:
            db: Database session
            user_id: ID of the user

        Raises:
            HTTPException: If user has reached the maximum number of active keys
        """
        active_count = await self.api_key_repo.count_active_by_user_id(db, user_id)

        if active_count >= self.MAX_ACTIVE_KEYS_PER_USER:
            raise_bad_request_error(
                f"Maximum number of active API keys ({self.MAX_ACTIVE_KEYS_PER_USER}) reached. Please revoke some keys first."
            )

    async def create_api_key(
        self,
        db: AsyncSession,
        user: User,
        label: Optional[str] = None,
        expires_in_days: Optional[int] = 30,
    ) -> tuple[ApiKey, str]:
        """
        Create a new Personal API Key for a user after validating limits.

        Args:
            db: Database session
            user: User to create the key for
            label: Optional user-provided label for the key
            expires_in_days: Days until expiration (None for no expiry)

        Returns:
            Tuple of (ApiKey model, JWT token string)

        Raises:
            HTTPException: If validation fails or database error occurs
        """
        if user.id is None:
            raise_bad_request_error("User must have a valid ID")

        # Validate user hasn't exceeded key limit
        await self.validate_user_key_limit(db, user.id)

        # Delegate to the simple creation function
        return await create_api_key_simple(db, user, label, expires_in_days)

    @with_database_error_handling(
        operation="verifying API key ownership",
        custom_message="Failed to verify API key ownership",
        rollback=False,
    )
    async def verify_key_ownership(
        self, db: AsyncSession, key_id: int, user_id: int
    ) -> ApiKey:
        """
        Verify that a user owns a specific API key and return it.

        Args:
            db: Database session
            key_id: ID of the API key
            user_id: ID of the user

        Returns:
            ApiKey if found and owned by user

        Raises:
            HTTPException: If key not found, not owned by user, or already revoked
        """
        api_key = await self.api_key_repo.get_by_user_id_and_key_id(db, user_id, key_id)

        if api_key is None:
            raise_not_found_error(
                "API key", "API key not found or you don't have permission to access it"
            )

        # At this point, api_key is guaranteed to be not None
        return api_key

    async def revoke_user_key(
        self, db: AsyncSession, key_id: int, user_id: int
    ) -> bool:
        """
        Revoke an API key after verifying ownership.

        Args:
            db: Database session
            key_id: ID of the API key to revoke
            user_id: ID of the user

        Returns:
            True if successfully revoked

        Raises:
            HTTPException: If key not found, not owned by user, or already revoked
        """
        # Verify ownership first
        api_key = await self.verify_key_ownership(db, key_id, user_id)

        # Check if already revoked
        if api_key.revoked_at is not None:
            raise_bad_request_error("API key is already revoked")

        # Revoke the key
        success = await revoke_api_key_simple(db, key_id)

        if not success:
            raise_internal_server_error("Failed to revoke API key")

        return success


# Dependency injection function
api_key_service = ApiKeyService()


def get_api_key_service() -> ApiKeyService:
    """Get ApiKeyService instance for dependency injection."""
    return api_key_service


async def create_api_key_simple(
    db: AsyncSession,
    user: User,
    label: Optional[str] = None,
    expires_in_days: Optional[int] = 30,
) -> tuple[ApiKey, str]:
    """
    Create a new Personal API Key for a user.

    Args:
        db: Database session
        user: User to create the key for
        label: Optional user-provided label for the key
        expires_in_days: Days until expiration (None for no expiry)

    Returns:
        Tuple of (ApiKey model, JWT token string)
    """
    if user.id is None:
        raise ValueError("User must have a valid ID")

    # Calculate expiration date
    expires_at = None
    expires_delta = None
    if expires_in_days is not None:
        if expires_in_days <= 0:
            raise ValueError("expires_in_days must be positive")
        expires_delta = timedelta(days=expires_in_days)
        expires_at = datetime.now(timezone.utc) + expires_delta

    # Generate unique JWT ID
    jti = str(uuid4())

    # Create JWT token using the internal function
    token = create_api_key_token(
        subject=user.email,
        jti=jti,
        scopes=["*"],  # Default to full access
        expires_delta=expires_delta,
    )

    # Generate token hash for database storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Create database record
    api_key = ApiKey(
        user_id=user.id,
        jti=jti,
        token_hash=token_hash,
        label=label,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )

    # Set scopes using the property setter
    api_key.scopes = ["*"]  # Default to full access

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return api_key, token


async def get_api_key_by_id(db: AsyncSession, key_id: int) -> Optional[ApiKey]:
    """Get API key by ID."""
    api_key_repo = ApiKeyRepository()
    return await api_key_repo.get_by_id(db, key_id)


async def revoke_api_key_simple(db: AsyncSession, key_id: int) -> bool:
    """Revoke an API key by ID."""
    api_key = await get_api_key_by_id(db, key_id)
    if api_key and api_key.revoked_at is None:
        api_key.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        return True
    return False


async def get_api_key_by_jti(db: AsyncSession, jti: str) -> Optional[ApiKey]:
    """
    Get an API key by its JWT ID (jti).

    Args:
        db: Database session
        jti: JWT ID to look up

    Returns:
        ApiKey if found, None otherwise
    """
    try:
        api_key_repo = ApiKeyRepository()
        return await api_key_repo.get_by_jti(db, jti)
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving API key by JTI {jti}: {e}")
        return None


async def verify_api_key_by_hash(
    db: AsyncSession, token_hash: str, jti: str
) -> Optional[ApiKey]:
    """
    Verify an API key by its hash and JTI using constant-time comparison.

    Args:
        db: Database session
        token_hash: SHA256 hash of the JWT token
        jti: JWT ID for additional verification

    Returns:
        ApiKey if valid and active, None otherwise
    """
    import secrets

    try:
        # Look up key by JTI first
        api_key = await get_api_key_by_jti(db, jti)

        if api_key is None:
            return None

        # Check if key is active (not revoked and not expired)
        if not api_key.is_active:
            return None

        # Verify hash using constant-time comparison
        if not secrets.compare_digest(api_key.token_hash, token_hash):
            return None

        return api_key

    except SQLAlchemyError as e:
        logger.error(f"Database error verifying API key with JTI {jti}: {e}")
        return None


async def update_api_key_last_used(
    db: AsyncSession, api_key: ApiKey, throttle_minutes: int = 10
) -> None:
    """
    Update the last_used_at timestamp for an API key with throttling.

    Args:
        db: Database session
        api_key: API key to update
        throttle_minutes: Minimum minutes between updates
    """
    try:
        now = datetime.now(timezone.utc)

        # Check if we need to update (throttling)
        if api_key.last_used_at is None or now - api_key.last_used_at > timedelta(
            minutes=throttle_minutes
        ):
            api_key.last_used_at = now
            await db.commit()

    except (SQLAlchemyError, Exception) as e:
        # Don't fail authentication if last_used update fails
        logger.warning(f"Failed to update last_used_at for API key: {e}")
        await db.rollback()
