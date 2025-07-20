"""LMStudio LLM provider implementation."""

from collections.abc import AsyncIterator
from typing import Any, List, Type, TypeVar

import httpx
from openai import APIError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel

from app.utils.performance import timing_decorator

from ..config import LMStudioConfig
from ..exceptions import LLMGenerationError, LLMProviderError, LLMRateLimitError
from ..utils import retry_on_failure
from .base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)


class LMStudioLLMProvider(BaseLLMProvider):
    """
    LMStudio implementation of the LLM service.

    LMStudio provides an OpenAI-compatible API with local models.
    This provider extends the OpenAI pattern to work with local LMStudio instances.
    """

    def __init__(self, config: LMStudioConfig) -> None:
        """
        Initialize the LMStudio provider.

        Args:
            config: LMStudio configuration
        """
        super().__init__(config.default_model)
        # Use OpenAI client with custom base URL for LMStudio compatibility
        self.client = AsyncOpenAI(
            api_key="not-required",  # LMStudio doesn't require API keys
            base_url=config.base_url,
            timeout=config.timeout,
        )
        self.base_url = config.base_url
        self.max_retries = config.max_retries

    async def get_available_models(self) -> List[str]:
        """
        Get list of available models from LMStudio.

        Returns:
            List of available model names

        Raises:
            LLMProviderError: If models endpoint fails
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/models")
                response.raise_for_status()

                data = response.json()
                models = data.get("data", [])
                return [model.get("id", "") for model in models if model.get("id")]

        except httpx.HTTPError as e:
            self.logger.error(f"Failed to fetch LMStudio models: {e}")
            raise LLMProviderError(f"Failed to fetch available models: {e}") from e
        except ValueError as e:
            self.logger.error(f"Invalid response format from LMStudio: {e}")
            raise LLMProviderError(f"Invalid response format: {e}") from e
        except KeyError as e:
            self.logger.error(f"Missing expected field in LMStudio response: {e}")
            raise LLMProviderError(f"Invalid response structure: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error fetching LMStudio models: {e}")
            raise LLMProviderError(f"Unexpected error fetching models: {e}") from e

    @retry_on_failure(max_retries=3)
    @timing_decorator
    async def get_response(
        self,
        prompt: str,
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> str:
        """
        Generate a simple text response from LMStudio.

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
                f"LMStudio rate limit exceeded with model {model_key}: {e}"
            )
            raise LLMRateLimitError("LMStudio API rate limit exceeded") from e
        except APIError as e:
            self.logger.error(f"LMStudio API error with model {model_key}: {e}")
            raise LLMGenerationError(f"LMStudio API error: {e}") from e

    @timing_decorator
    async def get_structured_response(
        self,
        prompt: str,
        response_model: Type[T],
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """
        Generate a structured response using LMStudio.

        Note: Some local models may not support JSON mode, so we fall back to
        the base implementation that uses prompt engineering.

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
        json_prompt = self._format_structured_prompt(prompt, response_model)
        model_key = self._get_model(model)
        self._log_llm_call("get_structured_response", model_key, **kwargs)

        try:
            # Try JSON mode first (some local models support it)
            if "response_format" not in kwargs:
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(
                model=model_key,
                messages=[{"role": "user", "content": json_prompt}],
                **kwargs,
            )
            content = response.choices[0].message.content
            validated_content = self._validate_response(content or "")

            # Parse and validate the JSON response
            return response_model.model_validate_json(validated_content)

        except (RateLimitError, APIError):
            # Re-raise API errors without modification
            raise
        except ValueError as e:
            self.logger.warning(
                f"JSON validation failed for LMStudio model {model_key}: {e}"
            )
            # Remove response_format and try again with base implementation
            kwargs.pop("response_format", None)
            return await super().get_structured_response(
                prompt, response_model, model, **kwargs
            )
        except Exception as e:
            # If JSON mode fails, fall back to base implementation
            self.logger.warning(
                f"JSON mode failed for LMStudio model {model_key}, falling back to prompt engineering: {e}"
            )
            # Remove response_format and try again with base implementation
            kwargs.pop("response_format", None)
            return await super().get_structured_response(
                prompt, response_model, model, **kwargs
            )

    @timing_decorator
    async def stream_response(  # type: ignore[override,misc]
        self,
        prompt: str,
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> AsyncIterator[str]:
        """
        Stream text responses from LMStudio.

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
            self.logger.error(f"LMStudio streaming error with model {model_key}: {e}")
            raise LLMGenerationError(f"Failed to stream response: {e}") from e
