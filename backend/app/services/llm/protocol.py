"""Protocol definition for LLM service interface."""

from collections.abc import AsyncIterator
from typing import Any, Protocol, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMService(Protocol):
    """
    A protocol defining the interface for a large language model service.

    This protocol ensures all LLM providers implement the same interface,
    allowing for easy swapping between different providers (OpenAI, Bedrock, etc.).
    """

    async def get_response(
        self,
        prompt: str,
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> str:
        """
        Generates a simple text response from the LLM.

        Args:
            prompt: The input prompt for the LLM
            model: Optional model override
            **kwargs: Provider-specific parameters

        Returns:
            The generated text response

        Raises:
            LLMGenerationError: If response generation fails
        """
        ...

    async def get_structured_response(
        self,
        prompt: str,
        response_model: Type[T],
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """
        Generates a response conforming to the provided Pydantic model.

        Args:
            prompt: The input prompt for the LLM
            response_model: Pydantic model class for response validation
            model: Optional model override
            **kwargs: Provider-specific parameters

        Returns:
            Validated response instance of the specified model

        Raises:
            LLMGenerationError: If response generation fails
            LLMValidationError: If response doesn't match the model
        """
        ...

    async def stream_response(
        self,
        prompt: str,
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> AsyncIterator[str]:
        """
        Streams text responses from the LLM.

        Args:
            prompt: The input prompt for the LLM
            model: Optional model override
            **kwargs: Provider-specific parameters

        Yields:
            Chunks of the generated text response

        Raises:
            LLMGenerationError: If streaming fails
        """
        ...
