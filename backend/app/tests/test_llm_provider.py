import importlib
import sys
import types
from types import ModuleType
from unittest.mock import AsyncMock, patch

import pytest


def reload_llm_module(dummy_boto3: types.SimpleNamespace | None = None):
    if dummy_boto3 is not None:
        # Create a proper module wrapper for the SimpleNamespace
        dummy_module = ModuleType("boto3")
        for attr_name in dir(dummy_boto3):
            if not attr_name.startswith("_"):
                setattr(dummy_module, attr_name, getattr(dummy_boto3, attr_name))
        sys.modules["boto3"] = dummy_module

    # Clear all LLM-related modules AND config modules to ensure clean reload
    modules_to_clear = [
        "app.services.llm",
        "app.services.llm.providers",
        "app.services.llm.providers.bedrock",
        "app.services.llm.providers.openai",
        "app.services.llm.providers.openrouter",
        "app.services.llm.providers.base",
        "app.services.llm.providers.lmstudio",
        "app.services.llm.config",
        "app.services.llm.factory",
        "app.services.llm.protocol",
        "app.services.llm.exceptions",
        "app.services.llm.utils",
        "app.services.llm.registry",
        "app.services.llm.dependency_resolver",
        "app.services.llm.cache",
        "app.core.config",
        "app.core.secrets",
    ]

    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]

    return importlib.import_module("app.services.llm")


@pytest.mark.asyncio
async def test_get_llm_service_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    module = reload_llm_module()

    # Mock the database session
    mock_session = AsyncMock()
    mock_settings = type(
        "MockSettings",
        (),
        {
            "provider": "openai",
            "openai_model": "gpt-4o-mini",
            "openrouter_model": None,
            "bedrock_model": None,
            "lmstudio_model": None,
        },
    )()
    mock_session.get.return_value = mock_settings

    service = await module.get_llm_service(db=mock_session)
    assert type(service).__name__ == "OpenAILLMProvider"


@pytest.mark.asyncio
async def test_get_llm_service_bedrock(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "bedrock")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("BEDROCK_MODEL", "model")
    monkeypatch.setenv("BEDROCK_REGION", "us-east-1")

    captured: dict[str, str] = {}

    def dummy_client(*_, **kwargs):
        captured.update(kwargs)
        return object()

    dummy = types.SimpleNamespace(client=dummy_client)

    # Save the original read_secret function before patching
    from app.utils.secrets import read_secret as original_read_secret

    # Mock read_secret to return test values for AWS credentials
    def mock_read_secret(secret_name, default=None):
        if secret_name == "aws_access_key_id":
            return "test-access-key-id"
        elif secret_name == "aws_secret_access_key":
            return "test-secret-access-key"
        else:
            # For other secrets, call the original function
            result = original_read_secret(secret_name, default)
            return result

    with patch("app.utils.secrets.read_secret", side_effect=mock_read_secret):
        reload_llm_module(dummy_boto3=dummy)

        # Test BedrockLLMProvider creation directly with proper config
        from app.services.llm.config import load_config

        config = load_config(provider="bedrock", default_model="model")

        # Clear captured kwargs before creating the provider
        captured.clear()

        # Create BedrockLLMProvider directly - this should capture the AWS credentials
        if config.bedrock:
            from app.services.llm.providers.bedrock import BedrockLLMProvider

            provider = BedrockLLMProvider(config.bedrock)
            assert type(provider).__name__ == "BedrockLLMProvider"

        # Verify that boto3.client was called with the expected AWS credentials
        assert "aws_access_key_id" in captured
        assert "aws_secret_access_key" in captured
        assert captured["aws_access_key_id"] == "test-access-key-id"
        assert captured["aws_secret_access_key"] == "test-secret-access-key"


@pytest.mark.asyncio
async def test_get_llm_service_openrouter(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")

    # Import fresh modules to avoid cached state
    import sys

    # Clear specific modules that might be cached
    for module_name in ["app.services.llm.registry", "app.services.llm.factory"]:
        if module_name in sys.modules:
            del sys.modules[module_name]

    # Import the modules fresh
    from app.services.llm.config import load_config
    from app.services.llm.factory import LLMServiceFactory

    # Test direct provider creation
    config = load_config(provider="openrouter", default_model="gpt-4o-mini")
    service = LLMServiceFactory.create_service(config)
    assert type(service).__name__ == "OpenRouterLLMProvider"
