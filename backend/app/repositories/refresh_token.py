"""Refresh Token repository for encapsulating refresh token database operations."""

from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.logging import get_logger
from app.models.refresh_token import RefreshToken

from .base import BaseRepository

logger = get_logger(__name__)


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for RefreshToken entity database operations."""

    def __init__(self) -> None:
        """Initialize the RefreshTokenRepository."""
        super().__init__(RefreshToken)

    async def get_by_token(
        self, db: AsyncSession, token: str
    ) -> Optional[RefreshToken]:
        """
        Get a refresh token by its token value.

        Args:
            db: Database session
            token: Token value to look up

        Returns:
            RefreshToken if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = (
                select(RefreshToken)
                .where(RefreshToken.token == token)
                .options(selectinload(RefreshToken.user))  # type: ignore[arg-type]
            )
            result = await db.execute(statement)
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting refresh token by token: {e}")
            raise

    async def get_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> Optional[RefreshToken]:
        """
        Get a refresh token by user ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            RefreshToken if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = select(RefreshToken).where(RefreshToken.user_id == user_id)
            result = await db.execute(statement)
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting refresh token by user ID {user_id}: {e}"
            )
            raise

    async def delete_by_user_id(self, db: AsyncSession, user_id: int) -> None:
        """
        Delete refresh token by user ID.

        Args:
            db: Database session
            user_id: User ID

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            refresh_token = await self.get_by_user_id(db, user_id)
            if refresh_token:
                await self.delete(db, refresh_token)
        except SQLAlchemyError as e:
            logger.error(
                f"Database error deleting refresh token for user {user_id}: {e}"
            )
            raise

    async def delete_by_token(self, db: AsyncSession, token: str) -> None:
        """
        Delete refresh token by token value.

        Args:
            db: Database session
            token: Token value

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            refresh_token = await self.get_by_token(db, token)
            if refresh_token:
                await self.delete(db, refresh_token)
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting refresh token by token: {e}")
            raise
