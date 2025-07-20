"""LLM provider registry and management."""

import logging
from typing import Any, Callable, Type

from .config import LLMConfig
from .exceptions import LLMConfigurationError
from .protocol import LLMService
from .providers import (
    BedrockLLMProvider,
    LMStudioLLMProvider,
    OpenAILLMProvider,
    OpenRouterLLMProvider,
)
from .providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

__all__ = [
    "LLMProviderRegistry",
    "get_provider_registry",
]


class LLMProviderRegistry:
    """Registry for managing LLM provider implementations."""

    def __init__(self) -> None:
        # Registry of provider name to provider class
        self._providers: dict[str, Type[BaseLLMProvider]] = {}

        # Mapping of provider names to their configuration attribute getter
        self._provider_configs: dict[str, Callable[[LLMConfig], Any]] = {}

        # Register default providers
        self._register_default_providers()

    def _register_default_providers(self) -> None:
        """Register the default built-in LLM providers."""
        self.register_provider(
            "openai", OpenAILLMProvider, lambda config: config.openai
        )
        self.register_provider(
            "openrouter", OpenRouterLLMProvider, lambda config: config.openrouter
        )
        self.register_provider(
            "bedrock", BedrockLLMProvider, lambda config: config.bedrock
        )
        self.register_provider(
            "lmstudio", LMStudioLLMProvider, lambda config: config.lmstudio
        )

    def register_provider(
        self,
        name: str,
        provider_class: Type[BaseLLMProvider],
        config_getter: Callable[[LLMConfig], Any] | None = None,
    ) -> None:
        """
        Register a new LLM provider.

        Args:
            name: Provider name (e.g., 'openai', 'bedrock')
            provider_class: Provider implementation class
            config_getter: Function to extract provider config from LLMConfig
        """
        self._providers[name] = provider_class
        if config_getter:
            self._provider_configs[name] = config_getter
        logger.info(f"Registered LLM provider: {name}")

    def get_provider_class(self, name: str) -> Type[BaseLLMProvider]:
        """
        Get a provider class by name.

        Args:
            name: Provider name

        Returns:
            Provider class

        Raises:
            LLMConfigurationError: If provider is not registered
        """
        if name not in self._providers:
            available = list(self._providers.keys())
            raise LLMConfigurationError(
                f"Unsupported LLM provider: {name}. Available: {available}"
            )
        return self._providers[name]

    def get_config_getter(self, name: str) -> Callable[[LLMConfig], Any]:
        """
        Get the configuration getter for a provider.

        Args:
            name: Provider name

        Returns:
            Configuration getter function

        Raises:
            LLMConfigurationError: If no config getter is registered for the provider
        """
        config_getter = self._provider_configs.get(name)
        if not config_getter:
            raise LLMConfigurationError(
                f"No configuration handler for provider: {name}"
            )
        return config_getter

    def create_provider(self, name: str, config: LLMConfig) -> LLMService:
        """
        Create a provider instance with the given configuration.

        Args:
            name: Provider name
            config: LLM configuration

        Returns:
            Configured LLM service instance

        Raises:
            LLMConfigurationError: If provider creation fails
        """
        provider_name = name.lower()
        provider_class = self.get_provider_class(provider_name)
        config_getter = self.get_config_getter(provider_name)

        try:
            provider_config = config_getter(config)
            if provider_config is None:
                raise LLMConfigurationError(
                    f"{provider_name.title()} configuration is missing"
                )

            return provider_class(provider_config)

        except TypeError as e:
            logger.error(
                f"Invalid configuration type for provider {provider_name}: {e}"
            )
            raise LLMConfigurationError(
                f"Invalid configuration type for {provider_name} provider: {e}"
            ) from e
        except AttributeError as e:
            logger.error(
                f"Missing configuration attribute for provider {provider_name}: {e}"
            )
            raise LLMConfigurationError(
                f"Missing configuration for {provider_name} provider: {e}"
            ) from e
        except Exception as e:
            logger.error(
                f"Failed to create LLM service for provider {provider_name}: {e}"
            )
            raise LLMConfigurationError(
                f"Failed to initialize {provider_name} provider: {e}"
            ) from e

    def list_providers(self) -> list[str]:
        """
        Get a list of all registered provider names.

        Returns:
            List of provider names
        """
        return list(self._providers.keys())


# Global registry instance
_registry = LLMProviderRegistry()


def get_provider_registry() -> LLMProviderRegistry:
    """
    Get the global LLM provider registry instance.

    Returns:
        The global provider registry
    """
    return _registry
