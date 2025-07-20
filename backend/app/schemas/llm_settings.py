import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LLMSettingsSchema(BaseModel):
    """Schema for LLM settings."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Settings ID")
    provider: Literal["openai", "openrouter", "bedrock", "lmstudio"] = Field(
        ..., description="Active LLM provider"
    )
    openai_model: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="OpenAI model name (required when provider=openai)",
    )
    openrouter_model: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="OpenRouter model name (required when provider=openrouter)",
    )
    bedrock_model: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="AWS Bedrock model name (required when provider=bedrock)",
    )
    lmstudio_model: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="LMStudio model name (required when provider=lmstudio)",
    )

    @field_validator(
        "openai_model", "openrouter_model", "bedrock_model", "lmstudio_model"
    )
    @classmethod
    def validate_model_names(cls, v: str | None) -> str | None:
        """Validate model names follow expected patterns."""
        if v is not None:
            # Remove leading/trailing whitespace
            v = str(v).strip()

            # Allow empty strings (for non-active providers)
            if not v:
                return None

            # Validate model name length
            if len(v) > 200:
                raise ValueError("Model name must be less than 200 characters")

            # Basic validation - model names shouldn't contain certain characters
            if re.search(r"[<>\"\'&]", v):
                raise ValueError("Model name contains invalid characters")

            return v

        return None


class LLMSettingsCreateSchema(BaseModel):
    """Schema for creating LLM settings."""

    model_config = ConfigDict()

    provider: Literal["openai", "openrouter", "bedrock", "lmstudio"] = Field(
        ..., description="Active LLM provider"
    )
    openai_model: Optional[str] = Field(
        None,
        description="OpenAI model name (required when provider=openai)",
    )
    openrouter_model: Optional[str] = Field(
        None,
        description="OpenRouter model name (required when provider=openrouter)",
    )
    bedrock_model: Optional[str] = Field(
        None,
        description="AWS Bedrock model name (required when provider=bedrock)",
    )
    lmstudio_model: Optional[str] = Field(
        None,
        description="LMStudio model name (required when provider=lmstudio)",
    )

    @field_validator(
        "openai_model", "openrouter_model", "bedrock_model", "lmstudio_model"
    )
    @classmethod
    def validate_model_names(cls, v: str | None) -> str | None:
        """Validate model names follow expected patterns."""
        if v is not None:
            # Convert to string and remove leading/trailing whitespace
            v = str(v).strip()

            # For create schema, we don't return None for empty strings
            # Let the model validator handle provider-specific requirements

            # Validate model name length
            if len(v) > 200:
                raise ValueError("Model name must be less than 200 characters")

            # Basic validation - model names shouldn't contain certain characters
            if re.search(r"[<>\"\'&]", v):
                raise ValueError("Model name contains invalid characters")

            return v

        return None

    @model_validator(mode="after")
    def validate_provider_model_combination(self) -> "LLMSettingsCreateSchema":
        """Validate that the selected provider has a corresponding model."""
        if self.provider == "openai" and (
            not self.openai_model or not self.openai_model.strip()
        ):
            raise ValueError(
                "OpenAI model is required when provider is set to 'openai'"
            )
        elif self.provider == "openrouter" and (
            not self.openrouter_model or not self.openrouter_model.strip()
        ):
            raise ValueError(
                "OpenRouter model is required when provider is set to 'openrouter'"
            )
        elif self.provider == "bedrock" and (
            not self.bedrock_model or not self.bedrock_model.strip()
        ):
            raise ValueError(
                "Bedrock model is required when provider is set to 'bedrock'"
            )
        elif self.provider == "lmstudio" and (
            not self.lmstudio_model or not self.lmstudio_model.strip()
        ):
            raise ValueError(
                "LMStudio model is required when provider is set to 'lmstudio'"
            )

        return self


class LLMSettingsUpdateSchema(BaseModel):
    """Schema for updating LLM settings."""

    model_config = ConfigDict()

    provider: Optional[Literal["openai", "openrouter", "bedrock", "lmstudio"]] = Field(
        None, description="Active LLM provider"
    )
    openai_model: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="OpenAI model name (required when provider=openai)",
    )
    openrouter_model: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="OpenRouter model name (required when provider=openrouter)",
    )
    bedrock_model: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="AWS Bedrock model name (required when provider=bedrock)",
    )
    lmstudio_model: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="LMStudio model name (required when provider=lmstudio)",
    )

    @field_validator(
        "openai_model", "openrouter_model", "bedrock_model", "lmstudio_model"
    )
    @classmethod
    def validate_model_names(cls, v: str | None) -> str | None:
        """Validate model names follow expected patterns."""
        if v is not None:
            # Remove leading/trailing whitespace
            v = str(v).strip()

            # Allow empty strings (for non-active providers)
            if not v:
                return None

            # Validate model name length
            if len(v) > 200:
                raise ValueError("Model name must be less than 200 characters")

            # Basic validation - model names shouldn't contain certain characters
            if re.search(r"[<>\"\'&]", v):
                raise ValueError("Model name contains invalid characters")

            return v

        return None
