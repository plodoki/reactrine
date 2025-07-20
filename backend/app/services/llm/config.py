"""Configuration management for LLM services."""

from typing import Literal

from pydantic import BaseModel, Field


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI LLM provider."""

    api_key: str = Field(..., description="OpenAI API key")
    default_model: str = Field(
        default="gpt-4o-mini", description="Default model to use"
    )
    max_retries: int = Field(default=3, description="Maximum number of retries")
    timeout: int = Field(default=60, description="Request timeout in seconds")


class OpenRouterConfig(BaseModel):
    """Configuration for OpenRouter LLM provider."""

    api_key: str = Field(..., description="OpenRouter API key")
    base_url: str = Field(
        default="https://openrouter.ai/api/v1", description="OpenRouter base URL"
    )
    default_model: str = Field(
        default="google/gemini-2.5-flash", description="Default model to use"
    )
    max_retries: int = Field(default=3, description="Maximum number of retries")
    timeout: int = Field(default=60, description="Request timeout in seconds")


class BedrockConfig(BaseModel):
    """Configuration for Amazon Bedrock LLM provider."""

    region: str = Field(default="us-east-1", description="AWS region")
    model_id: str = Field(..., description="Bedrock model ID")
    access_key_id: str | None = Field(default=None, description="AWS access key ID")
    secret_access_key: str | None = Field(
        default=None, description="AWS secret access key"
    )
    max_retries: int = Field(default=3, description="Maximum number of retries")
    timeout: int = Field(default=60, description="Request timeout in seconds")


class LMStudioConfig(BaseModel):
    """Configuration for LMStudio LLM provider."""

    base_url: str = Field(..., description="LMStudio server base URL")
    default_model: str = Field(
        default="local-model", description="Default model to use"
    )
    max_retries: int = Field(default=3, description="Maximum number of retries")
    timeout: int = Field(default=60, description="Request timeout in seconds")


class LLMConfig(BaseModel):
    """Main configuration for LLM services."""

    provider: Literal["openai", "openrouter", "bedrock", "lmstudio"] = Field(
        default="openai", description="LLM provider to use"
    )
    default_model: str = Field(
        default="gpt-4o-mini", description="Default model across providers"
    )
    openai: OpenAIConfig | None = Field(
        default=None, description="OpenAI configuration"
    )
    openrouter: OpenRouterConfig | None = Field(
        default=None, description="OpenRouter configuration"
    )
    bedrock: BedrockConfig | None = Field(
        default=None, description="Bedrock configuration"
    )
    lmstudio: LMStudioConfig | None = Field(
        default=None, description="LMStudio configuration"
    )


def load_config(
    provider: str | None = None, default_model: str | None = None
) -> LLMConfig:
    """Load LLM configuration using the given provider and model."""

    from app.core.config import get_settings

    from .exceptions import LLMConfigurationError

    settings = get_settings()

    resolved_provider = provider or settings.LLM_PROVIDER
    provider = resolved_provider.lower() if resolved_provider else "openai"
    default_model = (
        default_model if default_model is not None else settings.DEFAULT_LLM_MODEL
    )

    if provider == "openai":
        openai_api_key = settings.OPENAI_API_KEY
        if not openai_api_key or openai_api_key.strip() == "":
            raise LLMConfigurationError(
                "OPENAI_API_KEY secret is required for OpenAI provider"
            )

        openai_config = OpenAIConfig(
            api_key=openai_api_key,
            default_model=default_model,
        )

        return LLMConfig(
            provider=provider,  # type: ignore
            default_model=default_model,
            openai=openai_config,
            openrouter=None,
            bedrock=None,
            lmstudio=None,
        )

    elif provider == "openrouter":
        openrouter_api_key = settings.OPENROUTER_API_KEY
        if not openrouter_api_key or openrouter_api_key.strip() == "":
            raise LLMConfigurationError(
                "OPENROUTER_API_KEY secret is required for OpenRouter provider"
            )

        # Use OPENROUTER_MODEL if available, otherwise fall back to DEFAULT_LLM_MODEL
        openrouter_model = settings.OPENROUTER_MODEL or default_model

        openrouter_config = OpenRouterConfig(
            api_key=openrouter_api_key,
            base_url=settings.OPENROUTER_BASE_URL,
            default_model=openrouter_model,
        )

        return LLMConfig(
            provider=provider,  # type: ignore
            default_model=openrouter_model,
            openai=None,
            openrouter=openrouter_config,
            bedrock=None,
            lmstudio=None,
        )

    elif provider == "bedrock":
        bedrock_model = settings.BEDROCK_MODEL
        if not bedrock_model or bedrock_model.strip() == "":
            raise LLMConfigurationError(
                "BEDROCK_MODEL environment variable is required for Bedrock provider"
            )

        bedrock_config = BedrockConfig(
            region=settings.BEDROCK_REGION,
            model_id=bedrock_model,
            access_key_id=settings.AWS_ACCESS_KEY_ID,
            secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        return LLMConfig(
            provider=provider,  # type: ignore
            default_model=bedrock_model,
            openai=None,
            openrouter=None,
            bedrock=bedrock_config,
            lmstudio=None,
        )

    elif provider == "lmstudio":
        lmstudio_base_url = settings.LMSTUDIO_BASE_URL
        if not lmstudio_base_url:
            raise LLMConfigurationError(
                "LMSTUDIO_BASE_URL environment variable is required for LMStudio provider"
            )

        # Use the passed default_model if available, otherwise fall back to LMSTUDIO_MODEL
        lmstudio_model = default_model or settings.LMSTUDIO_MODEL

        lmstudio_config = LMStudioConfig(
            base_url=lmstudio_base_url,
            default_model=lmstudio_model,
        )

        return LLMConfig(
            provider=provider,  # type: ignore
            default_model=lmstudio_model,
            openai=None,
            openrouter=None,
            bedrock=None,
            lmstudio=lmstudio_config,
        )

    else:
        raise LLMConfigurationError(f"Unsupported LLM provider: {provider}")
