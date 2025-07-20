"""Base class for all LLM providers."""

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Type, TypeVar

from pydantic import BaseModel

from app.utils.performance import timing_decorator

from ..exceptions import LLMGenerationError
from ..utils import parse_json_response

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Provides common functionality and enforces the interface contract.
    """

    def __init__(self, default_model: str) -> None:
        """
        Initialize the base provider.

        Args:
            default_model: Default model to use for requests
        """
        self.default_model = default_model
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def get_response(
        self,
        prompt: str,
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> str:
        """Generate a simple text response."""
        ...

    @timing_decorator
    async def get_structured_response(
        self,
        prompt: str,
        response_model: Type[T],
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """
        Generate a structured response using the base implementation.

        This method can be overridden by providers that have native structured response support.
        """
        # Add JSON formatting instruction to the prompt
        json_prompt = self._format_structured_prompt(prompt, response_model)
        model_key = self._get_model(model)
        self._log_llm_call("get_structured_response", model_key, **kwargs)

        try:
            response_text = await self.get_response(json_prompt, model=model, **kwargs)
            return parse_json_response(response_text, response_model)
        except LLMGenerationError:
            # Re-raise LLM generation errors without modification
            raise
        except ValueError as e:
            self.logger.error(f"JSON parsing error in structured response: {e}")
            raise LLMGenerationError(f"Failed to parse structured response: {e}") from e
        except TypeError as e:
            self.logger.error(f"Type error in structured response: {e}")
            raise LLMGenerationError(f"Invalid response type: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error in structured response: {e}")
            raise LLMGenerationError(f"Failed to get structured response: {e}") from e

    @abstractmethod
    async def stream_response(
        self,
        prompt: str,
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> AsyncIterator[str]:
        """Stream text responses."""
        ...

    def _get_model(self, model: str | None) -> str:
        """Get the model to use, falling back to default if not specified."""
        resolved_model = model or self.default_model
        self.logger.info(f"Using model: {resolved_model}")
        return resolved_model

    def _log_llm_call(
        self, operation: str, model: str, **kwargs: Any  # noqa: ANN401
    ) -> None:
        """
        Log LLM call details for debugging purposes.

        Args:
            operation: The type of operation (e.g., 'get_response', 'stream_response')
            model: The model being used
            **kwargs: Additional parameters to log
        """
        # Add relevant kwargs for debugging (excluding sensitive data)
        safe_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ["api_key", "access_key_id", "secret_access_key"]
        }

        provider_name = self.__class__.__name__.replace("LLMProvider", "")

        # Build the log message parts to avoid format string issues
        log_parts = [
            f"🤖 LLM Call → Provider: {provider_name}",
            f"Model: {model}",
            f"Operation: {operation}",
        ]

        if safe_kwargs:
            # Format parameters safely by converting to key=value pairs
            param_parts = [f"{k}={v}" for k, v in safe_kwargs.items()]
            log_parts.append(f"Parameters: {', '.join(param_parts)}")

        log_message = ", ".join(log_parts)

        # Log using structured logging only
        self.logger.info(log_message)

    def _format_structured_prompt(self, prompt: str, response_model: Type[T]) -> str:
        """
        Format a prompt to request JSON output matching the response model.

        Args:
            prompt: Original prompt
            response_model: Pydantic model for the expected response

        Returns:
            Formatted prompt requesting JSON output
        """
        schema = response_model.model_json_schema()
        return f"""{prompt}

Please respond with a valid JSON object that matches this schema:
{schema}

Respond only with the JSON object, no additional text."""

    def _validate_response(self, content: str) -> str:
        """
        Validate that the response content is not empty.

        Args:
            content: Response content to validate

        Returns:
            Validated content

        Raises:
            LLMGenerationError: If content is empty or invalid
        """
        if not content or not content.strip():
            raise LLMGenerationError("Received an empty response from LLM provider")
        return content.strip()
