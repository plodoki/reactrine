"""API Key repository for encapsulating API key database operations."""

from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.logging import get_logger
from app.models.api_key import ApiKey

from .base import BaseRepository

logger = get_logger(__name__)


class ApiKeyRepository(BaseRepository[ApiKey]):
    """Repository for ApiKey entity database operations."""

    def __init__(self) -> None:
        """Initialize the ApiKeyRepository."""
        super().__init__(ApiKey)

    async def get_by_user_id(self, db: AsyncSession, user_id: int) -> List[ApiKey]:
        """
        Get all API keys for a specific user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of API keys for the user

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = select(ApiKey).where(ApiKey.user_id == user_id)
            result = await db.execute(statement)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error getting API keys for user {user_id}: {e}")
            raise

    async def get_active_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> List[ApiKey]:
        """
        Get all active API keys for a specific user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of active API keys for the user

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Get all keys for user and filter active ones in Python
            # since is_active is a property, not a database column
            all_keys = await self.get_by_user_id(db, user_id)
            return [key for key in all_keys if key.is_active]
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting active API keys for user {user_id}: {e}"
            )
            raise

    async def get_by_jti(self, db: AsyncSession, jti: str) -> Optional[ApiKey]:
        """
        Get an API key by its JWT ID (jti).

        Args:
            db: Database session
            jti: JWT ID to look up

        Returns:
            ApiKey if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = select(ApiKey).where(ApiKey.jti == jti)
            result = await db.execute(statement)
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting API key by JTI {jti}: {e}")
            raise

    async def count_active_by_user_id(self, db: AsyncSession, user_id: int) -> int:
        """
        Count active API keys for a specific user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Number of active API keys for the user

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            active_keys = await self.get_active_by_user_id(db, user_id)
            return len(active_keys)
        except SQLAlchemyError as e:
            logger.error(
                f"Database error counting active API keys for user {user_id}: {e}"
            )
            raise

    async def get_by_user_id_and_key_id(
        self, db: AsyncSession, user_id: int, key_id: int
    ) -> Optional[ApiKey]:
        """
        Get an API key by user ID and key ID (for ownership verification).

        Args:
            db: Database session
            user_id: User ID
            key_id: API key ID

        Returns:
            ApiKey if found and owned by user, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = select(ApiKey).where(
                ApiKey.id == key_id, ApiKey.user_id == user_id
            )
            result = await db.execute(statement)
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting API key {key_id} for user {user_id}: {e}"
            )
            raise
