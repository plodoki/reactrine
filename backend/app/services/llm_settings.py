"""Service for managing LLM settings with comprehensive business logic."""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.llm_settings import LLMSettings
from app.repositories.llm_settings import LLMSettingsRepository
from app.schemas.llm_settings import (
    LLMSettingsCreateSchema,
    LLMSettingsSchema,
    LLMSettingsUpdateSchema,
)
from app.services.llm.cache import get_llm_settings_cache
from app.services.llm.config import LMStudioConfig
from app.services.llm.providers.lmstudio import LMStudioLLMProvider

logger = get_logger(__name__)


class LLMSettingsService:
    """Service for handling LLM settings operations with business logic."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        """Initialize LLM settings service with optional settings override."""
        self.settings = settings or get_settings()
        self.llm_settings_repo = LLMSettingsRepository()
        self._provider_model_mapping = {
            "openai": ("openai_model", self.settings.DEFAULT_LLM_MODEL),
            "openrouter": ("openrouter_model", self.settings.OPENROUTER_MODEL),
            "bedrock": ("bedrock_model", self.settings.BEDROCK_MODEL),
            "lmstudio": ("lmstudio_model", self.settings.LMSTUDIO_MODEL),
        }

    async def get_settings(self, db: AsyncSession) -> LLMSettingsSchema:
        """
        Get current LLM settings.

        Args:
            db: Database session

        Returns:
            LLMSettingsSchema: Current LLM settings

        Raises:
            HTTPException: If settings not found or database error
        """
        logger.info("Retrieving LLM settings")

        try:
            settings = await self.llm_settings_repo.get_default_settings(db)
            if not settings:
                logger.warning("LLM settings not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="LLM settings not found",
                )

            logger.info(
                "LLM settings retrieved successfully",
                extra={"provider": settings.provider},
            )
            return LLMSettingsSchema.model_validate(settings)

        except SQLAlchemyError as e:
            logger.error(
                "Database error retrieving LLM settings",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve LLM settings",
            ) from e

    async def create_llm_settings(
        self, payload: LLMSettingsCreateSchema, db: AsyncSession
    ) -> LLMSettingsSchema:
        """
        Create new LLM settings.

        Args:
            payload: Settings creation data
            db: Database session

        Returns:
            LLMSettingsSchema: Created LLM settings

        Raises:
            HTTPException: If settings already exist or database error
        """
        logger.info("Creating LLM settings", extra={"provider": payload.provider})

        try:
            settings = LLMSettings(
                provider=payload.provider,
                openai_model=payload.openai_model,
                openrouter_model=payload.openrouter_model,
                bedrock_model=payload.bedrock_model,
                lmstudio_model=payload.lmstudio_model,
            )

            settings = await self.llm_settings_repo.create_default_settings(
                db, settings
            )

            # Invalidate cache after successful creation
            cache = get_llm_settings_cache()
            await cache.invalidate_cache()

            logger.info(
                "LLM settings created successfully",
                extra={"provider": settings.provider, "id": settings.id},
            )

            return LLMSettingsSchema.model_validate(settings)

        except IntegrityError as e:
            # Handle race condition - settings already exist
            await db.rollback()
            logger.warning(
                "LLM settings already exist (race condition detected)",
                extra={"error": str(e)},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="LLM settings already exist. Use PATCH to update.",
            ) from e
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(
                "Database error creating LLM settings",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create LLM settings",
            ) from e

    async def update_llm_settings(
        self, payload: LLMSettingsUpdateSchema, db: AsyncSession
    ) -> LLMSettingsSchema:
        """
        Update existing LLM settings with business logic.

        Args:
            payload: Settings update data
            db: Database session

        Returns:
            LLMSettingsSchema: Updated LLM settings

        Raises:
            HTTPException: If settings not found, validation fails, or database error
        """
        logger.info(
            "Updating LLM settings",
            extra={
                "update_fields": list(payload.model_dump(exclude_unset=True).keys())
            },
        )

        try:
            settings = await self.llm_settings_repo.get_default_settings(db)
            if not settings:
                logger.warning("Attempted to update non-existent LLM settings")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="LLM settings not found. Use POST to create new settings.",
                )

            # Get update data excluding unset fields
            update_data = payload.model_dump(exclude_unset=True)

            # Apply auto-population logic for provider changes
            if "provider" in update_data:
                update_data = self._apply_provider_auto_population(
                    update_data, settings
                )

            # Validate provider/model combination for updates
            self._validate_provider_model_combination(update_data, settings)

            # Apply updates to settings
            for field, value in update_data.items():
                setattr(settings, field, value)

            settings = await self.llm_settings_repo.update_default_settings(
                db, settings
            )

            # Invalidate cache after successful update
            cache = get_llm_settings_cache()
            await cache.invalidate_cache()

            logger.info(
                "LLM settings updated successfully",
                extra={
                    "provider": settings.provider,
                    "updated_fields": list(update_data.keys()),
                },
            )

            return LLMSettingsSchema.model_validate(settings)

        except HTTPException:
            # Re-raise HTTPExceptions without modification
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(
                "Database error updating LLM settings",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update LLM settings",
            ) from e

    def _apply_provider_auto_population(
        self, update_data: Dict[str, Any], current_settings: LLMSettings
    ) -> Dict[str, Any]:
        """
        Apply auto-population logic when switching providers.

        If switching to a provider that has no configured model, auto-populate
        with the default model from settings if available.

        Args:
            update_data: Update data dictionary
            current_settings: Current LLM settings

        Returns:
            Dict[str, Any]: Updated data with auto-population applied
        """
        new_provider = update_data["provider"]
        logger.debug(
            "Applying auto-population for provider change",
            extra={"new_provider": new_provider},
        )

        if new_provider in self._provider_model_mapping:
            model_key, default_model = self._provider_model_mapping[new_provider]

            # Only auto-populate if no model provided in update AND there's no valid existing model
            if model_key not in update_data:
                current_model = getattr(current_settings, model_key)
                if not current_model or current_model.strip() == "":
                    # Auto-populate with default model if available
                    if default_model and default_model.strip():
                        update_data[model_key] = default_model
                        logger.info(
                            "Auto-populated model for provider change",
                            extra={
                                "provider": new_provider,
                                "model_key": model_key,
                                "default_model": default_model,
                            },
                        )
                    else:
                        logger.debug(
                            "No default model available for auto-population",
                            extra={"provider": new_provider, "model_key": model_key},
                        )
                else:
                    logger.debug(
                        "Existing valid model retained for provider",
                        extra={"provider": new_provider, "model": current_model},
                    )

        return update_data

    def _validate_provider_model_combination(
        self, update_data: Dict[str, Any], current_settings: LLMSettings
    ) -> None:
        """
        Validate that provider has corresponding model when updating.

        Args:
            update_data: Update data dictionary
            current_settings: Current LLM settings

        Raises:
            HTTPException: If provider/model validation fails
        """
        if "provider" not in update_data:
            return

        new_provider = update_data["provider"]
        model_key = f"{new_provider}_model"

        # Get the model value from the update or existing settings
        model_value = update_data.get(model_key) or getattr(current_settings, model_key)

        if not model_value or model_value.strip() == "":
            provider_names = {
                "openai": "OpenAI",
                "openrouter": "OpenRouter",
                "bedrock": "Bedrock",
                "lmstudio": "LMStudio",
            }
            provider_name = provider_names.get(new_provider, new_provider.title())

            logger.warning(
                "Provider model validation failed",
                extra={
                    "provider": new_provider,
                    "model_key": model_key,
                    "model_value": model_value,
                },
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{provider_name} model must be provided when updating to {provider_name} provider",
            )

    async def get_lmstudio_models(self) -> list[str]:
        """
        Get available models from LMStudio server.

        Returns:
            list[str]: List of available LMStudio models

        Raises:
            HTTPException: If unable to fetch models from LMStudio server
        """
        logger.info("Fetching available LMStudio models")

        try:
            lmstudio_config = LMStudioConfig(
                base_url=self.settings.LMSTUDIO_BASE_URL,
                default_model=self.settings.LMSTUDIO_MODEL,
            )

            provider = LMStudioLLMProvider(lmstudio_config)
            models = await provider.get_available_models()

            if not models:
                logger.warning("No models returned from LMStudio server")
                return []

            logger.info(
                "Successfully fetched LMStudio models",
                extra={"model_count": len(models)},
            )

            return models

        except HTTPException:
            # Re-raise HTTPExceptions without modification
            raise
        except ConnectionError as e:
            logger.error(
                "Connection error fetching LMStudio models",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to connect to LMStudio server",
            ) from e
        except TimeoutError as e:
            logger.error(
                "Timeout error fetching LMStudio models",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LMStudio server response timeout",
            ) from e
        except ValueError as e:
            logger.error(
                "Validation error fetching LMStudio models",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid LMStudio server configuration",
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error fetching LMStudio models",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch models from LMStudio server",
            ) from e


# Service instance for dependency injection
llm_settings_service = LLMSettingsService()


def get_llm_settings_service() -> LLMSettingsService:
    """Dependency injection function for LLM settings service."""
    return llm_settings_service
