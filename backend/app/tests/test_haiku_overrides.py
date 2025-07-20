"""Tests for haiku service with provider and model overrides."""

from unittest.mock import MagicMock, patch

import pytest

from app.models.llm_settings import LLMSettings
from app.schemas.haiku import HaikuRequest
from app.services.haiku import get_haiku_service_with_overrides
from app.services.llm import LLMServiceResult, get_llm_service_with_overrides
from app.services.llm.providers.base import BaseLLMProvider


@pytest.mark.asyncio
async def test_get_llm_service_with_overrides_default():
    """Test get_llm_service_with_overrides with default settings."""
    from app.tests.mocks import create_mock_db_session

    # Create mock settings with bedrock as default (matches system default)
    mock_settings = LLMSettings(
        id=1,
        provider="bedrock",
        openai_model="gpt-4o-mini",
        openrouter_model="google/gemini-2.5-flash",
        bedrock_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        lmstudio_model="llama-3.2-3b-instruct",
    )

    async for mock_db in create_mock_db_session():
        mock_db.get.return_value = mock_settings

        # Mock environment variables for bedrock
        with patch.dict(
            "os.environ",
            {
                "AWS_ACCESS_KEY_ID": "test-key",
                "AWS_SECRET_ACCESS_KEY": "test-secret",
                "BEDROCK_MODEL": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            },
        ):
            result = await get_llm_service_with_overrides(db=mock_db)

            # Verify the result
            assert isinstance(result, LLMServiceResult)
            assert result.provider == "openrouter"
            assert result.model == "google/gemini-2.5-flash"
            assert result.service is not None


@pytest.mark.asyncio
async def test_get_llm_service_with_overrides_provider_only():
    """Test get_llm_service_with_overrides with provider override only."""
    from app.tests.mocks import create_mock_db_session

    # Create mock settings
    mock_settings = LLMSettings(
        id=1,
        provider="openai",  # Default provider
        openai_model="gpt-4o-mini",
        openrouter_model="google/gemini-2.5-flash",
        bedrock_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        lmstudio_model="llama-3.2-3b-instruct",
    )

    async for mock_db in create_mock_db_session():
        mock_db.get.return_value = mock_settings

        # Mock environment variables
        with patch.dict(
            "os.environ",
            {"OPENROUTER_API_KEY": "test-key", "OPENAI_API_KEY": "test-key"},
        ):
            result = await get_llm_service_with_overrides(
                provider="openrouter", db=mock_db
            )

            # Verify that OpenRouter provider is used with its default model
            assert isinstance(result, LLMServiceResult)
            assert result.provider == "openrouter"
            assert result.model == "google/gemini-2.5-flash"
            assert result.service is not None


@pytest.mark.asyncio
async def test_get_llm_service_with_overrides_model_only():
    """Test get_llm_service_with_overrides with model override only."""
    from app.tests.mocks import create_mock_db_session

    # Create mock settings with bedrock as default (matches system default)
    mock_settings = LLMSettings(
        id=1,
        provider="bedrock",
        openai_model="gpt-4o-mini",
        openrouter_model="google/gemini-2.5-flash",
        bedrock_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        lmstudio_model="llama-3.2-3b-instruct",
    )

    async for mock_db in create_mock_db_session():
        mock_db.get.return_value = mock_settings

        # Mock environment variables for bedrock
        with patch.dict(
            "os.environ",
            {
                "AWS_ACCESS_KEY_ID": "test-key",
                "AWS_SECRET_ACCESS_KEY": "test-secret",
                "BEDROCK_MODEL": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            },
        ):
            result = await get_llm_service_with_overrides(
                model="us.anthropic.claude-3-haiku-20240307-v1:0", db=mock_db
            )

            # Verify that default provider is used with overridden model
            assert isinstance(result, LLMServiceResult)
            assert result.provider == "openrouter"
            assert result.model == "us.anthropic.claude-3-haiku-20240307-v1:0"
            assert result.service is not None


@pytest.mark.asyncio
async def test_get_llm_service_with_overrides_both():
    """Test get_llm_service_with_overrides with both provider and model overrides."""
    from app.tests.mocks import create_mock_db_session

    # Create mock settings
    mock_settings = LLMSettings(
        id=1,
        provider="openai",  # Default provider
        openai_model="gpt-4o-mini",
        openrouter_model="google/gemini-2.5-flash",
        bedrock_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        lmstudio_model="llama-3.2-3b-instruct",
    )

    async for mock_db in create_mock_db_session():
        mock_db.get.return_value = mock_settings

        # Mock environment variables
        with patch.dict(
            "os.environ",
            {"OPENROUTER_API_KEY": "test-key", "OPENAI_API_KEY": "test-key"},
        ):
            result = await get_llm_service_with_overrides(
                provider="openrouter", model="custom-model", db=mock_db
            )

            # Verify that both overrides are applied
            assert isinstance(result, LLMServiceResult)
            assert result.provider == "openrouter"
            assert result.model == "custom-model"
            assert result.service is not None


@pytest.mark.asyncio
async def test_get_haiku_service_with_overrides():
    """Test the haiku service with overrides."""
    with patch("app.services.haiku.get_llm_service_with_overrides") as mock_get_llm:
        # Mock the LLM service result
        mock_service = MagicMock(spec=BaseLLMProvider)
        mock_result = LLMServiceResult(
            service=mock_service,
            provider="bedrock",
            model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        )
        mock_get_llm.return_value = mock_result

        # Test the haiku service creation
        haiku_service = await get_haiku_service_with_overrides(
            provider="bedrock", model="us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

        # Verify that the service was created with correct provider/model
        assert haiku_service.provider == "bedrock"
        assert haiku_service.model == "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert haiku_service.llm_service == mock_service


def test_haiku_request_schema_with_overrides():
    """Test that HaikuRequest accepts provider and model parameters."""
    request = HaikuRequest(
        topic="nature", style="traditional", provider="openrouter", model="gpt-4"
    )

    assert request.topic == "nature"
    assert request.style == "traditional"
    assert request.provider == "openrouter"
    assert request.model == "gpt-4"


def test_haiku_request_schema_without_overrides():
    """Test that HaikuRequest works without provider and model parameters."""
    request = HaikuRequest(topic="nature", style="traditional")

    assert request.topic == "nature"
    assert request.style == "traditional"
    assert request.provider is None
    assert request.model is None
