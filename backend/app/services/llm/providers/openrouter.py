"""OpenRouter LLM provider implementation."""

from collections.abc import AsyncIterator
from typing import Any, Type, TypeVar

from openai import APIError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel

from app.utils.performance import timing_decorator

from ..config import OpenRouterConfig
from ..exceptions import LLMGenerationError, LLMRateLimitError
from ..utils import retry_on_failure
from .base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)


class OpenRouterLLMProvider(BaseLLMProvider):
    """OpenRouter implementation of the LLM service."""

    def __init__(self, config: OpenRouterConfig) -> None:
        """
        Initialize the OpenRouter provider.

        Args:
            config: OpenRouter configuration
        """
        super().__init__(config.default_model)
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
        self.max_retries = config.max_retries

    @retry_on_failure(max_retries=3)
    @timing_decorator
    async def get_response(
        self,
        prompt: str,
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> str:
        """
        Generate a simple text response from OpenRouter.

        Args:
            prompt: The input prompt
            model: Optional model override
            **kwargs: Additional OpenAI-compatible parameters

        Returns:
            Generated text response

        Raises:
            LLMGenerationError: If response generation fails
            LLMRateLimitError: If rate limit is exceeded
        """
        model_key = self._get_model(model)
        self._log_llm_call("get_response", model_key, **kwargs)

        try:
            response = await self.client.chat.completions.create(
                model=model_key,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            content = response.choices[0].message.content
            return self._validate_response(content or "")

        except RateLimitError as e:
            self.logger.error(
                f"OpenRouter rate limit exceeded with model {model_key}: {e}"
            )
            raise LLMRateLimitError("OpenRouter API rate limit exceeded") from e
        except APIError as e:
            self.logger.error(f"OpenRouter API error with model {model_key}: {e}")
            raise LLMGenerationError(f"OpenRouter API error: {e}") from e

    @timing_decorator
    async def get_structured_response(
        self,
        prompt: str,
        response_model: Type[T],
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """
        Generate a structured response using OpenRouter.

        Args:
            prompt: The input prompt
            response_model: Pydantic model for response validation
            model: Optional model override
            **kwargs: Additional OpenAI-compatible parameters

        Returns:
            Validated response instance

        Raises:
            LLMGenerationError: If response generation fails
        """
        # Use JSON mode for better structured responses
        json_prompt = self._format_structured_prompt(prompt, response_model)
        model_key = self._get_model(model)
        self._log_llm_call("get_structured_response", model_key, **kwargs)

        try:
            response = await self.client.chat.completions.create(
                model=model_key,
                messages=[{"role": "user", "content": json_prompt}],
                response_format={"type": "json_object"},
                **kwargs,
            )
            content = response.choices[0].message.content
            validated_content = self._validate_response(content or "")

            # Parse and validate the JSON response
            return response_model.model_validate_json(validated_content)

        except (RateLimitError, APIError) as e:
            self.logger.error(
                f"OpenRouter structured response error with model {model_key}: {e}"
            )
            raise LLMGenerationError(f"Failed to get structured response: {e}") from e
        except ValueError as e:
            self.logger.error(f"Structured response validation failed: {e}")
            raise LLMGenerationError(f"Invalid structured response: {e}") from e
        except Exception as e:
            self.logger.error(f"Structured response parsing failed: {e}")
            raise LLMGenerationError(f"Failed to parse structured response: {e}") from e

    @timing_decorator
    async def stream_response(  # type: ignore[override,misc]
        self, prompt: str, model: str | None = None, **kwargs: Any  # noqa: ANN401
    ) -> AsyncIterator[str]:
        """
        Stream text responses from OpenRouter.

        Args:
            prompt: The input prompt
            model: Optional model override
            **kwargs: Additional OpenAI-compatible parameters

        Yields:
            Chunks of the generated text response

        Raises:
            LLMGenerationError: If streaming fails
        """
        model_key = self._get_model(model)
        self._log_llm_call("stream_response", model_key, **kwargs)

        try:
            stream = await self.client.chat.completions.create(
                model=model_key,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                **kwargs,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except (RateLimitError, APIError) as e:
            self.logger.error(f"OpenRouter streaming error with model {model_key}: {e}")
            raise LLMGenerationError(f"Failed to stream response: {e}") from e
