"""Role repository for encapsulating role database operations."""

from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.logging import get_logger
from app.models.role import Role

from .base import BaseRepository

logger = get_logger(__name__)


class RoleRepository(BaseRepository[Role]):
    """Repository for Role entity database operations."""

    def __init__(self) -> None:
        """Initialize the RoleRepository."""
        super().__init__(Role)

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        """
        Get a role by name.

        Args:
            db: Database session
            name: Role name (case-insensitive)

        Returns:
            Role if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = select(Role).where(Role.name.ilike(name))  # type: ignore[attr-defined]
            result = await db.execute(statement)
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting role by name {name}: {e}")
            raise

    async def get_all_active(self, db: AsyncSession) -> List[Role]:
        """
        Get all active roles.

        Args:
            db: Database session

        Returns:
            List of all roles (currently all roles are active)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return await self.get_all(db)
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all active roles: {e}")
            raise

    async def name_exists(self, db: AsyncSession, name: str) -> bool:
        """
        Check if a role with the given name exists.

        Args:
            db: Database session
            name: Role name to check

        Returns:
            True if role exists, False otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            role = await self.get_by_name(db, name)
            return role is not None
        except SQLAlchemyError as e:
            logger.error(f"Database error checking if role name exists {name}: {e}")
            raise
