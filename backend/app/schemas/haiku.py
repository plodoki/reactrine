import re
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator


class HaikuRequest(BaseModel):
    """
    Schema for a request to generate a haiku.
    """

    topic: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="The topic for the haiku (1-200 characters, descriptive content)",
    )
    style: str = Field(
        "traditional",
        min_length=1,
        max_length=50,
        description="The style of haiku to generate (e.g., traditional, modern, nature, urban)",
    )
    provider: Literal["openai", "openrouter", "bedrock", "lmstudio"] | None = Field(
        default=None,
        description="Optional LLM provider to use. If not specified, uses the current default provider.",
    )
    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Optional model name to use. If not specified, uses the provider's default model.",
    )

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validate topic content and format."""
        # Remove leading/trailing whitespace
        v = v.strip()

        # Check if empty after stripping
        if not v:
            raise ValueError("Topic cannot be empty or whitespace only")

        # Check for reasonable content - allow letters, numbers, spaces, basic punctuation
        if not re.match(r"^[a-zA-Z0-9\s\-_.,!?()]+$", v):
            raise ValueError(
                "Topic can only contain letters, numbers, spaces, and basic punctuation"
            )

        # Check for consecutive spaces
        if "  " in v:
            raise ValueError("Topic cannot contain consecutive spaces")

        return v

    @field_validator("style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        """Validate style format."""
        # Remove leading/trailing whitespace
        v = v.strip()

        # Check if empty after stripping
        if not v:
            raise ValueError("Style cannot be empty or whitespace only")

        # Check pattern - allow letters, numbers, spaces, hyphens
        if not re.match(r"^[a-zA-Z0-9\s\-]+$", v):
            raise ValueError(
                "Style can only contain letters, numbers, spaces, and hyphens"
            )

        # Check for consecutive spaces
        if "  " in v:
            raise ValueError("Style cannot contain consecutive spaces")

        return v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str | None) -> str | None:
        """Validate model name format."""
        if v is not None:
            # Remove leading/trailing whitespace
            v = v.strip()

            # Check if empty after stripping
            if not v:
                raise ValueError("Model name cannot be empty or whitespace only")

            # Check pattern - allow letters, numbers, hyphens, underscores, dots, forward slashes
            if not re.match(r"^[a-zA-Z0-9\-_./]+$", v):
                raise ValueError(
                    "Model name can only contain letters, numbers, hyphens, underscores, dots, and forward slashes"
                )

        return v


class HaikuResponse(BaseModel):
    """
    Schema for the response containing the generated haiku.
    """

    haiku: str = Field(description="The complete generated haiku text.")
    lines: List[str] = Field(description="The individual lines of the haiku.")
    syllables: List[int] = Field(description="The syllable count for each line.")
    model_used: str = Field(
        description="The name of the LLM that generated the response."
    )
    provider_used: str = Field(
        description="The LLM provider that was used to generate the response."
    )
