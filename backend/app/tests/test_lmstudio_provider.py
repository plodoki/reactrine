"""Tests for LMStudio LLM provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm.config import LMStudioConfig
from app.services.llm.exceptions import LLMProviderError
from app.services.llm.providers.lmstudio import LMStudioLLMProvider


@pytest.fixture
def lmstudio_config():
    """Create a test LMStudio configuration."""
    return LMStudioConfig(
        base_url="http://localhost:1234/v1",
        default_model="test-model",
    )


@pytest.fixture
def lmstudio_provider(lmstudio_config):
    """Create a test LMStudio provider."""
    return LMStudioLLMProvider(lmstudio_config)


class TestLMStudioProvider:
    """Test cases for LMStudio provider."""

    def test_init(self, lmstudio_config):
        """Test provider initialization."""
        provider = LMStudioLLMProvider(lmstudio_config)

        assert provider.default_model == "test-model"
        assert provider.base_url == "http://localhost:1234/v1"
        assert str(provider.client.base_url) == "http://localhost:1234/v1/"

    @pytest.mark.asyncio
    async def test_get_available_models_success(self, lmstudio_provider):
        """Test successful model fetching."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"id": "llama-3-8b"}, {"id": "mistral-7b"}, {"id": "codellama-7b"}]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            models = await lmstudio_provider.get_available_models()

            assert models == ["llama-3-8b", "mistral-7b", "codellama-7b"]
            mock_client_instance.get.assert_called_once_with(
                "http://localhost:1234/v1/models"
            )

    @pytest.mark.asyncio
    async def test_get_available_models_empty_response(self, lmstudio_provider):
        """Test handling of empty model response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            models = await lmstudio_provider.get_available_models()

            assert models == []

    @pytest.mark.asyncio
    async def test_get_available_models_http_error(self, lmstudio_provider):
        """Test handling of HTTP errors when fetching models."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = Exception("Connection refused")
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(
                LLMProviderError, match="Unexpected error fetching models"
            ):
                await lmstudio_provider.get_available_models()

    @pytest.mark.asyncio
    async def test_get_response_success(self, lmstudio_provider):
        """Test successful response generation."""
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from LMStudio!"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            lmstudio_provider.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response

            response = await lmstudio_provider.get_response("Hello")

            assert response == "Hello from LMStudio!"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_response_with_model_override(self, lmstudio_provider):
        """Test response generation with model override."""
        mock_choice = MagicMock()
        mock_choice.message.content = "Response from custom model"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch.object(
            lmstudio_provider.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_response

            response = await lmstudio_provider.get_response(
                "Hello", model="custom-model"
            )

            assert response == "Response from custom model"
            # Verify the correct model was used
            call_args = mock_create.call_args
            assert call_args[1]["model"] == "custom-model"

    @pytest.mark.asyncio
    async def test_stream_response_success(self, lmstudio_provider):
        """Test successful streaming response."""
        # Mock streaming chunks
        mock_chunks = []
        for i, content in enumerate(["Hello", " from", " LMStudio!"]):
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = content
            mock_chunks.append(chunk)

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        with patch.object(
            lmstudio_provider.client.chat.completions, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_stream()

            chunks = []
            async for chunk in lmstudio_provider.stream_response("Hello"):
                chunks.append(chunk)

            assert chunks == ["Hello", " from", " LMStudio!"]

    def test_model_selection(self, lmstudio_provider):
        """Test model selection logic."""
        # Test default model
        assert lmstudio_provider._get_model(None) == "test-model"

        # Test model override
        assert lmstudio_provider._get_model("custom-model") == "custom-model"
