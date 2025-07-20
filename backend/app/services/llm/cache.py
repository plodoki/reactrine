"""LLM settings caching to avoid database hits on every request."""

import asyncio
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import LLMSettings
from app.repositories.llm_settings import LLMSettingsRepository

from .exceptions import LLMConfigurationError
from .protocol import LLMService

# Type variable for service instances


logger = logging.getLogger(__name__)

__all__ = [
    "LLMSettingsCache",
    "LLMServiceCache",
    "get_llm_settings_cache",
    "get_llm_service_cache",
]


class LLMSettingsCache:
    """
    Cache for LLM settings to avoid database hits on every request.

    Uses TTL (Time To Live) to ensure settings are refreshed periodically
    while avoiding the performance penalty of database queries on every request.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:  # 5 minutes default TTL
        """
        Initialize the LLM settings cache.

        Args:
            ttl_seconds: Time to live for cached settings in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cached_settings: Optional[LLMSettings] = None
        self._cached_at: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._llm_settings_repo = LLMSettingsRepository()

    async def get_settings(self, db: AsyncSession) -> LLMSettings:
        """
        Get LLM settings from cache or database.

        Args:
            db: Database session

        Returns:
            LLM settings

        Raises:
            LLMConfigurationError: If settings cannot be retrieved
        """
        async with self._lock:
            # Check if cache is still valid
            if self._is_cache_valid() and self._cached_settings is not None:
                logger.debug("Returning cached LLM settings")
                return self._cached_settings

            # Cache is invalid or empty, fetch from database
            logger.debug("Cache miss or expired, fetching LLM settings from database")
            settings = await self._fetch_from_database(db)

            # Update cache
            self._cached_settings = settings
            self._cached_at = datetime.now(timezone.utc)

            return settings

    def _is_cache_valid(self) -> bool:
        """Check if the cached settings are still valid."""
        if self._cached_settings is None or self._cached_at is None:
            return False

        expiry_time = self._cached_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) < expiry_time

    async def _fetch_from_database(self, db: AsyncSession) -> LLMSettings:
        """
        Fetch LLM settings from database, creating default if not exists.

        Args:
            db: Database session

        Returns:
            LLM settings

        Raises:
            LLMConfigurationError: If settings cannot be created or retrieved
        """
        try:
            settings_row = await self._llm_settings_repo.get_default_settings(db)
            if settings_row is None:
                # Create default settings if they don't exist
                settings_row = await self._create_default_settings(db)

            return settings_row
        except LLMConfigurationError:
            # Re-raise LLM configuration errors without modification
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching LLM settings: {e}")
            raise LLMConfigurationError("Database error retrieving LLM settings") from e
        except Exception as e:
            logger.error(f"Failed to fetch LLM settings from database: {e}")
            raise LLMConfigurationError(
                "Failed to retrieve LLM settings from database"
            ) from e

    async def _create_default_settings(self, db: AsyncSession) -> LLMSettings:
        """
        Create default LLM settings in database.

        Args:
            db: Database session

        Returns:
            Created LLM settings

        Raises:
            LLMConfigurationError: If settings cannot be created
        """
        try:
            app_settings = get_settings()
            settings_row = LLMSettings(
                provider=app_settings.LLM_PROVIDER,
                openai_model=app_settings.DEFAULT_LLM_MODEL or None,
                openrouter_model=app_settings.OPENROUTER_MODEL or None,
                bedrock_model=app_settings.BEDROCK_MODEL or None,
                lmstudio_model=app_settings.LMSTUDIO_MODEL or None,
            )

            settings_row = await self._llm_settings_repo.create_default_settings(
                db, settings_row
            )

            logger.info(
                f"Created default LLM settings with provider: {app_settings.LLM_PROVIDER}"
            )
            return settings_row

        except IntegrityError as e:
            # Handle race condition - another request might have created settings
            await db.rollback()
            fallback_settings = await self._llm_settings_repo.get_default_settings(db)
            if fallback_settings is not None:
                logger.info("LLM settings were created by another process")
                return fallback_settings

            logger.error(
                f"Failed to create default LLM settings due to integrity error: {e}"
            )
            raise LLMConfigurationError(
                "Failed to create or retrieve LLM settings"
            ) from e
        except LLMConfigurationError:
            # Re-raise LLM configuration errors without modification
            raise
        except SQLAlchemyError as e:
            # Handle other database errors
            await db.rollback()
            logger.error(f"Database error creating default LLM settings: {e}")
            raise LLMConfigurationError(
                "Database error creating or retrieving LLM settings"
            ) from e
        except Exception as e:
            # Handle other unexpected errors
            await db.rollback()
            logger.error(f"Failed to create default LLM settings: {e}")
            raise LLMConfigurationError(
                "Failed to create or retrieve LLM settings"
            ) from e

    async def invalidate_cache(self) -> None:
        """Invalidate the current cache, forcing a fresh fetch on next access."""
        async with self._lock:
            self._cached_settings = None
            self._cached_at = None
            logger.debug("LLM settings cache invalidated")


