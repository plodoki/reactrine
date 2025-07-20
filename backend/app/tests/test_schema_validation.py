import pytest
from pydantic import ValidationError

from app.schemas.llm_settings import LLMSettingsCreateSchema


class TestLLMSettingsCreateSchemaValidation:
    """Test Pydantic validation for LLMSettingsCreateSchema."""

    def test_valid_openai_config(self):
        """Test valid OpenAI configuration."""
        data = {
            "provider": "openai",
            "openai_model": "gpt-4o-mini",
        }
        schema = LLMSettingsCreateSchema(**data)
        assert schema.provider == "openai"
        assert schema.openai_model == "gpt-4o-mini"

    def test_valid_openrouter_config(self):
        """Test valid OpenRouter configuration."""
        data = {
            "provider": "openrouter",
            "openrouter_model": "microsoft/wizard-lm-2-8x22b",
        }
        schema = LLMSettingsCreateSchema(**data)
        assert schema.provider == "openrouter"
        assert schema.openrouter_model == "microsoft/wizard-lm-2-8x22b"

    def test_valid_bedrock_config(self):
        """Test valid Bedrock configuration."""
        data = {
            "provider": "bedrock",
            "bedrock_model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        }
        schema = LLMSettingsCreateSchema(**data)
        assert schema.provider == "bedrock"
        assert schema.bedrock_model == "anthropic.claude-3-5-sonnet-20241022-v2:0"

    def test_valid_lmstudio_config(self):
        """Test valid LMStudio configuration."""
        data = {
            "provider": "lmstudio",
            "lmstudio_model": "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF",
        }
        schema = LLMSettingsCreateSchema(**data)
        assert schema.provider == "lmstudio"
        assert (
            schema.lmstudio_model
            == "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF"
        )

    def test_missing_required_model_for_openai(self):
        """Test validation fails when OpenAI provider is missing required model."""
        data = {
            "provider": "openai",
            # Missing openai_model
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMSettingsCreateSchema(**data)

        errors = exc_info.value.errors()
        assert any(
            "OpenAI model is required when provider is set to 'openai'" in str(error)
            for error in errors
        )

    def test_missing_required_model_for_openrouter(self):
        """Test validation fails when OpenRouter provider is missing required model."""
        data = {
            "provider": "openrouter",
            # Missing openrouter_model
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMSettingsCreateSchema(**data)

        errors = exc_info.value.errors()
        assert any(
            "OpenRouter model is required when provider is set to 'openrouter'"
            in str(error)
            for error in errors
        )

    def test_missing_required_model_for_bedrock(self):
        """Test validation fails when Bedrock provider is missing required model."""
        data = {
            "provider": "bedrock",
            # Missing bedrock_model
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMSettingsCreateSchema(**data)

        errors = exc_info.value.errors()
        assert any(
            "Bedrock model is required when provider is set to 'bedrock'" in str(error)
            for error in errors
        )

    def test_missing_required_model_for_lmstudio(self):
        """Test validation fails when LMStudio provider is missing required model."""
        data = {
            "provider": "lmstudio",
            # Missing lmstudio_model
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMSettingsCreateSchema(**data)

        errors = exc_info.value.errors()
        assert any(
            "LMStudio model is required when provider is set to 'lmstudio'"
            in str(error)
            for error in errors
        )

    def test_empty_string_model_for_openai(self):
        """Test validation fails when OpenAI model is empty string."""
        data = {
            "provider": "openai",
            "openai_model": "",
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMSettingsCreateSchema(**data)

        errors = exc_info.value.errors()
        assert any(
            "OpenAI model is required when provider is set to 'openai'" in str(error)
            for error in errors
        )

    def test_whitespace_only_model_for_openai(self):
        """Test validation fails when OpenAI model is whitespace only."""
        data = {
            "provider": "openai",
            "openai_model": "   ",
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMSettingsCreateSchema(**data)

        errors = exc_info.value.errors()
        assert any(
            "OpenAI model is required when provider is set to 'openai'" in str(error)
            for error in errors
        )

    def test_invalid_model_name_with_special_characters(self):
        """Test validation fails with invalid characters in model name."""
        data = {
            "provider": "openai",
            "openai_model": "gpt-4<script>",
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMSettingsCreateSchema(**data)

        errors = exc_info.value.errors()
        assert any(
            "Model name contains invalid characters" in str(error) for error in errors
        )

    def test_model_name_too_long(self):
        """Test validation fails when model name is too long."""
        long_model_name = "a" * 201  # Exceeds 200 character limit
        data = {
            "provider": "openai",
            "openai_model": long_model_name,
        }
        with pytest.raises(ValidationError) as exc_info:
            LLMSettingsCreateSchema(**data)

        errors = exc_info.value.errors()
        assert any(
            "Model name must be less than 200 characters" in str(error)
            for error in errors
        )
