"""Amazon Bedrock LLM provider implementation."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any, Type, TypeVar

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel

from app.utils.performance import timing_decorator

from ..config import BedrockConfig
from ..exceptions import LLMGenerationError, LLMProviderError
from ..utils import parse_json_response, retry_on_failure
from .base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)


class BedrockLLMProvider(BaseLLMProvider):
    """
    Amazon Bedrock implementation of the LLM service using the modern converse API.

    Provides improved async handling and better error management.
    """

    # Constants for Bedrock event types
    CONTENT_BLOCK_DELTA = "contentBlockDelta"
    MESSAGE_STOP = "messageStop"
    TOOL_USE = "toolUse"

    def __init__(self, config: BedrockConfig) -> None:
        """
        Initialize the Bedrock provider.

        Args:
            config: Bedrock configuration
        """
        super().__init__(config.model_id)

        # Build client configuration
        client_kwargs = {"region_name": config.region}
        if config.access_key_id and config.secret_access_key:
            client_kwargs["aws_access_key_id"] = config.access_key_id
            client_kwargs["aws_secret_access_key"] = config.secret_access_key

        self.client = boto3.client("bedrock-runtime", **client_kwargs)
        self.model_id = config.model_id
        self.max_retries = config.max_retries

    def _convert_prompt_to_messages(self, prompt: str) -> list:
        """
        Convert a simple prompt to the messages format required by the converse API.

        Args:
            prompt: The input prompt

        Returns:
            List of message dictionaries in converse API format
        """
        return [{"role": "user", "content": [{"text": prompt.strip()}]}]

    def _build_converse_params(
        self, prompt: str, model: str, **kwargs: Any  # noqa: ANN401
    ) -> dict[str, Any]:
        """
        Build parameters for the converse API call.

        Args:
            prompt: The input prompt
            model: The model ID to use
            **kwargs: Additional parameters

        Returns:
            Dictionary of parameters for the converse API
        """
        # Convert prompt to messages format
        messages = self._convert_prompt_to_messages(prompt)

        # Build inference config
        inference_config = {}
        if "max_tokens" in kwargs:
            inference_config["maxTokens"] = kwargs.pop("max_tokens")
        if "temperature" in kwargs:
            inference_config["temperature"] = kwargs.pop("temperature")
        if "top_p" in kwargs:
            inference_config["topP"] = kwargs.pop("top_p")
        if "stop_sequences" in kwargs:
            inference_config["stopSequences"] = kwargs.pop("stop_sequences")

        # Build request parameters
        params = {
            "modelId": model,
            "messages": messages,
            "inferenceConfig": inference_config,
        }

        # Add system message if needed (optional for most use cases)
        system_message = kwargs.pop("system", None)
        if system_message:
            params["system"] = [{"text": system_message}]

        return params

    def _extract_text_from_response(self, response: dict) -> str:
        """
        Extract text content from the converse API response.

        Args:
            response: The response from the converse API

        Returns:
            The extracted text content
        """
        try:
            output = response.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])

            # Extract text from content blocks
            text_parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])

            return "\n".join(text_parts).strip()
        except (KeyError, TypeError) as e:
            raise LLMGenerationError(f"Failed to extract text from response: {e}")

    @retry_on_failure(max_retries=3)
    @timing_decorator
    async def get_response(
        self, prompt: str, model: str | None = None, **kwargs: Any  # noqa: ANN401
    ) -> str:
        """
        Generate a simple text response from Bedrock using the converse API.

        Args:
            prompt: The input prompt
            model: Optional model override
            **kwargs: Additional Bedrock parameters

        Returns:
            Generated text response

        Raises:
            LLMGenerationError: If response generation fails
        """
        model_key = self._get_model(model)

        self._log_llm_call("get_response", model_key, **kwargs)

        # Build converse API parameters
        params = self._build_converse_params(prompt, model_key, **kwargs)

        try:
            # Use the converse API
            response = await asyncio.to_thread(self.client.converse, **params)

            # Extract text from response
            content = self._extract_text_from_response(response)

            if not content:
                raise LLMGenerationError(
                    "No content returned from Bedrock converse API"
                )

            return self._validate_response(content)

        except (BotoCoreError, ClientError) as e:
            self.logger.error(f"Bedrock API error with model {model_key}: {e}")
            raise LLMProviderError(f"Bedrock API error: {e}") from e
        except ValueError as e:
            self.logger.error(f"Invalid Bedrock response format: {e}")
            raise LLMGenerationError(f"Invalid response format: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected Bedrock error: {e}")
            raise LLMGenerationError(f"Unexpected error with Bedrock API: {e}") from e

    @timing_decorator
    async def stream_response(  # type: ignore[override,misc]
        self, prompt: str, model: str | None = None, **kwargs: Any  # noqa: ANN401
    ) -> AsyncIterator[str]:
        """
        Stream text responses from Bedrock using the converse stream API.

        Args:
            prompt: The input prompt
            model: Optional model override
            **kwargs: Additional Bedrock parameters

        Yields:
            Chunks of the generated text response

        Raises:
            LLMGenerationError: If streaming fails
        """
        model_key = self._get_model(model)
        self._log_llm_call("stream_response", model_key, **kwargs)

        # Build converse API parameters
        params = self._build_converse_params(prompt, model_key, **kwargs)

        try:
            # Use the converse stream API
            response = await asyncio.to_thread(self.client.converse_stream, **params)

            # Process the streaming response
            stream = response.get("stream", [])
            for event in stream:
                if self.CONTENT_BLOCK_DELTA in event:
                    delta = event[self.CONTENT_BLOCK_DELTA].get("delta", {})
                    if "text" in delta:
                        yield delta["text"]
                elif self.MESSAGE_STOP in event:
                    # End of stream
                    break

        except (BotoCoreError, ClientError) as e:
            self.logger.error(f"Bedrock streaming error with model {model_key}: {e}")
            raise LLMGenerationError(
                f"Failed to stream response from Bedrock: {e}"
            ) from e
        except ValueError as e:
            self.logger.error(f"Invalid Bedrock streaming response format: {e}")
            raise LLMGenerationError(f"Invalid streaming response format: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected Bedrock streaming error: {e}")
            raise LLMGenerationError(f"Unexpected streaming error: {e}") from e

    @timing_decorator
    async def get_structured_response(
        self,
        prompt: str,
        response_model: Type[T],
        model: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> T:
        """
        Generate a structured response from Bedrock.

        Args:
            prompt: The input prompt
            response_model: Pydantic model describing the expected JSON schema
            model: Optional model override
            **kwargs: Additional parameters

        Returns:
            Validated response instance

        Raises:
            LLMGenerationError: If structured response generation fails
        """
        model_key = self._get_model(model)
        self._log_llm_call("get_structured_response", model_key, **kwargs)

        # Build converse API parameters
        params = self._build_converse_params(prompt, model_key, **kwargs)

        # Add tool configuration for structured output using the model schema
        tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": "json_extractor",
                        "description": "Extracts structured data in JSON format",
                        "inputSchema": {"json": response_model.model_json_schema()},
                    }
                }
            ]
        }
        params["toolConfig"] = tool_config

        try:
            # Use the converse API with tools
            response = await asyncio.to_thread(self.client.converse, **params)

            # Extract structured data from tool use
            output = response.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])

            for item in content:
                if isinstance(item, dict) and self.TOOL_USE in item:
                    tool_use = item.get(self.TOOL_USE, {})
                    tool_input = tool_use.get("input", {})
                    if tool_input:
                        return response_model.model_validate(tool_input)

            # Fallback to regular text extraction and JSON parsing
            text_content = self._extract_text_from_response(response)
            return parse_json_response(text_content, response_model)

        except (BotoCoreError, ClientError) as e:
            self.logger.error(
                f"Bedrock structured response error with model {model_key}: {e}"
            )
            raise LLMProviderError(f"Bedrock API error: {e}") from e
        except ValueError as e:
            self.logger.error(f"Invalid Bedrock structured response: {e}")
            raise LLMGenerationError(f"Invalid structured response: {e}") from e
        except TypeError as e:
            self.logger.error(f"Type error in Bedrock structured response: {e}")
            raise LLMGenerationError(f"Invalid structured response type: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected Bedrock structured response error: {e}")
            raise LLMGenerationError(f"Unexpected error with Bedrock API: {e}") from e