class LLMServiceCache:
    """
    Cache for LLMService instances to avoid heavy service creation on every request.

    Caches actual LLM service instances with TTL to prevent recreating expensive
    provider instances (OpenAI clients, Bedrock clients, etc.) on every request.
    """

    def __init__(self, ttl_seconds: int = 900) -> None:  # 15 minutes default TTL
        """
        Initialize the LLM service cache.

        Args:
            ttl_seconds: Time to live for cached services in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cached_services: dict[str, tuple[LLMService, datetime]] = {}
        self._lock = asyncio.Lock()

    async def get_service(
        self, cache_key: str, factory_func: Callable[[], LLMService]
    ) -> LLMService:
        """
        Get a cached service instance or create a new one.

        Args:
            cache_key: Unique key for the service configuration
            factory_func: Function to create the service if not cached

        Returns:
            Cached or newly created service instance
        """
        async with self._lock:
            # Check if we have a valid cached service
            if cache_key in self._cached_services:
                service, cached_at = self._cached_services[cache_key]
                if self._is_cache_valid(cached_at):
                    logger.debug(f"Returning cached LLM service for key: {cache_key}")
                    return service
                else:
                    # Cache expired, remove it
                    del self._cached_services[cache_key]
                    logger.debug(f"Expired cache entry removed for key: {cache_key}")

            # Create new service instance
            logger.debug(f"Creating new LLM service for key: {cache_key}")
            service = factory_func()

            # Cache the service
            self._cached_services[cache_key] = (service, datetime.now(timezone.utc))

            return service

    def _is_cache_valid(self, cached_at: datetime) -> bool:
        """Check if a cached service is still valid."""
        expiry_time = cached_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) < expiry_time

    async def invalidate_cache(self, cache_key: Optional[str] = None) -> None:
        """
        Invalidate cached services.

        Args:
            cache_key: Specific cache key to invalidate, or None to clear all
        """
        async with self._lock:
            if cache_key is None:
                # Clear all cached services
                self._cached_services.clear()
                logger.debug("All cached LLM services invalidated")
            elif cache_key in self._cached_services:
                # Clear specific cached service
                del self._cached_services[cache_key]
                logger.debug(f"Cached LLM service invalidated for key: {cache_key}")

    def _generate_cache_key(
        self,
        provider: str,
        model: str,
        **config_params: Any,  # noqa: ANN401
    ) -> str:
        """
        Generate a cache key for a service configuration.

        Args:
            provider: LLM provider name
            model: Model name
            **config_params: Additional configuration parameters

        Returns:
            Cache key string
        """
        # Create a stable cache key from provider, model, and config
        key_parts = [provider, model]

        # Add sorted config parameters for deterministic key generation
        for key, value in sorted(config_params.items()):
            key_parts.append(f"{key}={value}")

        return "|".join(key_parts)

    async def get_service_with_config(
        self,
        provider: str,
        model: str,
        config_params: dict[str, Any],
        factory_func: Callable[[], LLMService],
    ) -> LLMService:
        """
        Get a cached service with specific configuration parameters.

        Args:
            provider: LLM provider name
            model: Model name
            config_params: Configuration parameters for cache key generation
            factory_func: Function to create the service if not cached

        Returns:
            Cached or newly created service instance
        """
        # Remove provider and model from config_params to avoid conflicts
        filtered_config_params = {
            k: v for k, v in config_params.items() if k not in ("provider", "model")
        }
        cache_key = self._generate_cache_key(provider, model, **filtered_config_params)
        return await self.get_service(cache_key, factory_func)


# Global cache instances
_llm_settings_cache: Optional[LLMSettingsCache] = None
_llm_service_cache: Optional[LLMServiceCache] = None
_cache_lock = threading.Lock()


def get_llm_settings_cache() -> LLMSettingsCache:
    """
    Get the global LLM settings cache instance.

    Returns:
        LLM settings cache instance
    """
    global _llm_settings_cache
    if _llm_settings_cache is None:
        with _cache_lock:
            # Double-checked locking pattern
            if _llm_settings_cache is None:
                _llm_settings_cache = LLMSettingsCache()
    return _llm_settings_cache


def get_llm_service_cache() -> LLMServiceCache:
    """
    Get the global LLM service cache instance.

    Returns:
        LLM service cache instance
    """
    global _llm_service_cache
    if _llm_service_cache is None:
        with _cache_lock:
            # Double-checked locking pattern
            if _llm_service_cache is None:
                _llm_service_cache = LLMServiceCache()
    return _llm_service_cache
