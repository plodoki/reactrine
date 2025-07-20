"""User repository for encapsulating user database operations."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.logging import get_logger
from app.models.user import User

from .base import BaseRepository

logger = get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User entity database operations."""

    def __init__(self) -> None:
        """Initialize the UserRepository."""
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Get a user by email address.

        Args:
            db: Database session
            email: User email address

        Returns:
            User if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = select(User).where(User.email == email)
            result = await db.execute(statement)
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by email {email}: {e}")
            raise

    async def email_exists(self, db: AsyncSession, email: str) -> bool:
        """
        Check if a user with the given email exists.

        Args:
            db: Database session
            email: Email address to check

        Returns:
            True if user exists, False otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            user = await self.get_by_email(db, email)
            return user is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error checking if email exists {email}: {e}")
            raise

    async def get_by_id_with_role(
        self, db: AsyncSession, user_id: int
    ) -> Optional[User]:
        """
        Get a user by ID with role eagerly loaded.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User with role if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = (
                select(User).where(User.id == user_id).options(selectinload(User.role))  # type: ignore[arg-type]
            )
            result = await db.execute(statement)
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by ID with role {user_id}: {e}")
            raise

    async def get_by_email_with_role(
        self, db: AsyncSession, email: str
    ) -> Optional[User]:
        """
        Get a user by email with role eagerly loaded.

        Args:
            db: Database session
            email: User email address

        Returns:
            User with role if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = (
                select(User).where(User.email == email).options(selectinload(User.role))  # type: ignore[arg-type]
            )
            result = await db.execute(statement)
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by email with role {email}: {e}")
            raise

    async def update_user_role(
        self, db: AsyncSession, user_id: int, role_id: int
    ) -> Optional[User]:
        """
        Update a user's role.

        Args:
            db: Database session
            user_id: User ID
            role_id: New role ID

        Returns:
            Updated user with role if successful, None if user not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            user = await self.get_by_id(db, user_id)
            if not user:
                return None

            user.role_id = role_id
            user.updated_at = datetime.now(timezone.utc)

            return await self.update(db, user)
        except SQLAlchemyError as e:
            logger.error(f"Database error updating user role {user_id}: {e}")
            raise

    async def get_users_with_roles(
        self, db: AsyncSession, limit: int = 100, offset: int = 0
    ) -> List[User]:
        """
        Get users with their roles (paginated).

        Args:
            db: Database session
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of users with roles

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = (
                select(User)
                .options(selectinload(User.role))  # type: ignore[arg-type]
                .limit(limit)
                .offset(offset)
            )
            result = await db.execute(statement)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error getting users with roles: {e}")
            raise

    async def search_users_by_email(
        self, db: AsyncSession, email_pattern: str, limit: int = 100
    ) -> List[User]:
        """
        Search users by email pattern with roles loaded.

        Args:
            db: Database session
            email_pattern: Email pattern to search for
            limit: Maximum number of users to return

        Returns:
            List of users matching the email pattern

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = (
                select(User)
                .where(User.email.ilike(f"%{email_pattern}%"))  # type: ignore[attr-defined]
                .options(selectinload(User.role))  # type: ignore[arg-type]
                .limit(limit)
            )
            result = await db.execute(statement)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(
                f"Database error searching users by email {email_pattern}: {e}"
            )
            raise

    async def count_total_users(self, db: AsyncSession) -> int:
        """
        Get the total count of all users.

        Args:
            db: Database session

        Returns:
            Total number of users

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = select(func.count()).select_from(User)
            result = await db.execute(statement)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Database error counting total users: {e}")
            raise

    async def count_users_by_email(self, db: AsyncSession, email_pattern: str) -> int:
        """
        Get the count of users matching an email pattern.

        Args:
            db: Database session
            email_pattern: Email pattern to search for

        Returns:
            Number of users matching the email pattern

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = (
                select(func.count())
                .select_from(User)
                .where(
                    User.email.ilike(f"%{email_pattern}%")  # type: ignore[attr-defined]
                )
            )
            result = await db.execute(statement)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Database error counting users by email: {e}")
            raise

    async def soft_delete_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Soft delete a user (mark as inactive).

        Args:
            db: Database session
            user_id: User ID to soft delete

        Returns:
            Updated user if successful, None if user not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            user = await self.get_by_id(db, user_id)
            if not user:
                return None

            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)

            return await self.update(db, user)
        except SQLAlchemyError as e:
            logger.error(f"Database error soft deleting user {user_id}: {e}")
            raise

    async def activate_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Activate a user (mark as active).

        Args:
            db: Database session
            user_id: User ID to activate

        Returns:
            Updated user if successful, None if user not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            user = await self.get_by_id(db, user_id)
            if not user:
                return None

            user.is_active = True
            user.updated_at = datetime.now(timezone.utc)

            return await self.update(db, user)
        except SQLAlchemyError as e:
            logger.error(f"Database error activating user {user_id}: {e}")
            raise

    async def hard_delete_user(self, db: AsyncSession, user_id: int) -> bool:
        """
        Hard delete a user from the database.

        Args:
            db: Database session
            user_id: User ID to delete

        Returns:
            True if deletion successful, False if user not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            user = await self.get_by_id(db, user_id)
            if not user:
                return False

            await db.delete(user)
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error hard deleting user {user_id}: {e}")
            raise
