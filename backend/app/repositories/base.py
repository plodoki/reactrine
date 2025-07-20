"""Base repository class providing common database operations."""

from abc import ABC
from typing import Generic, List, Optional, Type, TypeVar, cast

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

from app.core.logging import get_logger

logger = get_logger(__name__)

# Generic type for SQLModel entities
T = TypeVar("T", bound=SQLModel)


class BaseRepository(ABC, Generic[T]):
    """
    Base repository class providing common database operations.

    This class implements the Repository pattern to encapsulate database access logic
    and provide a consistent interface for data operations across different entities.
    """

    def __init__(self, model: Type[T]) -> None:
        """
        Initialize the repository with a specific model type.

        Args:
            model: The SQLModel class this repository manages
        """
        self.model = model

    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[T]:
        """
        Get an entity by its ID.

        Args:
            db: Database session
            id: Entity ID

        Returns:
            Entity if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return await db.get(self.model, id)
        except SQLAlchemyError as e:
            logger.error(
                f"Database error getting {self.model.__name__} by ID {id}: {e}"
            )
            raise

    async def get_all(self, db: AsyncSession) -> List[T]:
        """
        Get all entities of this type.

        Args:
            db: Database session

        Returns:
            List of all entities

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            statement = select(self.model)
            result = await db.execute(statement)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Database error getting all {self.model.__name__}: {e}")
            raise

    async def create(self, db: AsyncSession, entity: T) -> T:
        """
        Create a new entity.

        Args:
            db: Database session
            entity: Entity to create

        Returns:
            Created entity with updated fields (e.g., ID)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            db.add(entity)
            await db.commit()
            await db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error creating {self.model.__name__}: {e}")
            raise

    async def update(self, db: AsyncSession, entity: T) -> T:
        """
        Update an existing entity.

        Args:
            db: Database session
            entity: Entity to update

        Returns:
            Updated entity

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Merge the entity into the session to ensure changes are tracked
            merged_entity: T = cast(T, await db.merge(entity))
            await db.commit()
            await db.refresh(merged_entity)
            return merged_entity
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error updating {self.model.__name__}: {e}")
            raise

    async def delete(self, db: AsyncSession, entity: T) -> None:
        """
        Delete an entity.

        Args:
            db: Database session
            entity: Entity to delete

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # db.delete() is synchronous, not awaitable
            db.delete(entity)  # type: ignore[unused-coroutine]
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error deleting {self.model.__name__}: {e}")
            raise

    async def exists_by_id(self, db: AsyncSession, id: int) -> bool:
        """
        Check if an entity exists by ID.

        Args:
            db: Database session
            id: Entity ID

        Returns:
            True if entity exists, False otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            entity = await self.get_by_id(db, id)
            return entity is not None
        except SQLAlchemyError as e:
            logger.error(
                f"Database error checking existence of {self.model.__name__} by ID {id}: {e}"
            )
            raise
