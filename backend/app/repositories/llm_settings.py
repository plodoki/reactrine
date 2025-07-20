"""LLM Settings repository for encapsulating LLM settings database operations."""

from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.llm_settings import LLMSettings

from .base import BaseRepository

logger = get_logger(__name__)


class LLMSettingsRepository(BaseRepository[LLMSettings]):
    """Repository for LLMSettings entity database operations."""

    def __init__(self) -> None:
        """Initialize the LLMSettingsRepository."""
        super().__init__(LLMSettings)

    async def get_default_settings(self, db: AsyncSession) -> Optional[LLMSettings]:
        """
        Get the default LLM settings (ID = 1).

        Args:
            db: Database session

        Returns:
            LLMSettings if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return await self.get_by_id(db, 1)
        except SQLAlchemyError as e:
            logger.error(f"Database error getting default LLM settings: {e}")
            raise

    async def create_default_settings(
        self, db: AsyncSession, settings: LLMSettings
    ) -> LLMSettings:
        """
        Create the default LLM settings with ID = 1.

        Args:
            db: Database session
            settings: LLM settings to create

        Returns:
            Created LLM settings

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Create a new settings object with ID = 1 to avoid modifying the input
            default_settings = LLMSettings(
                id=1,
                provider=settings.provider,
                openai_model=settings.openai_model,
                openrouter_model=settings.openrouter_model,
                bedrock_model=settings.bedrock_model,
                lmstudio_model=settings.lmstudio_model,
            )
            return await self.create(db, default_settings)
        except SQLAlchemyError as e:
            logger.error(f"Database error creating default LLM settings: {e}")
            raise

    async def update_default_settings(
        self, db: AsyncSession, settings: LLMSettings
    ) -> LLMSettings:
        """
        Update the default LLM settings.

        Args:
            db: Database session
            settings: Updated LLM settings

        Returns:
            Updated LLM settings

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            return await self.update(db, settings)
        except SQLAlchemyError as e:
            logger.error(f"Database error updating default LLM settings: {e}")
            raise
