"""Simple tests for LLM configuration integration with application settings."""

from unittest.mock import patch

import pytest

from app.core.config import get_settings
from app.services.llm.config import load_config
from app.services.llm.exceptions import LLMConfigurationError


def test_settings_integration():
    """Test that LLM config uses application settings."""
    settings = get_settings()

    # Verify settings have LLM configuration
    assert hasattr(settings, "LLM_PROVIDER")
    assert hasattr(settings, "DEFAULT_LLM_MODEL")
    assert hasattr(settings, "BEDROCK_REGION")
    assert hasattr(settings, "BEDROCK_MODEL")
    assert hasattr(settings, "OPENROUTER_BASE_URL")
    assert hasattr(settings, "OPENROUTER_MODEL")


@patch("app.core.secrets.read_secret")
def test_load_config_openai(mock_read_secret):
    """Test loading OpenAI configuration from settings."""
    mock_read_secret.side_effect = lambda key: {
        "openai_api_key": "test-key",
        "openrouter_api_key": None,
        "aws_access_key_id": None,
        "aws_secret_access_key": None,
    }.get(key)

    config = load_config(provider="openai", default_model="gpt-4")

    assert config.provider == "openai"
    assert config.default_model == "gpt-4"
    assert config.openai is not None
    assert config.openai.api_key == "test-key"
    assert config.openrouter is None
    assert config.bedrock is None


@patch("app.core.secrets.read_secret")
def test_load_config_openrouter(mock_read_secret):
    """Test loading OpenRouter configuration from settings."""
    mock_read_secret.side_effect = lambda key: {
        "openai_api_key": None,
        "openrouter_api_key": "test-key",
        "aws_access_key_id": None,
        "aws_secret_access_key": None,
    }.get(key)

    config = load_config(provider="openrouter", default_model="test-model")

    assert config.provider == "openrouter"
    assert config.openrouter is not None
    assert config.openrouter.api_key == "test-key"
    assert config.openrouter.base_url == "https://openrouter.ai/api/v1"
    assert config.openai is None
    assert config.bedrock is None


@patch("app.core.secrets.read_secret")
def test_load_config_bedrock(mock_read_secret):
    """Test loading Bedrock configuration from settings."""
    mock_read_secret.side_effect = lambda key: {
        "openai_api_key": None,
        "openrouter_api_key": None,
        "aws_access_key_id": "test-id",
        "aws_secret_access_key": "test-secret",
    }.get(key)

    config = load_config(provider="bedrock")

    assert config.provider == "bedrock"
    assert config.bedrock is not None
    assert config.bedrock.region == "us-east-1"
    assert config.bedrock.access_key_id == "test-id"
    assert config.bedrock.secret_access_key == "test-secret"
    assert config.openai is None
    assert config.openrouter is None


@patch("app.core.secrets.read_secret")
def test_load_config_missing_api_key_raises_error(mock_read_secret):
    """Test that missing API keys raise configuration errors."""
    mock_read_secret.return_value = None

    with pytest.raises(
        LLMConfigurationError, match="OPENAI_API_KEY secret is required"
    ):
        load_config(provider="openai")


def test_load_config_unsupported_provider_raises_error():
    """Test that unsupported providers raise configuration errors."""
    with pytest.raises(LLMConfigurationError, match="Unsupported LLM provider"):
        load_config(provider="unsupported")


@patch("app.core.config.get_settings")
def test_load_config_uses_settings_defaults(mock_get_settings):
    """Test that load_config uses default values from settings."""
    mock_settings = type(
        "MockSettings",
        (),
        {
            "LLM_PROVIDER": "bedrock",
            "DEFAULT_LLM_MODEL": "test-model",
            "BEDROCK_MODEL": "test-bedrock-model",
            "BEDROCK_REGION": "us-west-2",
            "OPENROUTER_BASE_URL": "https://custom.openrouter.ai",
            "OPENROUTER_MODEL": "custom-model",
            "OPENAI_API_KEY": None,
            "OPENROUTER_API_KEY": None,
            "AWS_ACCESS_KEY_ID": "test-id",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        },
    )()
    mock_get_settings.return_value = mock_settings

    config = load_config()  # No provider specified, should use settings default

    assert config.provider == "bedrock"
    assert config.default_model == "test-bedrock-model"
    assert config.bedrock is not None
    assert config.bedrock.region == "us-west-2"
