"""
LLM Service Module

This module provides a unified interface for interacting with various Large Language Model providers.
It supports OpenAI and Amazon Bedrock out of the box, with an extensible architecture for adding
new providers.

Usage:
    from app.services.llm import LLMService, LLMServiceDep, get_llm_service

    # In FastAPI endpoints
    async def my_endpoint(llm_service: LLMService = LLMServiceDep):
        response = await llm_service.get_response("Hello, world!")
        return {"response": response}
"""

# Configuration
# Caching
from .cache import (
    LLMServiceCache,
    LLMSettingsCache,
    get_llm_service_cache,
    get_llm_settings_cache,
)
from .config import LLMConfig, load_config

# Dependency resolution and FastAPI integration
from .dependency_resolver import (
    LLMServiceDep,
    LLMServiceResult,
    ensure_llm_settings,
    get_llm_service,
    get_llm_service_with_overrides,
)

# Exceptions
from .exceptions import (
    LLMConfigurationError,
    LLMGenerationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMValidationError,
)

# Factory
from .factory import LLMServiceFactory

# Core interfaces and types
from .protocol import LLMService

# Provider implementations (for advanced usage)
from .providers import (
    BaseLLMProvider,
    BedrockLLMProvider,
    LMStudioLLMProvider,
    OpenAILLMProvider,
    OpenRouterLLMProvider,
)

# Registry for provider management
from .registry import LLMProviderRegistry, get_provider_registry

# Utilities
from .utils import parse_json_response, retry_on_failure

# Backward compatibility - maintain the same exports as the original llm.py
# This allows existing code to continue working without changes
DEFAULT_MODEL = "gpt-4o-mini"  # For backward compatibility

# Legacy class names for backward compatibility
OpenAILLMService = OpenAILLMProvider
BedrockLLMService = BedrockLLMProvider
OpenRouterLLMService = OpenRouterLLMProvider
LMStudioLLMService = LMStudioLLMProvider

__all__ = [
    # Core interface
    "LLMService",
    # Exceptions
    "LLMGenerationError",
    "LLMConfigurationError",
    "LLMProviderError",
    "LLMRateLimitError",
    "LLMValidationError",
    # Configuration
    "LLMConfig",
    "load_config",
    # Caching
    "LLMSettingsCache",
    "LLMServiceCache",
    "get_llm_settings_cache",
    "get_llm_service_cache",
    # Factory and DI
    "LLMServiceFactory",
    "get_llm_service",
    "get_llm_service_with_overrides",
    "LLMServiceDep",
    "LLMServiceResult",
    "ensure_llm_settings",
    # Registry
    "LLMProviderRegistry",
    "get_provider_registry",
    # Providers
    "BaseLLMProvider",
    "OpenAILLMProvider",
    "OpenRouterLLMProvider",
    "BedrockLLMProvider",
    "LMStudioLLMProvider",
    # Utilities
    "parse_json_response",
    "retry_on_failure",
    # Backward compatibility
    "DEFAULT_MODEL",
    "OpenAILLMService",
    "OpenRouterLLMService",
    "BedrockLLMService",
    "LMStudioLLMService",
]
