from sqlmodel import Field, SQLModel


class LLMSettings(SQLModel, table=True):
    """Model for storing LLM provider configuration."""

    id: int | None = Field(default=1, primary_key=True)
    provider: str = Field(index=True)
    openai_model: str | None = None
    openrouter_model: str | None = None
    bedrock_model: str | None = None
    lmstudio_model: str | None = None
