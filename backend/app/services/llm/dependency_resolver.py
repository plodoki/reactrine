"""Dependency resolution and database operations for LLM services."""

import logging
from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import LLMSettings

from .cache import get_llm_service_cache, get_llm_settings_cache
from .config import load_config
from .exceptions import LLMConfigurationError
from .factory import LLMServiceFactory
from .protocol import LLMService

logger = logging.getLogger(__name__)

__all__ = [
    "ensure_llm_settings",
    "get_llm_service",
    "get_llm_service_with_overrides",
    "LLMServiceDep",
    "LLMServiceResult",
]


async def ensure_llm_settings(db: AsyncSession) -> LLMSettings:
    """
    Helper function to get LLM settings with caching.

    Uses the LLM settings cache to avoid database hits on every request.
    The cache has a TTL (Time To Live) to ensure settings are refreshed periodically.

    Args:
        db: Database session

    Returns:
        LLMSettings row

    Raises:
        LLMConfigurationError: If settings cannot be retrieved
    """
    cache = get_llm_settings_cache()
    return await cache.get_settings(db)


def _validate_provider_and_model(provider: str, model: Optional[str]) -> str:
    """
    Validate provider and extract model, raising errors for invalid configurations.

    Args:
        provider: Provider name
        model: Model name (can be None)

    Returns:
        Validated model name

    Raises:
        LLMConfigurationError: If validation fails
    """
    supported_providers = {"openai", "openrouter", "bedrock", "lmstudio"}
    if provider not in supported_providers:
        raise LLMConfigurationError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: {supported_providers}"
        )

    if not model or model.strip() == "":
        raise LLMConfigurationError(f"{provider.title()} model is required but not set")

    return model


def _get_model_for_provider(settings_row: LLMSettings, provider: str) -> str:
    """
    Get the appropriate model for a given provider from settings.

    Args:
        settings_row: LLM settings from database
        provider: Provider name

    Returns:
        Model name for the provider

    Raises:
        LLMConfigurationError: If model is not configured for the provider
    """
    # Mapping from provider to its corresponding model attribute
    provider_model_mapping = {
        "openai": settings_row.openai_model,
        "openrouter": settings_row.openrouter_model,
        "bedrock": settings_row.bedrock_model,
        "lmstudio": settings_row.lmstudio_model,
    }

    model = provider_model_mapping.get(provider)
    if model is None:
        raise LLMConfigurationError(f"Unsupported provider: {provider}")

    return _validate_provider_and_model(provider, model)


async def _create_service_with_cache_async(provider: str, model: str) -> LLMService:
    """
    Create an LLM service instance with async caching.

    Args:
        provider: Provider name
        model: Model name

    Returns:
        LLM service instance

    Raises:
        LLMConfigurationError: If service creation fails
    """

    def factory_func() -> LLMService:
        config = load_config(provider=provider, default_model=model)
        return LLMServiceFactory.create_service(config)

    service_cache = get_llm_service_cache()
    return await service_cache.get_service_with_config(
        provider=provider,
        model=model,
        config_params={"provider": provider, "model": model},
        factory_func=factory_func,
    )


async def get_llm_service(
    db: AsyncSession = Depends(get_db_session),
) -> LLMService:
    """
    FastAPI dependency that returns the configured LLM service implementation.

    Uses service caching to avoid heavy service creation on every request.
    The cache has a TTL to ensure services are refreshed periodically.

    Returns:
        Configured LLM service instance

    Raises:
        HTTPException: If LLM service configuration fails
    """
    try:
        settings_row = await ensure_llm_settings(db)
        model = _get_model_for_provider(settings_row, settings_row.provider)
        return await _create_service_with_cache_async(settings_row.provider, model)
    except LLMConfigurationError as e:
        from app.api.utils import handle_llm_error

        handle_llm_error(e, "LLM service initialization")


class LLMServiceResult:
    """Result of LLM service creation with provider and model information.

    This class provides a structured way to return the LLM service instance
    along with the actual provider and model used, replacing the error-prone
    tuple return pattern.
    """

    def __init__(self, service: LLMService, provider: str, model: str) -> None:
        self.service = service
        self.provider = provider
        self.model = model


async def get_llm_service_with_overrides(
    provider: str | None = None,
    model: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> LLMServiceResult:
    """
    Get an LLM service with optional provider and model overrides.

    Uses service caching to avoid heavy service creation on every request.
    The cache has a TTL to ensure services are refreshed periodically.

    Args:
        provider: Optional provider to override default (e.g., 'openai', 'openrouter', 'bedrock')
        model: Optional model to override provider default
        db: Database session

    Returns:
        Configured LLM service instance with provider and model information

    Raises:
        HTTPException: If LLM service configuration fails
    """
    try:
        # Get default settings
        settings_row = await ensure_llm_settings(db)

        # Determine actual provider and model to use
        actual_provider = provider or settings_row.provider

        # Determine model based on provider and override
        if model:
            actual_model = model
        else:
            actual_model = _get_model_for_provider(settings_row, actual_provider)

        # Validate the final provider selection
        _validate_provider_and_model(actual_provider, actual_model)

        # Create LLM service with caching
        service = await _create_service_with_cache_async(actual_provider, actual_model)

        return LLMServiceResult(service, actual_provider, actual_model)

    except LLMConfigurationError as e:
        from app.api.utils import handle_llm_error

        handle_llm_error(e, "LLM service initialization with overrides")


# FastAPI dependency
LLMServiceDep = Depends(get_llm_service)
