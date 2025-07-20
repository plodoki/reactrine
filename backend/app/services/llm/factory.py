"""Service factory for LLM services."""

import logging
from typing import Any, Callable, Type

from .config import LLMConfig
from .exceptions import LLMConfigurationError
from .protocol import LLMService
from .providers.base import BaseLLMProvider
from .registry import get_provider_registry

logger = logging.getLogger(__name__)

__all__ = [
    "LLMServiceFactory",
]


class LLMServiceFactory:
    """Factory for creating LLM service instances."""

    @classmethod
    def create_service(cls, config: LLMConfig) -> LLMService:
        """
        Create an LLM service instance based on configuration.

        Args:
            config: LLM configuration

        Returns:
            Configured LLM service instance

        Raises:
            LLMConfigurationError: If provider is not supported or configuration is invalid
        """
        provider_name = config.provider.lower()
        registry = get_provider_registry()

        try:
            return registry.create_provider(provider_name, config)
        except LLMConfigurationError:
            # Re-raise LLM configuration errors without modification
            raise
        except KeyError as e:
            logger.error(f"Unknown provider {provider_name}: {e}")
            raise LLMConfigurationError(
                f"Provider '{provider_name}' is not supported"
            ) from e
        except ValueError as e:
            logger.error(f"Invalid configuration for provider {provider_name}: {e}")
            raise LLMConfigurationError(
                f"Invalid configuration for {provider_name} provider: {e}"
            ) from e
        except TypeError as e:
            logger.error(
                f"Invalid configuration type for provider {provider_name}: {e}"
            )
            raise LLMConfigurationError(
                f"Invalid configuration type for {provider_name} provider: {e}"
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error creating LLM service for provider {provider_name}: {e}"
            )
            raise LLMConfigurationError(
                f"Failed to initialize {provider_name} provider: {e}"
            ) from e

    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: Type[BaseLLMProvider],
        config_getter: Callable[[LLMConfig], Any] | None = None,
    ) -> None:
        """
        Register a new LLM provider (delegates to registry).

        Args:
            name: Provider name
            provider_class: Provider implementation class
            config_getter: Function to extract provider config from LLMConfig
        """
        registry = get_provider_registry()
        registry.register_provider(name, provider_class, config_getter)
