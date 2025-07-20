"""Tests for LLM service factory."""

from unittest.mock import Mock

import pytest

from app.services.llm.config import (
    BedrockConfig,
    LLMConfig,
    OpenAIConfig,
    OpenRouterConfig,
)
from app.services.llm.exceptions import LLMConfigurationError
from app.services.llm.factory import LLMServiceFactory
from app.services.llm.providers.base import BaseLLMProvider
from app.services.llm.registry import get_provider_registry


class MockProvider(BaseLLMProvider):
    """Mock provider for testing."""

    def __init__(self, config):
        self.config = config
        super().__init__("mock-model")

    async def get_response(
        self, prompt: str, model: str | None = None, **kwargs
    ) -> str:
        return "mock response"

    async def stream_response(self, prompt: str, model: str | None = None, **kwargs):
        """Stream mock responses."""
        yield "mock "
        yield "streaming "
        yield "response"


def test_create_service_openai():
    """Test creating OpenAI service."""
    config = LLMConfig(
        provider="openai",
        default_model="gpt-4",
        openai=OpenAIConfig(api_key="test-key", default_model="gpt-4"),
    )

    service = LLMServiceFactory.create_service(config)
    assert service is not None


def test_create_service_openrouter():
    """Test creating OpenRouter service."""
    config = LLMConfig(
        provider="openrouter",
        default_model="gpt-4",
        openrouter=OpenRouterConfig(api_key="test-key", default_model="gpt-4"),
    )

    service = LLMServiceFactory.create_service(config)
    assert service is not None


def test_create_service_bedrock():
    """Test creating Bedrock service."""
    config = LLMConfig(
        provider="bedrock",
        default_model="claude-3",
        bedrock=BedrockConfig(model_id="claude-3", region="us-east-1"),
    )

    service = LLMServiceFactory.create_service(config)
    assert service is not None


def test_create_service_unsupported_provider():
    """Test error handling for unsupported provider."""
    # Create a mock config that bypasses Pydantic validation
    mock_config = Mock()
    mock_config.provider = "unsupported"

    with pytest.raises(LLMConfigurationError) as exc_info:
        LLMServiceFactory.create_service(mock_config)

    assert "Unsupported LLM provider: unsupported" in str(exc_info.value)
    assert "Available:" in str(exc_info.value)


def test_create_service_missing_config():
    """Test error handling when provider config is missing."""
    config = LLMConfig(
        provider="openai", default_model="gpt-4", openai=None  # Missing config
    )

    with pytest.raises(LLMConfigurationError) as exc_info:
        LLMServiceFactory.create_service(config)

    assert "Openai configuration is missing" in str(exc_info.value)


def test_register_provider():
    """Test registering a new provider."""
    registry = get_provider_registry()

    # Register mock provider
    LLMServiceFactory.register_provider(
        "mock", MockProvider, lambda config: Mock()  # Return a mock config object
    )

    # Verify provider is registered
    providers = registry.list_providers()
    assert "mock" in providers
    assert registry.get_provider_class("mock") == MockProvider

    # Test using the registered provider with a mock config
    mock_config = Mock()
    mock_config.provider = "mock"

    service = LLMServiceFactory.create_service(mock_config)
    assert isinstance(service, MockProvider)


def test_register_provider_no_config_getter():
    """Test registering provider without config getter."""
    registry = get_provider_registry()

    # Register provider without config getter
    LLMServiceFactory.register_provider("test", MockProvider)

    # Verify provider is registered
    providers = registry.list_providers()
    assert "test" in providers

    # Test error when trying to use provider without config getter
    mock_config = Mock()
    mock_config.provider = "test"

    with pytest.raises(LLMConfigurationError) as exc_info:
        LLMServiceFactory.create_service(mock_config)

    assert "No configuration handler for provider: test" in str(exc_info.value)


def test_config_mapping_structure():
    """Test that the provider config mapping is correctly structured."""
    registry = get_provider_registry()

    # Test that all registered providers have config getters (excluding test providers)
    providers = registry.list_providers()
    for provider_name in providers:
        # Skip test providers that were registered without config getters
        if provider_name in ["test", "mock"]:
            continue
        # Should not raise an exception
        registry.get_config_getter(provider_name)

    # Test that config getters work correctly for valid configs
    openai_config = LLMConfig(
        provider="openai", openai=OpenAIConfig(api_key="test", default_model="gpt-4")
    )

    openai_getter = registry.get_config_getter("openai")
    assert openai_getter(openai_config) == openai_config.openai

    openrouter_config = LLMConfig(
        provider="openrouter",
        openrouter=OpenRouterConfig(api_key="test", default_model="gpt-4"),
    )

    openrouter_getter = registry.get_config_getter("openrouter")
    assert openrouter_getter(openrouter_config) == openrouter_config.openrouter

    bedrock_config = LLMConfig(
        provider="bedrock",
        bedrock=BedrockConfig(model_id="claude-3", region="us-east-1"),
    )

    bedrock_getter = registry.get_config_getter("bedrock")
    assert bedrock_getter(bedrock_config) == bedrock_config.bedrock
