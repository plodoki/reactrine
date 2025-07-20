import logging
import os

import syllables  # type: ignore
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils import handle_llm_error
from app.db.session import get_db_session
from app.schemas.haiku import HaikuRequest, HaikuResponse
from app.services.llm import (
    LLMGenerationError,
    LLMService,
    get_llm_service_with_overrides,
)

logger = logging.getLogger(__name__)


# Configuration
def get_haiku_model() -> str | None:
    """
    Get the model to use for haiku generation.

    Returns None to use the provider's default model, unless HAIKU_MODEL is explicitly set.
    """
    # If HAIKU_MODEL is explicitly set, use it to override the provider's default
    return os.getenv("HAIKU_MODEL")


class HaikuService:
    def __init__(
        self,
        llm_service: LLMService,
        model: str | None = None,
        provider: str | None = None,
    ) -> None:
        self.llm_service = llm_service
        self.model = model
        self.provider = provider

    async def generate_haiku(self, request: HaikuRequest) -> HaikuResponse:
        """
        Generates a haiku based on a topic and style using the LLMService.
        """
        prompt = self._build_prompt(request.topic, request.style)

        try:
            # Only pass model if it's specified (not None)
            response_text = await self.llm_service.get_response(
                prompt=prompt,
                model=self.model,
                max_tokens=150,
            )

            lines = [
                line.strip()
                for line in response_text.strip().split("\n")
                if line.strip()
            ]

            if len(lines) != 3:
                raise LLMGenerationError(
                    f"LLM returned {len(lines)} lines, expected 3."
                )

            # Use proper syllable counting library
            def count_syllables(word: str) -> int:
                count = syllables.estimate(word)
                return (
                    max(count, 1) if count is not None else 1
                )  # Ensure at least 1 syllable

            syllable_counts = [
                sum(count_syllables(word) for word in line.split()) for line in lines
            ]

            return HaikuResponse(
                haiku="\n".join(lines),
                lines=lines,
                syllables=syllable_counts,
                model_used=self.model or "provider_default",
                provider_used=self.provider or "default",
            )
        except LLMGenerationError as e:
            handle_llm_error(e, f"haiku generation for topic '{request.topic}'")

    def _build_prompt(self, topic: str, style: str) -> str:
        """
        Builds a structured prompt for the LLM.
        """
        return f"""
        Generate a creative, three-line haiku with a 5, 7, 5 syllable structure.
        Topic: "{topic}"
        Style: {style}

        Respond with only the three lines of the haiku, separated by newlines. Do not include a title or any other text.
        """


async def get_haiku_service_default(
    db: AsyncSession = Depends(get_db_session),
) -> HaikuService:
    """
    FastAPI dependency that creates a haiku service with default LLM configuration.
    """
    # Use get_llm_service_with_overrides to get actual provider/model info
    result = await get_llm_service_with_overrides(
        provider=None, model=get_haiku_model(), db=db
    )
    return HaikuService(result.service, result.model, result.provider)


async def get_haiku_service_with_overrides(
    provider: str | None = None,
    model: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> HaikuService:
    """
    Create a haiku service with optional provider and model overrides.

    Args:
        provider: Optional LLM provider override
        model: Optional model override
        db: Database session

    Returns:
        HaikuService configured with the specified or default provider/model
    """
    result = await get_llm_service_with_overrides(provider=provider, model=model, db=db)

    # Use the overridden model if specified, otherwise fall back to HAIKU_MODEL env var or actual_model
    final_model = model or get_haiku_model() or result.model

    return HaikuService(result.service, final_model, result.provider)


# Create a FastAPI dependency
HaikuServiceDep = Depends(get_haiku_service_default)
